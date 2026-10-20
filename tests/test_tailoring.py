import base64
import json
import pathlib
import shutil

import pytest

from fcat import cli, config, render_html
from fcat.config import ReportOptionsError, parse_report_options

ROOT = pathlib.Path(__file__).resolve().parent.parent
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20


def _run(tmp_path, extra_cfg="", args=()):
    out = tmp_path / "out"
    shutil.copytree(ROOT / "tests" / "synthetic" / "snapshot", out / "snapshot")
    cfg = tmp_path / "c.toml"
    cfg.write_text(extra_cfg)
    rc = cli.main(["analyze", "--config", str(cfg), "--out", str(out), *args])
    return rc, out


def test_defaults_keep_the_standard_report(tmp_path):
    rc, out = _run(tmp_path)
    assert rc == 0
    h = (out / "report.html").read_text()
    assert "<title>F-CAT assessment report</title>" in h and "Check coverage" in h and "<img" not in h
    assert json.loads((out / "report.json").read_text())["manifest"]["report_options"]["hidden_sections"] == []


def test_branding_applies_and_is_recorded_in_the_manifest(tmp_path):
    (tmp_path / "logo.png").write_bytes(PNG)
    rc, out = _run(
        tmp_path,
        '[report]\ntitle="Acme Cloud Cost Review"\nsubtitle="Q4"\nprepared_by="Contoso FinOps"\nprepared_for="Acme"\nfooter="Confidential"\naccent="#0057b8"\nlogo="logo.png"\n',
    )
    assert rc == 0
    h = (out / "report.html").read_text()
    assert "<title>Acme Cloud Cost Review</title>" in h and "Prepared for Acme" in h and "Confidential" in h and "--accent:#0057b8" in h
    assert "data:image/png;base64," + base64.b64encode(PNG).decode() in h
    ro = json.loads((out / "report.json").read_text())["manifest"]["report_options"]
    assert ro["logo_sha256"] and ro["title"] == "Acme Cloud Cost Review" and "logo.png" not in json.dumps(ro)


def test_hostile_branding_text_is_escaped(tmp_path):
    rc, out = _run(tmp_path, '[report]\ntitle="<script>alert(1)</script>"\nfooter="\\"><img src=x onerror=alert(1)>"\n')
    h = (out / "report.html").read_text()
    assert rc == 0 and "<script>alert" not in h and "<img src=x" not in h and "&lt;script&gt;" in h


@pytest.mark.parametrize(
    "bad",
    [
        {"nope": 1},
        {"accent": "red"},
        {"accent": "#12345"},
        {"accent": "#123456; background:url(x)"},
        {"title": "x" * 500},
        {"title": "line\nbreak"},
        {"title": 5},
        {"hide": ["findings"]},
        {"hide": ["audit"]},
        {"hide": "coverage"},
        {"logo": "does-not-exist.png"},
    ],
)
def test_invalid_options_are_rejected(bad, tmp_path):
    with pytest.raises(ReportOptionsError):
        parse_report_options(bad, tmp_path)


def test_logo_must_be_a_real_image_and_small(tmp_path):
    (tmp_path / "x.png").write_text("not an image")
    with pytest.raises(ReportOptionsError):
        parse_report_options({"logo": "x.png"}, tmp_path)
    (tmp_path / "big.png").write_bytes(PNG + b"0" * config.MAX_LOGO_BYTES)
    with pytest.raises(ReportOptionsError):
        parse_report_options({"logo": "big.png"}, tmp_path)
    (tmp_path / "ok.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    assert parse_report_options({"logo": "ok.svg"}, tmp_path).logo_data_uri.startswith("data:image/svg+xml;base64,")


def test_hiding_sections_keeps_findings_audit_result_and_a_coverage_statement(tmp_path):
    rc, out = _run(tmp_path, '[report]\nhide=["coverage","collector_errors","audit_detail"]\n')
    h = (out / "report.html").read_text()
    assert rc == 0 and "<th>Validation</th>" not in h and "What it verifies" not in h
    assert "Self-audit: PASS" in h and "Findings (114)" in h
    assert "checks:" in h and "ran" in h  # one-line coverage statement replaces the table
    ro = json.loads((out / "report.json").read_text())["manifest"]["report_options"]
    assert ro["hidden_sections"] == ["audit_detail", "collector_errors", "coverage"]


def test_a_failed_audit_is_never_tucked_away():
    doc = {
        "schema_version": "x",
        "manifest": {"tool_version": "t", "started": "s", "ended": "e", "checks": [], "scope": {}},
        "check_catalogue": [],
        "findings": [],
        "audit": {
            "status": "fail",
            "report_hash": "h",
            "limits": "",
            "invariants": [{"id": "INV-01", "passed": False, "description": "d", "violation_count": 2}],
        },
    }
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        render_html.render(pathlib.Path(d) / "r.html", doc, parse_report_options({"hide": ["audit_detail"]}))
        h = (pathlib.Path(d) / "r.html").read_text()
    assert "Self-audit: FAIL" in h and "INV-01" in h


def test_per_run_branding_file_replaces_main_config_report_settings(tmp_path):
    (tmp_path / "brand.toml").write_text('[report]\ntitle="Partner Review"\nprepared_by="Partner Ltd"\n')
    rc, out = _run(tmp_path, '[report]\ntitle="Own Company Report"\n', args=("--branding", str(tmp_path / "brand.toml")))
    h = (out / "report.html").read_text()
    assert rc == 0 and "Partner Review" in h and "Own Company Report" not in h


def test_branding_file_may_not_change_anything_but_the_report_table(tmp_path, capsys):
    (tmp_path / "brand.toml").write_text('[checks]\n"ORPH-DISK-01" = false\n')
    rc, _ = _run(tmp_path, args=("--branding", str(tmp_path / "brand.toml")))
    assert rc == 2 and "only a [report] table" in capsys.readouterr().err


def test_tailoring_never_changes_the_findings(tmp_path):
    _, plain = _run(tmp_path / "a" if (tmp_path / "a").mkdir() is None else tmp_path)
    _, styled = _run(tmp_path / "b" if (tmp_path / "b").mkdir() is None else tmp_path, '[report]\ntitle="X"\nhide=["coverage"]\n')
    a = json.loads((plain / "report.json").read_text())["findings"]
    b = json.loads((styled / "report.json").read_text())["findings"]
    assert a == b
