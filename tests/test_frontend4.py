"""Round 4 mock-up generator: the comparison and maturity panels must be the real output of the tool, and the page must stay clean."""

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("v4", ROOT / "scripts" / "make_frontend_v4.py")
v4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v4)


def test_changes_and_maturity_come_from_the_tool():
    d = v4.build()
    c = d["changes"]["counts"]
    # hand-derived from _older_snapshot: two disks not yet orphaned and one new running VM are new, one disk resized is changed, one retired disk is gone
    assert (c["new"], c["changed"], c["no_longer_reported"], c["worse"], c["better"]) == (3, 1, 1, 0, 0)
    assert {n["check_id"] for n in d["changes"]["not_comparable"]} == {"ORPH-AVSET-01", "RIGHT-VMCPU-01"}
    assert d["maturity"]["counts"] == {"below": 2, "meets": 5, "above": 1, "no_target": 11, "needs_input": 3}
    assert len(d["portfolio"]) == 2 and all(r["audit"] == "pass" for r in d["portfolio"])


def test_page_has_no_em_dash_no_script_errors_markers_and_no_real_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(v4, "OUT", tmp_path)
    v4.main()
    text = "".join(p.read_text() for p in tmp_path.glob("*.html"))
    assert "—" not in text and "[object " not in text and "sub-synth" in text
    assert "Design only" in text and "No longer reported does not prove a fix" in text
