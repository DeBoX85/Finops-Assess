"""Layer A self-audit tests: the audit must pass on a clean report and fail on each kind of tampering (docs/AUDIT.md)."""

import copy
import random

import pytest

from fcat import audit, checks, cli, config, manifest, render_html, render_json
from fcat.snapshot import Snapshot

checks.load_builtin()


def _doc(tmp_path, rows=None, name="s"):
    snap = Snapshot(tmp_path / name)
    snap.save("subscriptions", {"rows": []})
    snap.save("unattached_disks", {"rows": rows if rows is not None else [{"id": "/d1", "sizeGB": 8, "skuName": "S"}, {"id": "/d2"}]})
    cfg = config.Config()
    f, st = checks.run_all(cfg, snap)
    m = manifest.build(cfg, {}, [], st, [], manifest.now(), manifest.now(), manifest.scope_summary(snap))
    return render_json.render(tmp_path / f"{name}.json", m, f)


def _failed(doc):
    return {i["id"] for i in audit.build(doc)["invariants"] if not i["passed"]}


def test_clean_report_passes_all_invariants(tmp_path):
    a = _doc(tmp_path)["audit"]
    assert a["status"] == "pass" and len(a["invariants"]) == 11 and all(i["passed"] for i in a["invariants"])


def test_findings_carry_evidence_and_fingerprint(tmp_path):
    f = _doc(tmp_path)["findings"][0]
    assert f["fingerprint"] and f["evidence"]["logic_hash"] and f["evidence"]["snapshot_digests"]["unattached_disks"]


@pytest.mark.parametrize(
    "mutate,expected",
    [
        (lambda d: d["findings"].append(copy.deepcopy(d["findings"][0])), {"INV-01", "INV-04"}),
        (lambda d: d["findings"][0].update(check_id="NOPE-01"), {"INV-02", "INV-03", "INV-04", "INV-06"}),
        (lambda d: d["findings"][0].update(severity="critical!"), {"INV-05"}),
        (lambda d: d["findings"][0].update(fingerprint="tampered"), {"INV-06"}),
        (lambda d: d["findings"][0].update(resource_id=""), {"INV-06", "INV-07"}),
        (lambda d: d["findings"][0].update(message="This will save 40% guaranteed"), {"INV-08"}),
        (lambda d: d["findings"][0]["details"].update(savings_month=-5), {"INV-06", "INV-09"}),
        (lambda d: d["manifest"].update(collector_errors=[{"collector": "unattached_disks", "error": "x"}]), {"INV-10"}),
        (lambda d: d["findings"][0].update(evidence={}), {"INV-11"}),
    ],
)
def test_audit_detects_tampering(tmp_path, mutate, expected):
    d = _doc(tmp_path)
    mutate(d)
    assert expected <= _failed(d)


def test_report_hash_stable_across_reruns_and_ignores_times(tmp_path):
    a, b = _doc(tmp_path, name="a"), _doc(tmp_path, name="a")
    b["manifest"]["started"] = "1999-01-01T00:00:00Z"
    assert audit.report_hash(a) == audit.report_hash(b)


def test_report_hash_changes_when_a_finding_changes(tmp_path):
    a, b = _doc(tmp_path, name="a"), _doc(tmp_path, rows=[{"id": "/d1", "sizeGB": 9}], name="b")
    assert audit.report_hash(a) != audit.report_hash(b)


def test_row_order_does_not_change_report(tmp_path):
    """Metamorphic: the same disks in any order give the same conclusions."""
    rows = [{"id": f"/d{i}", "sizeGB": i} for i in range(20)]
    base = _doc(tmp_path, rows=rows, name="a")
    shuffled = rows[:]
    random.Random(7).shuffle(shuffled)
    other = _doc(tmp_path, rows=shuffled, name="b")
    assert [f["fingerprint"] for f in base["findings"]] == [f["fingerprint"] for f in other["findings"]]


def test_excluded_disk_never_appears_whatever_the_order(tmp_path):
    rows = [{"id": "/ok"}, {"id": "/sas", "diskState": "ActiveSAS"}, {"id": "/asr", "tags": {"ASR-ReplicaDisk": "1"}}]
    for seed in range(5):
        r = rows[:]
        random.Random(seed).shuffle(r)
        ids = {f["resource_id"] for f in _doc(tmp_path, rows=r, name=f"s{seed}")["findings"]}
        assert ids == {"/ok"}


def test_html_and_excel_show_the_audit(tmp_path):
    d = _doc(tmp_path)
    render_html.render(tmp_path / "r.html", d)
    html = (tmp_path / "r.html").read_text()
    assert "Self-audit: PASS" in html and d["audit"]["report_hash"] in html
    openpyxl = pytest.importorskip("openpyxl")
    from fcat import render_xlsx

    render_xlsx.render(tmp_path / "r.xlsx", d)
    ws = openpyxl.load_workbook(tmp_path / "r.xlsx")["Audit"]
    assert ws.max_row >= 12


def test_cli_exits_3_and_warns_when_audit_fails(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(audit, "build", lambda doc: {"version": "x", "status": "fail", "report_hash": "h", "invariants": [], "limits": ""})
    out = tmp_path / "out"
    Snapshot(out / "snapshot").save("unattached_disks", {"rows": [{"id": "/d"}]})
    cfgp = tmp_path / "c.toml"
    cfgp.write_text('[run]\nprofile="standard"\n')
    assert cli.main(["analyze", "--config", str(cfgp), "--out", str(out)]) == 3
    assert "self-audit FAILED" in capsys.readouterr().err
