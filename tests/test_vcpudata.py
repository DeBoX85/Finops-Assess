"""VM size to vCPU lookup (src/fcat/vcpudata.py), opt-in compute_apis, and its use by LIC-AHBVCP-01 and LIC-AHBWIN-01."""

from fcat import checks, collectors, config, vcpudata
from fcat.checks import NotAssessed
from fcat.http import Client, Response
from fcat.snapshot import Snapshot

checks.load_builtin()


class Tok:
    def token(self):
        return "t"

    def identity(self):
        return {}


class Fake:
    def __init__(self, *responses):
        self.responses, self.sent = list(responses), []

    def send(self, method, url, headers, body):
        self.sent.append((method, url))
        return self.responses.pop(0)


def client(*responses):
    t = Fake(*responses)
    return Client(Tok(), transport=t, sleep=lambda s: None), t


def sku(name, n):
    return {"resourceType": "virtualMachines", "name": name, "capabilities": [{"name": "vCPUs", "value": str(n)}]}


def vm(i, sub="s1", loc="westeurope", size="Standard_D2s_v5", os="Windows", lic="Windows_Server"):
    return {
        "id": i,
        "subscriptionId": sub,
        "location": loc,
        "vmSize": size,
        "osType": os,
        "licenseType": lic,
        "resType": "microsoft.compute/virtualmachines",
    }


def snap_with(tmp_path, *rows):
    s = Snapshot(tmp_path / "snap")
    s.save("vm_licensing", {"rows": list(rows)})
    return s


def test_one_call_per_subscription_and_region_and_only_used_sizes_kept(tmp_path):
    s = snap_with(
        tmp_path, vm("/a"), vm("/b", size="Standard_D4s_v5"), vm("/c", loc="northeurope"), vm("/lin", os="Linux", loc="swedencentral")
    )
    c, t = client(
        Response(200, {}, {"value": [sku("Standard_D2s_v5", 2)]}),  # northeurope sorts first
        Response(200, {}, {"value": [sku("Standard_D2s_v5", 2), sku("Standard_D4s_v5", 4), sku("Standard_D64s_v5", 64)]}),
    )
    errors = []
    vcpudata.collect_vm_vcpus(c, s, config.Config(), errors)
    assert errors == [] and len(t.sent) == 2 and all(m == "GET" for m, _ in t.sent)
    d = s.load("vm_vcpus")
    assert {(r["location"], r["size"], r["vcpus"]) for r in d["rows"]} == {
        ("northeurope", "Standard_D2s_v5", 2),
        ("westeurope", "Standard_D2s_v5", 2),
        ("westeurope", "Standard_D4s_v5", 4),
    }
    assert d["truncated"] is False and all(x["status"] == "ok" for x in d["scopes"])


def test_nothing_written_when_every_read_fails_and_error_recorded(tmp_path):
    s = snap_with(tmp_path, vm("/a"))
    c, _ = client(Response(403, {}, {"error": {"code": "AuthorizationFailed"}}))
    errors = []
    vcpudata.collect_vm_vcpus(c, s, config.Config(), errors)
    assert not s.has("vm_vcpus") and "HTTP 403" in errors[0]["error"]


def test_partial_failure_keeps_the_good_region(tmp_path):
    s = snap_with(tmp_path, vm("/a"), vm("/c", loc="northeurope"))
    c, _ = client(Response(500, {}, {}), Response(200, {}, {"value": [sku("Standard_D2s_v5", 2)]}))
    errors = []
    vcpudata.collect_vm_vcpus(c, s, config.Config(), errors)
    d = s.load("vm_vcpus")
    assert {(x["location"], x["status"]) for x in d["scopes"]} == {("northeurope", "HTTP 500"), ("westeurope", "ok")}
    assert len(d["rows"]) == 1 and len(errors) == 1


def test_missing_inventory_or_no_windows_vm_makes_no_calls(tmp_path):
    c, t = client()
    errors = []
    vcpudata.collect_vm_vcpus(c, Snapshot(tmp_path / "empty"), config.Config(), errors)
    assert errors and not t.sent
    s = snap_with(
        tmp_path, vm("/lin", os="Linux"), "junk", {"id": "/nolocation", "osType": "Windows", "subscriptionId": "s1", "vmSize": "x"}
    )
    errors2 = []
    vcpudata.collect_vm_vcpus(c, s, config.Config(), errors2)
    assert errors2 == [] and not t.sent and not s.has("vm_vcpus")


def test_switch_gates_the_collector_and_check_names_it(tmp_path):
    assert "vm_vcpus" in collectors.REST_COLLECTORS
    s = snap_with(tmp_path, vm("/a"))
    f, st = checks.run_all(config.Config(), s)
    row = next(x for x in st if x["id"] == "LIC-AHBVCP-01")
    assert row["status"] == "not_assessed" and "compute_apis" in row["reason"]


def test_check_reports_exact_boundary_and_refuses_when_nothing_known(tmp_path):
    s = snap_with(tmp_path, vm("/seven", size="S7"), vm("/eight", size="S8"), vm("/nine", size="S9"))
    t = lambda n: {"subscriptionId": "s1", "location": "westeurope", "size": f"S{n}", "vcpus": n}  # noqa: E731
    s.save("vm_vcpus", {"rows": [t(7), t(8), t(9)], "scopes": [], "truncated": False})
    fn = next(f for m, f in checks.REGISTRY if m.id == "LIC-AHBVCP-01")
    got = list(fn(s))
    assert [g.resource_id for g in got] == ["/seven"] and got[0].details["unused_core_licences_min"] == 1
    s.save("vm_vcpus", {"rows": [], "scopes": [], "truncated": False})
    try:
        list(fn(s))
        raise AssertionError("should not decide")
    except NotAssessed:
        pass


def test_payg_finding_gets_core_licence_detail_only_with_lookup(tmp_path):
    s = snap_with(tmp_path, vm("/p", size="S4", lic=None))
    fn = next(f for m, f in checks.REGISTRY if m.id == "LIC-AHBWIN-01")
    assert "vcpus" not in list(fn(s))[0].details
    s.save(
        "vm_vcpus",
        {"rows": [{"subscriptionId": "s1", "location": "westeurope", "size": "S4", "vcpus": 4}], "scopes": [], "truncated": False},
    )
    d = list(fn(s))[0].details
    assert d["vcpus"] == 4 and d["core_licences_needed"] == 8
    s.save(
        "vm_vcpus",
        {"rows": [{"subscriptionId": "s1", "location": "westeurope", "size": "S4", "vcpus": 32}], "scopes": [], "truncated": False},
    )
    assert list(fn(s))[0].details["core_licences_needed"] == 32


def test_config_validates_the_switch(tmp_path):
    import pytest

    p = tmp_path / "c.toml"
    p.write_text("[run]\ncompute_apis = true\n")
    assert config.load(p).compute_apis is True and config.Config(compute_apis=True).as_dict()["compute_apis"] is True
    p.write_text('[run]\ncompute_apis = "yes"\n')
    with pytest.raises(ValueError, match="compute_apis"):
        config.load(p)


def test_collect_calls_vcpudata_only_when_switched_on_and_records_a_crash(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(vcpudata, "collect_vm_vcpus", lambda *a, **k: seen.append(1))
    monkeypatch.setattr(collectors, "COLLECTORS", {})
    for on in (False, True):
        collectors.collect(client()[0], Snapshot(tmp_path / f"s{on}"), config.Config(compute_apis=on), [])
    assert seen == [1]

    def boom(*a, **k):
        raise RuntimeError("x")

    monkeypatch.setattr(vcpudata, "collect_vm_vcpus", boom)
    errors = []
    collectors.collect(client()[0], Snapshot(tmp_path / "crash"), config.Config(compute_apis=True), errors)
    assert errors[0]["collector"] == "compute_apis" and "RuntimeError" in errors[0]["error"]
