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
