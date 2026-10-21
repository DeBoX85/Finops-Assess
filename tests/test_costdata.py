"""Cost data collector (src/fcat/costdata.py) and COST-UNMAP-01: shape parsing, no guessing, no empty pass, opt-in switch, retry header."""

import pytest

from fcat import checks, collectors, config, costdata
from fcat.http import BlockedRequest, Client, Response
from fcat.snapshot import Snapshot

checks.load_builtin()

COLS = [{"name": "PreTaxCost", "type": "Number"}, {"name": "ResourceId", "type": "String"}, {"name": "Currency", "type": "String"}]


def page(rows, next_link=None, cols=COLS):
    return Response(200, {}, {"properties": {"columns": cols, "rows": rows, "nextLink": next_link}})


class Tok:
    def token(self):
        return "t"

    def identity(self):
        return {}


class Fake:
    """Scripted transport: a list of responses per call, recording what was sent."""

    def __init__(self, *responses):
        self.responses, self.sent = list(responses), []

    def send(self, method, url, headers, body):
        self.sent.append((method, url, body))
        return self.responses.pop(0)


def client(*responses):
    t = Fake(*responses)
    return Client(Tok(), transport=t, sleep=lambda s: None), t


def snap_with_subs(tmp_path, *subs):
    s = Snapshot(tmp_path / "s")
    s.save("subscriptions", {"rows": [{"subscriptionId": x, "state": "Enabled"} for x in subs]})
    return s


def test_request_is_the_allowed_read_only_query():
    c, t = client(page([[1.0, "/A", "USD"]]))
    rows, truncated, err = costdata._query_sub(c, "sub1", "TheLastMonth")
    method, url, body = t.sent[0]
    assert (method, err, truncated) == ("POST", None, False)
    assert url.endswith("/subscriptions/sub1/providers/Microsoft.CostManagement/query?api-version=2026-06-01")
    assert body["type"] == "ActualCost" and body["dataset"]["grouping"] == [{"type": "Dimension", "name": "ResourceId"}]
    assert rows == [{"subscriptionId": "sub1", "resourceId": "/a", "cost": 1.0, "currency": "USD"}]  # id lower-cased


def test_follows_next_link_and_stops_at_page_limit():
    c, t = client(
        page(
            [[1.0, "/a", "USD"]],
            "https://management.azure.com/subscriptions/sub1/providers/Microsoft.CostManagement/query?api-version=2026-06-01&$skiptoken=x",
        ),
        page([[2.0, "/b", "USD"]]),
    )
    rows, truncated, err = costdata._query_sub(c, "sub1", "TheLastMonth")
    assert [r["cost"] for r in rows] == [1.0, 2.0] and not truncated and len(t.sent) == 2
    link = "https://management.azure.com/subscriptions/sub1/providers/Microsoft.CostManagement/query?api-version=2026-06-01&$skiptoken=x"
    c, t = client(*[page([[1.0, "/a", "USD"]], link)] * costdata.PAGE_LIMIT)
    _, truncated, err = costdata._query_sub(c, "sub1", "TheLastMonth")
    assert truncated and err is None


def test_next_link_to_another_host_is_refused_by_the_allowlist():
    c, _ = client(
        page([[1.0, "/a", "USD"]], "https://evil.example/subscriptions/s/providers/Microsoft.CostManagement/query?api-version=2026-06-01")
    )
    with pytest.raises(BlockedRequest):
        costdata._query_sub(c, "sub1", "TheLastMonth")


def test_unknown_columns_are_an_error_not_a_zero():
    c, _ = client(page([[1.0, "x"]], cols=[{"name": "Weird", "type": "Number"}, {"name": "Other", "type": "String"}]))
    rows, _, err = costdata._query_sub(c, "sub1", "TheLastMonth")
    assert rows == [] and "unexpected columns" in err


def test_cost_column_may_be_named_cost_and_bad_rows_are_skipped():
    cols = [{"name": "Cost", "type": "Number"}, {"name": "ResourceId", "type": "String"}]
    c, _ = client(page([[5, "/A"], ["nan", "/b"], [True, "/c"], "junk", [1]], cols=cols))
    rows, _, err = costdata._query_sub(c, "sub1", "TheLastMonth")
    assert err is None and [(r["resourceId"], r["cost"], r["currency"]) for r in rows] == [("/a", 5.0, None)]


def test_204_and_http_errors():
    c, _ = client(Response(204, {}, None))
    assert costdata._query_sub(c, "s", "TheLastMonth") == ([], False, None)
    c, _ = client(Response(403, {}, {"error": "no"}))
    assert costdata._query_sub(c, "s", "TheLastMonth")[2] == "HTTP 403"


def test_collect_writes_snapshot_and_survives_one_failing_subscription(tmp_path):
    s = snap_with_subs(tmp_path, "s1", "s2")
    c, _ = client(page([[1.0, "/a", "USD"]]), Response(403, {}, {}))
    errs: list = []
    costdata.collect_cost(c, s, config.Config(), errs)
    d = s.load("cost_by_resource")
    assert [x["status"] for x in d["scopes"]] == ["ok", "HTTP 403"] and len(d["rows"]) == 1 and errs and "s2" in errs[0]["error"]


def test_collect_all_failed_writes_nothing(tmp_path):
    s = snap_with_subs(tmp_path, "s1")
    c, _ = client(Response(500, {}, {}))
    errs: list = []
    costdata.collect_cost(c, s, config.Config(), errs)
    assert not s.has("cost_by_resource") and errs


def test_collect_without_inventory_or_enabled_subscription(tmp_path):
    errs: list = []
    costdata.collect_cost(None, Snapshot(tmp_path / "a"), config.Config(), errs)
    s = Snapshot(tmp_path / "b")
    s.save("subscriptions", {"rows": [{"subscriptionId": "x", "state": "Disabled"}]})
    costdata.collect_cost(None, s, config.Config(), errs)
    assert len(errs) == 2


def test_config_switch(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text("[run]\n")
    assert config.load(p).cost_apis is False
    p.write_text("[run]\ncost_apis = true\n")
    assert config.load(p).cost_apis is True and config.load(p).as_dict()["cost_apis"] is True
    p.write_text('[run]\ncost_apis = "yes"\n')
    with pytest.raises(ValueError, match="cost_apis"):
        config.load(p)


def test_collect_runs_cost_collectors_only_when_enabled(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(costdata, "collect_cost", lambda *a: calls.append(a))
    monkeypatch.setattr(collectors, "COLLECTORS", {})
    monkeypatch.setattr(collectors, "COST_ARG_COLLECTORS", {})

    class Cfg:
        subscriptions: list = []
        management_groups: list = []
        cost_apis = False
        governance_apis = False
        rightsizing = False

    collectors.collect(None, Snapshot(tmp_path / "a"), Cfg(), [])
    assert calls == []
    Cfg.cost_apis = True
    collectors.collect(None, Snapshot(tmp_path / "b"), Cfg(), [])
    assert len(calls) == 1


def test_resource_id_query_projects_what_the_check_reads():
    assert "project id=tolower(id)" in collectors.KQL_RESOURCE_IDS and "subscriptionId" in collectors.KQL_RESOURCE_IDS


def run_check(tmp_path, cost, ids):
    s = Snapshot(tmp_path / "s")
    if cost is not None:
        s.save("cost_by_resource", cost)
    if ids is not None:
        s.save("resource_ids", ids)
    findings, status = checks.run_all(config.Config(), s)
    return [f for f in findings if f.check_id == "COST-UNMAP-01"], {x["id"]: x for x in status}["COST-UNMAP-01"]


OK = [{"subscriptionId": "s1", "status": "ok", "truncated": False}]


def test_check_not_assessed_cases(tmp_path):
    _, st = run_check(tmp_path / "1", None, None)
    assert st["status"] == "not_assessed" and "cost_apis" in st["reason"]
    row = {"subscriptionId": "s1", "resourceId": "/a", "cost": 1.0, "currency": "USD"}
    _, st = run_check(tmp_path / "2", {"rows": [row], "scopes": OK}, {"rows": [{"id": "/a"}], "total_records": 5})
    assert st["status"] == "not_assessed" and "incomplete" in st["reason"]
    _, st = run_check(tmp_path / "3", {"rows": [row], "scopes": [{"subscriptionId": "s1", "status": "HTTP 403"}]}, {"rows": []})
    assert st["status"] == "not_assessed" and "no subscription cost query" in st["reason"]
    _, st = run_check(
        tmp_path / "4", {"rows": [row], "scopes": [{"subscriptionId": "s1", "status": "ok", "truncated": True}]}, {"rows": []}
    )
    assert st["status"] == "not_assessed"
    mixed = [row, {**row, "resourceId": "/b", "currency": "EUR"}]
    _, st = run_check(tmp_path / "5", {"rows": mixed, "scopes": OK}, {"rows": []})
    assert st["status"] == "not_assessed" and "currency" in st["reason"]


def test_check_evidence_and_ordering(tmp_path):
    rows = [
        {"subscriptionId": "s1", "resourceId": r, "cost": v, "currency": "USD"}
        for r, v in [("/a", 700.0), ("/g1", 100.0), ("/g2", 200.0), ("", 0.0)]
    ]
    f, st = run_check(tmp_path, {"rows": rows, "scopes": OK, "timeframe": "TheLastMonth"}, {"rows": [{"id": "/a"}], "total_records": 1})
    assert st["status"] == "ran" and len(f) == 1
    d = f[0].details
    assert d["missing_from_inventory_cost"] == 300.0 and d["missing_from_inventory_resources"] == 2 and d["no_resource_id_cost"] == 0.0
    assert [x["id"] for x in d["top_missing"]] == ["/g2", "/g1"] and d["subscription_cost"] == 1000.0


def test_retry_after_reads_the_cost_management_header():
    from fcat import http

    assert http._retry_after({"x-ms-ratelimit-microsoft.consumption-retry-after": "7"}) == 7.0
    assert http._retry_after({"retry-after": "3", "x-ms-ratelimit-microsoft.consumption-retry-after": "9"}) == 3.0
    assert http._retry_after({}) == 2.0


def test_resource_id_collector_saves_rows_and_records_failures(monkeypatch, tmp_path):
    from fcat import arg

    class R:
        rows = [{"id": "/a"}]
        total_records = 1
        pages = 1
        warnings: list = []

    monkeypatch.setattr(collectors, "COLLECTORS", {})
    monkeypatch.setattr(costdata, "collect_cost", lambda *a: None)

    class Cfg:
        subscriptions: list = []
        management_groups: list = []
        cost_apis = True
        governance_apis = False
        rightsizing = False

    monkeypatch.setattr(arg, "query", lambda *a, **k: R())
    s, errs = Snapshot(tmp_path / "ok"), []
    collectors.collect(None, s, Cfg(), errs)
    assert s.load("resource_ids")["rows"] == [{"id": "/a"}] and errs == []

    def boom(*a, **k):
        raise RuntimeError("no")

    monkeypatch.setattr(arg, "query", boom)
    s, errs = Snapshot(tmp_path / "bad"), []
    collectors.collect(None, s, Cfg(), errs)
    assert not s.has("resource_ids") and errs[0]["collector"] == "resource_ids"
    monkeypatch.setattr(costdata, "collect_cost", boom)
    errs = []
    collectors.collect(None, Snapshot(tmp_path / "bad2"), Cfg(), errs)
    assert any(e["collector"] == "cost_apis" for e in errs)
