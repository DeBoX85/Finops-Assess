import json

import pytest

from fcat import arg, checks, config, manifest, render_json
from fcat.errors import FcatError, IncompleteResult
from fcat.http import BlockedRequest, Client, Response
from fcat.snapshot import Snapshot


class Tok:
    def token(self):
        return "t"


class Fake:
    def __init__(self, responses):
        self.r = list(responses)
        self.sent = []

    def send(self, method, url, headers, body):
        self.sent.append((method, url, body))
        return self.r.pop(0)


def client(*responses):
    f = Fake(responses)
    sl = []
    return Client(Tok(), f, sleep=sl.append), f, sl


def page(rows, total, skip=None, truncated=False):
    b = {"data": rows, "count": len(rows), "totalRecords": total, "resultTruncated": truncated}
    if skip:
        b["$skipToken"] = skip
    return Response(200, {}, b)


def test_paging_follows_skip_token():
    c, f, _ = client(page([{"id": "1"}], 2, "tok"), page([{"id": "2"}], 2))
    res = arg.query(c, "resources | project id | order by id asc")
    assert [r["id"] for r in res.rows] == ["1", "2"] and res.pages == 2
    assert f.sent[1][2]["options"]["$skipToken"] == "tok"


def test_truncation_without_token_is_an_error():
    c, _, _ = client(page([{"id": "1"}], 5, truncated=True))
    with pytest.raises(IncompleteResult):
        arg.query(c, "resources | project id | order by id asc | take 1")


def test_warns_when_no_order_by():
    c, _, _ = client(page([], 0))
    assert arg.query(c, "resources | project id").warnings


def test_retry_after_on_429():
    c, f, sl = client(Response(429, {"retry-after": "3"}, {}), page([], 0))
    arg.query(c, "resources | project id | order by id asc")
    assert sl == [3.0] and c.calls[0].retries == 1


def test_quota_zero_backs_off():
    ok = Response(200, {"x-ms-user-quota-remaining": "0", "x-ms-user-quota-resets-after": "00:00:03"}, {"data": [], "totalRecords": 0})
    c, _, sl = client(ok)
    arg.query(c, "resources | project id | order by id asc")
    assert sl == [3.0]


@pytest.mark.parametrize(
    "method,url",
    [
        ("PUT", "https://management.azure.com/subscriptions/x/resourceGroups/rg?api-version=1"),
        ("DELETE", "https://management.azure.com/subscriptions/x"),
        ("POST", "https://management.azure.com/subscriptions/x/providers/Microsoft.Compute/virtualMachines/v/deallocate?api-version=1"),
        ("GET", "https://evil.example.com/x"),
        ("GET", "http://management.azure.com/x"),
    ],
)
def test_read_only_allowlist_blocks(method, url):
    c, f, _ = client()
    with pytest.raises(BlockedRequest):
        c.request(method, url)
    assert f.sent == []


def test_ids_redacted_in_call_log():
    c, _, _ = client(Response(200, {}, {}))
    c.request("GET", "https://management.azure.com/subscriptions/11111111-2222-3333-4444-555555555555/resourcegroups?api-version=1")
    assert "1111" not in c.calls[0].endpoint and "{id}" in c.calls[0].endpoint


def test_pipeline_reports_not_assessed_and_findings(tmp_path):
    cfg = config.Config()
    snap = Snapshot(tmp_path / "s")
    f, st = checks.run_all(cfg, snap)
    assert st[0]["status"] == "not_assessed" and "unattached_disks" in st[0]["reason"]
    snap.save("unattached_disks", {"rows": [{"id": "/d1", "sizeGB": 128, "skuName": "Premium_LRS"}]})
    f, st = checks.run_all(cfg, snap)
    assert st[0]["status"] == "ran" and f[0].resource_id == "/d1"
    m = manifest.build(cfg, {}, [], st, [], manifest.now(), manifest.now())
    render_json.render(tmp_path / "r.json", m, f)
    assert json.loads((tmp_path / "r.json").read_text())["findings"][0]["check_id"] == "ORPH-DISK-01"


def test_toggles_skip_with_reason(tmp_path):
    cfg = config.Config(checks={"ORPH-DISK-01": False})
    _, st = checks.run_all(cfg, Snapshot(tmp_path))
    assert st[0]["status"] == "skipped"


def test_failed_check_is_reported_not_swallowed(tmp_path):
    meta = checks.CheckMeta("X-1", "d", "t", (), ())

    def boom(s):
        raise ValueError("bad")

    _, st = checks.run_all(config.Config(), Snapshot(tmp_path), [(meta, boom)])
    assert st[0]["status"] == "failed" and "bad" in st[0]["reason"]


def test_subscriptions_and_mgs_exclusive():
    c, _, _ = client()
    with pytest.raises(FcatError):
        arg.query(c, "x", ["a"], ["b"])
