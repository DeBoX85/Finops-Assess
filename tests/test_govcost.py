"""Phase 2 governance collectors (src/fcat/govcost.py): privacy projection, per-subscription failures, no empty pass, config switch."""

import json

import pytest

from fcat import checks, collectors, govcost
from fcat.config import load
from fcat.http import BlockedRequest, Client, Response
from fcat.snapshot import Snapshot

checks.load_builtin()

BUDGET = {
    "id": "/subscriptions/s1/providers/Microsoft.Consumption/budgets/b1",
    "name": "b1",
    "properties": {
        "amount": 1000,
        "category": "Cost",
        "timeGrain": "Monthly",
        "timePeriod": {"startDate": "2026-01-01T00:00:00Z", "endDate": "2027-01-01T00:00:00Z"},
        "currentSpend": {"amount": 120.5, "unit": "USD"},
        "notifications": {
            "n1": {
                "enabled": True,
                "operator": "GreaterThan",
                "threshold": 80,
                "thresholdType": "Actual",
                "contactEmails": ["alice@example.com"],
                "contactRoles": [],
                "contactGroups": ["/subscriptions/s1/resourceGroups/rg/providers/microsoft.insights/actionGroups/secret-ag"],
            },
            "n2": {"enabled": False, "operator": "GreaterThan", "threshold": 100, "thresholdType": "Forecasted", "contactEmails": [""]},
        },
    },
}
EXPORT = {
    "id": "/subscriptions/s1/providers/Microsoft.CostManagement/exports/e1",
    "name": "e1",
    "properties": {
        "format": "Csv",
        "definition": {"type": "ActualCost"},
        "deliveryInfo": {
            "destination": {
                "container": "private-container",
                "resourceId": "/subscriptions/s9/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/mystore",
                "rootFolderPath": "folder",
            }
        },
        "exportDescription": "owned by bob",
        "schedule": {"recurrence": "Daily", "status": "Active"},
        "runHistory": {
            "value": [
                {"properties": {"status": "Completed", "processingEndTime": "2026-10-01T00:00:00Z"}},
                {
                    "properties": {
                        "status": "Failed",
                        "processingEndTime": "2026-10-02T00:00:00Z",
                        "error": {"code": "StorageNotFound", "message": "mystore missing"},
                    }
                },
            ]
        },
    },
}
RULE = {"id": "/subscriptions/s1/providers/Microsoft.CostManagement/scheduledActions/a", "name": "a", "kind": "InsightAlert",
        "properties": {"status": "Enabled", "viewId": "/providers/Microsoft.CostManagement/views/ms:DailyAnomalyByResourceGroup",
                       "schedule": {"frequency": "Daily"}, "notification": {"to": ["carol@example.com"], "subject": "x"}}}  # fmt: skip


def test_budget_projection_keeps_booleans_and_drops_addresses_and_groups():
    row = govcost.project_budget("s1", BUDGET)
    text = json.dumps(row)
    assert "alice" not in text and "example.com" not in text and "secret-ag" not in text
    assert [n["hasEmail"] for n in row["notifications"]] == [True, False]  # blank address does not count
    assert row["notifications"][0]["hasGroup"] is True and row["currentSpend"] == 120.5 and row["level"] == "subscription"


def test_export_projection_drops_storage_ids_and_free_text_and_picks_latest_run():
    row = govcost.project_export("s1", EXPORT)
    text = json.dumps(row)
    for secret in ("mystore", "private-container", "folder", "bob", "s9", "missing"):
        assert secret not in text
    assert row["lastRunStatus"] == "Failed" and row["lastRunErrorCode"] == "StorageNotFound" and row["scheduleStatus"] == "Active"


def test_rule_projection_drops_recipients():
    row = govcost.project_scheduled_action("s1", RULE)
    assert "carol" not in json.dumps(row) and row["hasRecipient"] is True and row["kind"] == "InsightAlert"


def test_projections_survive_junk():
    for junk in ({}, {"properties": None}, {"properties": {"notifications": 5, "timePeriod": "x", "runHistory": []}}, {"properties": []}):
        govcost.project_budget("s", junk)
        govcost.project_export("s", junk)
        govcost.project_scheduled_action("s", junk)


class Tok:
    def token(self):
        return "t"


class Fake:
    def __init__(self, handler):
        self.handler, self.sent = handler, []

    def send(self, method, url, headers, body):
        self.sent.append((method, url))
        return self.handler(url)


def _client(handler):
    f = Fake(handler)
    return Client(Tok(), f, sleep=lambda s: None), f


def _snap(tmp_path, rows):
    s = Snapshot(tmp_path / "snap")
    s.save("subscriptions", {"rows": rows})
    return s


def test_collect_reads_three_get_endpoints_per_enabled_subscription_only(tmp_path):
    def handler(url):
        body = {"value": [BUDGET] if "budgets" in url else [EXPORT] if "exports" in url else [RULE]}
        return Response(200, {}, body)

    c, f = _client(handler)
    s = _snap(
        tmp_path, [{"subscriptionId": "S1", "state": "Enabled"}, {"subscriptionId": "s2", "state": "Disabled"}, {"subscriptionId": "S1"}]
    )
    errs: list = []
    govcost.collect_governance(c, s, None, errs)
    assert errs == [] and len(f.sent) == 3 and all(m == "GET" for m, _ in f.sent)
    assert (
        all("/subscriptions/S1/" in u and "api-version=2026-06-01" in u for _, u in f.sent)
        and "$expand=runHistory" in f.sent[2][1] + f.sent[1][1] + f.sent[0][1]
    )
    assert [r["name"] for r in s.load("budgets")["rows"]] == ["b1"] and s.load("budgets")["scopes"] == [
        {"subscriptionId": "S1", "status": "ok"}
    ]


def test_failed_subscription_is_recorded_and_all_failed_writes_nothing(tmp_path):
    def handler(url):
        return Response(403 if "/subscriptions/bad/" in url else 200, {}, {"value": []})

    c, _ = _client(handler)
    s = _snap(tmp_path, [{"subscriptionId": "good"}, {"subscriptionId": "bad"}])
    errs: list = []
    govcost.collect_governance(c, s, None, errs)
    assert s.load("budgets")["scopes"] == [{"subscriptionId": "bad", "status": "HTTP 403"}, {"subscriptionId": "good", "status": "ok"}] or {
        x["subscriptionId"]: x["status"] for x in s.load("budgets")["scopes"]
    } == {"good": "ok", "bad": "HTTP 403"}
    assert len(errs) == 3 and all("HTTP 403" in e["error"] for e in errs)

    c2, _ = _client(lambda url: Response(403, {}, {}))
    s2 = Snapshot(tmp_path / "snap2")
    s2.save("subscriptions", {"rows": [{"subscriptionId": "x"}]})
    errs2: list = []
    govcost.collect_governance(c2, s2, None, errs2)
    assert not s2.has("budgets") and not s2.has("cost_exports") and len(errs2) == 3  # M-008: never an empty pass


def test_missing_subscription_inventory_is_an_error_not_an_empty_snapshot(tmp_path):
    errs: list = []
    c, f = _client(lambda url: Response(200, {}, {"value": []}))
    govcost.collect_governance(c, Snapshot(tmp_path / "none"), None, errs)
    assert len(errs) == 3 and not f.sent


def test_paging_follows_next_link(tmp_path):
    pages = {
        1: {"value": [BUDGET], "nextLink": "https://management.azure.com/next?x=1"},
        2: {"value": [{**BUDGET, "name": "b2", "id": BUDGET["id"] + "2"}]},
    }

    def handler(url):
        if "next?x=1" in url:
            return Response(200, {}, pages[2])
        if "budgets" in url:
            return Response(200, {}, pages[1])
        return Response(200, {}, {"value": []})

    c, _ = _client(handler)
    s = _snap(tmp_path, [{"subscriptionId": "s1"}])
    govcost.collect_governance(c, s, None, [])
    assert [r["name"] for r in s.load("budgets")["rows"]] == ["b1", "b2"]


def test_checks_say_not_assessed_without_the_opt_in_data(tmp_path):
    s = Snapshot(tmp_path / "empty")
    for cid in ("BUD-COVER-01", "BUD-ALERT-01", "BUD-FCST-01", "BUD-EXP-01", "ALR-ANOM-01", "EXP-CFG-01"):
        fn = next(fn for m, fn in checks.REGISTRY if m.id == cid)
        with pytest.raises(checks.NotAssessed, match="governance_apis"):
            list(fn(s))


def test_allowlist_still_blocks_writes_to_these_endpoints():
    c, _ = _client(lambda url: Response(200, {}, {}))
    with pytest.raises(BlockedRequest):
        c.request("PUT", govcost.budgets_url("s1"), {})
    with pytest.raises(BlockedRequest):
        c.request("DELETE", govcost.exports_url("s1"))


def test_config_switch_defaults_off_and_must_be_boolean(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text("[run]\n")
    assert load(p).governance_apis is False
    p.write_text("[run]\ngovernance_apis = true\n")
    assert load(p).governance_apis is True and load(p).as_dict()["governance_apis"] is True
    p.write_text('[run]\ngovernance_apis = "yes"\n')
    with pytest.raises(ValueError, match="governance_apis"):
        load(p)


def test_collect_runs_governance_only_when_enabled(monkeypatch):
    calls = []
    monkeypatch.setattr(govcost, "collect_governance", lambda *a: calls.append(a))
    monkeypatch.setattr(collectors, "COLLECTORS", {})

    class Cfg:
        subscriptions: list = []
        management_groups: list = []
        governance_apis = False
        rightsizing = False

    import pathlib
    import tempfile

    with tempfile.TemporaryDirectory() as t:
        s = Snapshot(pathlib.Path(t))
        collectors.collect(None, s, Cfg(), [])
        assert calls == []
        Cfg.governance_apis = True
        collectors.collect(None, s, Cfg(), [])
        assert len(calls) == 1
