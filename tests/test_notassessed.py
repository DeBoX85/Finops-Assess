from fcat import checks, config
from fcat.snapshot import Snapshot


def test_age_check_without_collection_time_is_not_assessed_not_silent(tmp_path):
    s = Snapshot(tmp_path / "s")
    s.save("snapshots", {"rows": [{"id": "/s/1", "timeCreated": "2020-01-01T00:00:00Z"}]})
    findings, status = checks.run_all(config.Config(), s)
    st = {x["id"]: x for x in status}
    assert st["ORPH-SNAP-01"]["status"] == "not_assessed" and "collection time" in st["ORPH-SNAP-01"]["reason"]
    assert not [f for f in findings if f.check_id == "ORPH-SNAP-01"]
    assert st["ORPH-SNAP-02"]["status"] == "ran"  # checks that do not need the clock still run


def test_collect_stamps_snapshot_time(tmp_path):
    from fcat import collectors

    class C:  # no collector can run, but the stamp is written first
        pass

    s = Snapshot(tmp_path / "s")
    errs = []
    collectors.collect(C(), s, config.Config(), errs)
    assert s.load("_meta")["collected_at"].endswith("Z") and errs


def test_deallocated_vm_without_timestamp_is_not_assessed_not_flagged(tmp_path):
    s = Snapshot(tmp_path / "s")
    s.save("_meta", {"collected_at": "2026-10-01T00:00:00Z"})
    s.save("vms", {"rows": [{"id": "/s/1/vm-a", "powerState": "PowerState/deallocated"}]})
    findings, status = checks.run_all(config.Config(), s)
    st = {x["id"]: x for x in status}
    assert st["IDLE-VMDEAL-01"]["status"] == "not_assessed" and "timestamp" in st["IDLE-VMDEAL-01"]["reason"]
    assert not [f for f in findings if f.check_id == "IDLE-VMDEAL-01"]


def test_deallocated_vm_age_boundary(tmp_path):
    s = Snapshot(tmp_path / "s")
    s.save("_meta", {"collected_at": "2026-10-01T00:00:00Z"})
    rows = [
        {"id": "/s/1/vm-91", "powerState": "PowerState/deallocated", "powerTime": "2026-07-02T00:00:00Z"},  # 91 days: flagged
        {"id": "/s/1/vm-90", "powerState": "PowerState/deallocated", "powerTime": "2026-07-03T00:00:00Z"},  # 90 days: not flagged (> 90)
        {"id": "/s/1/vm-run", "powerState": "PowerState/running", "powerTime": "2020-01-01T00:00:00Z"},
    ]
    s.save("vms", {"rows": rows})
    findings, _ = checks.run_all(config.Config(), s)
    assert {f.resource_id for f in findings if f.check_id == "IDLE-VMDEAL-01"} == {"/s/1/vm-91"}


def test_deallocated_vm_with_unparsable_time_skipped_when_another_is_dated(tmp_path):
    s = Snapshot(tmp_path / "s")
    s.save("_meta", {"collected_at": "2026-10-01T00:00:00Z"})
    rows = [
        {"id": "/s/1/a", "powerState": "PowerState/deallocated", "powerTime": "garbage"},
        {"id": "/s/1/b", "powerState": "PowerState/deallocated", "powerTime": "2026-01-01T00:00:00Z"},
    ]
    s.save("vms", {"rows": rows})
    findings, _ = checks.run_all(config.Config(), s)
    assert {f.resource_id for f in findings if f.check_id == "IDLE-VMDEAL-01"} == {"/s/1/b"}


def test_scope_counts_are_not_assessed_without_the_inventory(tmp_path):
    from fcat import manifest
    from fcat.snapshot import Snapshot

    sc = manifest.scope_summary(Snapshot(tmp_path / "empty"))
    assert sc["resources"] is None and sc["resource_types"] is None and sc["regions"] is None
    s = Snapshot(tmp_path / "cut")
    s.save("inventory_counts", {"rows": [{"type": "t", "location": "l", "n": 3}], "total_records": 9})
    assert manifest.scope_summary(s)["resources"] is None  # incomplete list: never a partial total
