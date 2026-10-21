"""The live-readiness generator lists every registered check and every marker line (offline, no Azure)."""

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _mod():
    spec = importlib.util.spec_from_file_location("live_readiness", ROOT / "scripts" / "live_readiness.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_sheet_lists_every_check(tmp_path):
    from fcat import checks

    m = _mod()
    assert m.main(["--out-dir", str(tmp_path)]) == 0
    text = (tmp_path / "LIVE-TEST-SHEET.md").read_text()
    checks.load_builtin()
    for meta, _fn in checks.REGISTRY:
        assert f"| {meta.id} |" in text


def test_register_counts_marker_lines(tmp_path):
    m = _mod()
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("fine\nthis is UNVERIFIED here\nDON'T KNOW the other\n")
    (docs / "b.md").write_text("nothing\n")
    text, n = m.register(tmp_path)
    assert n == 2 and "docs/a.md (2)" in text and "b.md" not in text


def test_register_skips_its_own_output(tmp_path):
    m = _mod()
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "UNVERIFIED-REGISTER.md").write_text("UNVERIFIED\n")
    _text, n = m.register(tmp_path)
    assert n == 0
