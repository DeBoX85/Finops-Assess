"""Run-to-run comparison (backlog 34). Wording and not-comparable rules are part of the contract."""

import json

import pytest

from fcat import cli, compare


def _f(cid, rid, sev="medium", details=None, logic="aaa"):
    d = details or {}
    return {
        "check_id": cid,
        "resource_id": rid,
        "severity": sev,
        "message": "m",
        "details": d,
        "fingerprint": f"{cid}|{rid}|{sorted(d.items())}|{sev}",
        "evidence": {"logic_hash": logic},
    }


def _doc(findings, checks=None, started="2026-10-01T00:00:00+00:00", redacted=False, scope=None, audit="pass"):
    ids = checks or {f["check_id"]: "ran" for f in findings}
    return {
        "manifest": {
            "started": started,
            "redacted": redacted,
            "scope": scope or {"subscriptions": 2, "management_groups": 1},
            "config": {"subscriptions_count": 2},
            "checks": [{"id": k, "status": v} for k, v in ids.items()],
        },
        "findings": findings,
        "audit": {"status": audit, "report_hash": "h" + started[:10]},
    }


def _by(res, state):
    return sorted(i["resource_id"] for i in res["items"] if i["state"] == state)


def test_new_no_longer_reported_unchanged():
    old = _doc([_f("A-B-01", "/r1"), _f("A-B-01", "/r2")])
    new = _doc([_f("A-B-01", "/r2"), _f("A-B-01", "/r3")], started="2026-10-08T00:00:00+00:00")
    res = compare.compare(old, new)
    assert _by(res, "new") == ["/r3"]
    assert _by(res, "no_longer_reported") == ["/r1"]
    assert _by(res, "unchanged") == ["/r2"]
    assert res["counts"]["new"] == 1


def test_severity_and_details_changes():
    old = _doc([_f("A-B-01", "/r1", "low"), _f("A-B-01", "/r2", "high"), _f("A-B-01", "/r3", "medium", {"sizeGB": 8})])
    new = _doc([_f("A-B-01", "/r1", "high"), _f("A-B-01", "/r2", "low"), _f("A-B-01", "/r3", "medium", {"sizeGB": 16})])
    res = compare.compare(old, new)
    assert _by(res, "worse") == ["/r1"] and _by(res, "better") == ["/r2"] and _by(res, "changed") == ["/r3"]
    changed = next(i for i in res["items"] if i["resource_id"] == "/r3")
    assert changed["changed_detail_keys"] == ["sizeGB"]


def test_check_that_did_not_run_in_both_is_not_comparable_not_fixed():
    old = _doc([_f("A-B-01", "/r1")])
    new = _doc([], checks={"A-B-01": "not_assessed"}, started="2026-10-08T00:00:00+00:00")
    res = compare.compare(old, new)
    assert res["items"] == []
    assert res["not_comparable"][0]["check_id"] == "A-B-01"
    assert res["not_comparable"][0]["reason"].startswith("not comparable, because")


def test_new_check_in_newer_run_does_not_flood_new():
    old = _doc([_f("A-B-01", "/r1")])
    new = _doc([_f("A-B-01", "/r1"), _f("C-D-01", "/x")], started="2026-10-08T00:00:00+00:00")
    res = compare.compare(old, new)
    assert _by(res, "new") == []
    assert {n["check_id"] for n in res["not_comparable"]} == {"C-D-01"}


def test_rule_change_is_flagged():
    old = _doc([_f("A-B-01", "/r1", logic="aaa")])
    new = _doc([_f("A-B-01", "/r2", logic="bbb")], started="2026-10-08T00:00:00+00:00")
    res = compare.compare(old, new)
    assert all(i["rule_changed"] for i in res["items"])
    assert any("rule text changed" in w for w in res["warnings"])


def test_redacted_reports_are_refused():
    with pytest.raises(compare.CompareError, match="redacted"):
        compare.compare(_doc([], checks={"A-B-01": "ran"}, redacted=True), _doc([]))


def test_warnings_for_scope_audit_and_same_tenant():
    old = _doc([_f("A-B-01", "/r1")], scope={"subscriptions": 2, "management_groups": 1})
    new = _doc([_f("A-B-01", "/r1")], scope={"subscriptions": 3, "management_groups": 1}, audit="fail", started="2026-10-08T00:00:00+00:00")
    w = " ".join(compare.compare(old, new)["warnings"])
    assert "different number of subscriptions" in w and "self-audit" in w and "same tenant" in w


def test_markdown_avoids_fixed_claim_and_lists_sections():
    res = compare.compare(_doc([_f("A-B-01", "/r1")]), _doc([_f("A-B-01", "/r9")], started="2026-10-08T00:00:00+00:00"))
    md = compare.markdown(res)
    assert "does not prove a fix" in md and "## New (1)" in md and "## No longer reported (1)" in md
    assert "fixed" not in md.lower().replace("does not prove a fix", "")


def test_load_rejects_non_report(tmp_path):
    p = tmp_path / "x.json"
    p.write_text("[]")
    with pytest.raises(compare.CompareError):
        compare.load(p)
    with pytest.raises(compare.CompareError):
        compare.load(tmp_path / "missing.json")


def test_cli_compare_writes_files(tmp_path, capsys):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(_doc([_f("A-B-01", "/r1")])))
    b.write_text(json.dumps(_doc([_f("A-B-01", "/r2")], started="2026-10-08T00:00:00+00:00")))
    out = tmp_path / "out"
    assert cli.main(["compare", str(a), str(b), "--out", str(out), "--allow-unignored-out"]) == 0
    assert json.loads((out / "compare.json").read_text())["counts"]["new"] == 1
    assert (out / "compare.md").exists()
    assert "new 1" in capsys.readouterr().out


def test_cli_compare_refuses_redacted(tmp_path, capsys):
    a = tmp_path / "a.json"
    a.write_text(json.dumps(_doc([], checks={"A-B-01": "ran"}, redacted=True)))
    assert cli.main(["compare", str(a), str(a), "--out", str(tmp_path / "o"), "--allow-unignored-out"]) == 2
    assert "redacted" in capsys.readouterr().err


def test_resource_count_changes_are_not_a_scope_change():
    a = {"subscriptions": 2, "management_groups": 1, "resources": 10, "resource_types": 3, "regions": 2}
    b = {**a, "resources": 15}
    older, newer = _doc([], scope=a), _doc([], scope=b)
    assert not any("different number of subscriptions" in w for w in compare.compare(older, newer)["warnings"])
    newer2 = _doc([], scope={**a, "subscriptions": 3})
    assert any("different number of subscriptions" in w for w in compare.compare(older, newer2)["warnings"])
