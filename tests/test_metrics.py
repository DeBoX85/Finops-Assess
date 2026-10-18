import datetime as dt

import pytest

from fcat import collectors, metrics
from fcat.config import load
from fcat.snapshot import Snapshot

REF = dt.datetime(2026, 10, 18, 13, 37, 5, tzinfo=dt.UTC)


def test_window_is_floored_to_hour_and_30_days():
    s, e = metrics.window(REF)
    assert e == dt.datetime(2026, 10, 18, 13, tzinfo=dt.UTC) and (e - s).days == 30


def test_metrics_url_is_get_on_arm_with_expected_params():
    s, e = metrics.window(REF)
    u = metrics.metrics_url("/subscriptions/s/resourceGroups/r/providers/Microsoft.Compute/virtualMachines/v", s, e)
    assert u.startswith("https://management.azure.com/subscriptions/s/")
    for part in (
        "interval=PT1H",
        "aggregation=Average%2CMaximum",
        "metricnames=Percentage%20CPU",
        "api-version=2018-01-01",
        "timespan=2026-09-18T13%3A00%3A00Z",
    ):
        assert part in u


def _body(data, code="Success"):
    return {"value": [{"name": {"value": "Percentage CPU"}, "errorCode": code, "timeseries": [{"data": data}]}]}


def test_parse_cpu_drops_incomplete_points_and_never_zero_fills():
    s, _ = metrics.window(REF)
    d = [
        {"timeStamp": "2026-09-18T13:00:00Z", "average": 5, "maximum": 20},
        {"timeStamp": "2026-09-18T14:00:00Z", "average": 5},
        {"timeStamp": "bad", "average": 1, "maximum": 2},
        {"timeStamp": "2026-09-18T15:00:00Z", "average": True, "maximum": 2},
        {"timeStamp": "2026-09-18T16:00:00Z", "average": 1.5, "maximum": 9.5},
        "junk",
    ]
    pts, err = metrics.parse_cpu_response(_body(d), s)
    assert err is None and [(p.hour_index, p.cpu_max) for p in pts] == [(0, 20.0), (3, 9.5)]


@pytest.mark.parametrize(
    "body",
    [
        None,
        [],
        {},
        {"value": "x"},
        {"value": [{"name": {"value": "Other"}}]},
        _body([], code="BadRequest"),
        {"value": [{"name": {"value": "Percentage CPU"}, "timeseries": []}]},
    ],
)
def test_parse_cpu_errors_are_reported_not_raised(body):
    pts, err = metrics.parse_cpu_response(body, dt.datetime(2026, 9, 18, tzinfo=dt.UTC))
    assert pts == [] and err


def test_parse_skus_and_smaller_size():
    pages = [
        {
            "value": [
                {"resourceType": "virtualMachines", "name": n, "capabilities": [{"name": "vCPUs", "value": str(v)}]}
                for n, v in [
                    ("Standard_D4s_v5", 4),
                    ("Standard_D2s_v5", 2),
                    ("Standard_D8s_v5", 8),
                    ("Standard_B4ms", 4),
                    ("Standard_B2ms", 2),
                    ("Standard_E4s_v5", 4),
                ]
            ]
            + [
                {"resourceType": "disks", "name": "Premium_LRS"},
                {"resourceType": "virtualMachines", "name": "Standard_X", "capabilities": [{"name": "vCPUs", "value": "n/a"}]},
            ]
        }
    ]
    t = metrics.parse_skus(pages)
    assert t["Standard_D4s_v5"] == 4 and "Premium_LRS" not in t and "Standard_X" not in t
    assert metrics.smaller_size("Standard_D4s_v5", t) == "Standard_D2s_v5"
    assert metrics.smaller_size("Standard_D2s_v5", t) is None  # no 1 vCPU D2s_v5
    assert metrics.smaller_size("Standard_B4ms", t) is None  # burstable deliberately skipped
    assert metrics.smaller_size("Standard_E4s_v5", t) is None  # no E2s_v5 in the list
    assert metrics.smaller_size("nonsense", t) is None


class FakeResp:
    def __init__(self, status, body):
        self.status, self.body = status, body


class FakeClient:
    def __init__(self, skus, cpu, fail_metrics=()):
        self.skus, self.cpu, self.fail, self.calls = skus, cpu, set(fail_metrics), []

    def request(self, method, url, **kw):
        self.calls.append((method, url))
        assert method == "GET"
        if "/skus" in url:
            return FakeResp(200, self.skus)
        vid = url.split("https://management.azure.com")[1].split("/providers/Microsoft.Insights")[0]
        return FakeResp(500, {}) if vid in self.fail else FakeResp(200, self.cpu)


def _vm(i, size="Standard_D4s_v5", power="PowerState/running"):
    return {
        "id": f"/subscriptions/s1/resourceGroups/r/providers/Microsoft.Compute/virtualMachines/{i}",
        "subscriptionId": "s1",
        "location": "westeurope",
        "vmSize": size,
        "powerState": power,
    }


def test_collect_rightsizing_end_to_end_with_cap_skips_and_get_only(tmp_path):
    snap = Snapshot(tmp_path)
    snap.save("vms", {"rows": [_vm("a"), _vm("b"), _vm("c", power="PowerState/deallocated"), _vm("d", size="Standard_Z9"), _vm("e")]})
    skus = {
        "value": [
            {"resourceType": "virtualMachines", "name": n, "capabilities": [{"name": "vCPUs", "value": str(v)}]}
            for n, v in [("Standard_D4s_v5", 4), ("Standard_D2s_v5", 2)]
        ]
    }
    s, _ = metrics.window(REF)
    data = [{"timeStamp": (s + dt.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ"), "average": 3, "maximum": 20} for h in range(720)]
    client = FakeClient(
        skus, _body(data), fail_metrics=["/subscriptions/s1/resourceGroups/r/providers/Microsoft.Compute/virtualMachines/b"]
    )

    class Cfg:
        rightsizing_max_vms = 3

    errors = []
    metrics.collect_rightsizing(client, snap, Cfg, errors, REF)
    out = snap.load("vm_cpu")
    assert out["running_total"] == 4 and out["considered"] == 3 and out["cap"] == 3  # a, b, d (id order); e is beyond the cap
    assert [r["id"].rsplit("/", 1)[-1] for r in out["rows"]] == ["a"]
    reasons = {x["id"].rsplit("/", 1)[-1]: x["reason"] for x in out["skipped"]}
    assert "HTTP 500" in reasons["b"] and "unknown" in reasons["d"]
    assert len([c for c in client.calls if "/skus" in c[1]]) == 1  # SKU list fetched once per subscription and location
    a = metrics.assess_row(out["rows"][0], out["window"]["hours"])
    assert a["verdict"] == "candidate" and a["confidence"] == "medium"
    assert errors == []


def test_points_outside_window_are_ignored():
    s, _ = metrics.window(REF)
    d = [
        {"timeStamp": (s - dt.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"), "average": 1, "maximum": 2},
        {"timeStamp": (s + dt.timedelta(hours=720)).strftime("%Y-%m-%dT%H:%M:%SZ"), "average": 1, "maximum": 2},
        {"timeStamp": (s + dt.timedelta(hours=719)).strftime("%Y-%m-%dT%H:%M:%SZ"), "average": 1, "maximum": 2},
    ]
    pts, _err = metrics.parse_cpu_response(_body(d), s)
    assert [p.hour_index for p in pts] == [719]


def test_missing_vm_inventory_is_an_error_not_an_empty_result(tmp_path):
    snap = Snapshot(tmp_path)
    errors = []
    metrics.collect_rightsizing(None, snap, type("C", (), {"rightsizing_max_vms": 5}), errors, REF)
    assert not snap.has("vm_cpu") and "vms" in errors[0]["error"]


def test_sku_failure_is_recorded_and_vms_skipped(tmp_path):
    snap = Snapshot(tmp_path)
    snap.save("vms", {"rows": [_vm("a")]})

    class C:
        def request(self, m, u, **k):
            return FakeResp(403, {})

    class Cfg:
        rightsizing_max_vms = 5

    errors = []
    metrics.collect_rightsizing(C(), snap, Cfg, errors, REF)
    assert errors and "403" in errors[0]["error"] and snap.load("vm_cpu")["rows"] == []


def test_config_flag_defaults_off_and_validates(tmp_path):
    assert collectors.REST_COLLECTORS == ("vm_cpu",)
    p = tmp_path / "c.toml"
    p.write_text("[run]\nrightsizing = true\nrightsizing_max_vms = 10\n")
    c = load(str(p))
    assert c.rightsizing is True and c.rightsizing_max_vms == 10
    for bad in ("rightsizing = 1", "rightsizing_max_vms = 0", "rightsizing_max_vms = true", "rightsizing_max_vms = 501"):
        p.write_text(f"[run]\n{bad}\n")
        with pytest.raises(ValueError):
            load(str(p))
    p.write_text("[run]\n")
    assert load(str(p)).rightsizing is False


def test_collect_wires_rightsizing_only_when_enabled(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(collectors, "COLLECTORS", {})
    monkeypatch.setattr(metrics, "collect_rightsizing", lambda *a, **k: called.append(1))

    class Cfg:
        subscriptions, management_groups, rightsizing = [], [], False

    collectors.collect(None, Snapshot(tmp_path / "a"), Cfg, [])
    Cfg.rightsizing = True
    collectors.collect(None, Snapshot(tmp_path / "b"), Cfg, [])
    assert called == [1]


def test_rightsizing_check_reports_not_assessed_only_when_nothing_was_assessable(tmp_path):
    import pytest as _pt

    from fcat import checks

    checks.load_builtin()
    fn = next(f for m, f in checks.REGISTRY if m.id == "RIGHT-VMCPU-01")
    win = {"hours": 720}
    s = Snapshot(tmp_path / "a")
    s.save("vm_cpu", {"rows": [], "skipped": [{"id": "/v/1", "reason": "x"}], "window": win})
    with _pt.raises(checks.NotAssessed):
        list(fn(s))
    s = Snapshot(tmp_path / "b")
    s.save("vm_cpu", {"rows": [], "skipped": [], "window": win})  # no running VMs: a true empty result
    assert list(fn(s)) == []
    row = {"id": "/v/2", "vmSize": "a", "targetSize": "b", "vcpus": 4, "targetVcpus": 2, "points": [[h, 10.0, 2.0] for h in range(720)]}
    s = Snapshot(tmp_path / "c")
    s.save("vm_cpu", {"rows": [row], "skipped": [{"id": "/v/1", "reason": "x"}], "window": win})
    assert [f.resource_id for f in fn(s)] == ["/v/2"]  # partial coverage still reports what it could assess
