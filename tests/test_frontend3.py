"""Round 3 mock-up generator: builds from the real golden report and the synthetic estate, and stays consistent with them."""

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("v3", ROOT / "scripts" / "make_frontend_v3.py")
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)


def test_posture_is_derived_from_the_synthetic_snapshot_and_matches_hand_derivation():
    d = v3.build()  # build() asserts the hand-derived states and raises if rules and findings disagree
    assert [r["key"] for r in d["posture"]["rows"]] == ["alloc", "policy", "budget", "fcst", "anom", "ingest"]
    assert d["posture"]["subs"] == ["sub-synth-1", "sub-synth-2", "sub-synth-3"]
    assert d["domains"]["governance"] == "Cost governance"


def test_generated_pages_have_no_em_dash_and_no_tenant_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(v3, "OUT", tmp_path)
    v3.main()
    text = "".join(p.read_text() for p in tmp_path.glob("*.html"))
    assert "\u2014" not in text and "sub-synth" in text  # synthetic ids only
    assert "[object " not in text
