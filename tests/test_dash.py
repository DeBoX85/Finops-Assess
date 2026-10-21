"""Interactive dashboard, two audiences (backlog 39). The customer file must be built WITHOUT operator data and code."""

import json
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

from fcat import cli, compare, config, dash, maturity
from fcat.config import ReportOptions

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
GOLDEN = json.loads((ROOT / "tests" / "golden" / "report.json").read_text())


def _page(tmp_path, aud, doc=GOLDEN, opts=None, **kw):
    p = tmp_path / f"{aud}.html"
    dash.render(p, doc, aud, opts, **kw)
    return p.read_text(encoding="utf-8")


def _data(page):
    m = re.search(r"<script>const D=(.*?);\s*const \$=", page, re.S)
    return json.loads(m.group(1).replace("\\u003c", "<").replace("\\u003e", ">").replace("\\u0026", "&"))


def test_customer_file_has_no_operator_data_or_code(tmp_path):
    page = _page(tmp_path, "customer")
    hashes = {f["evidence"]["logic_hash"] for f in GOLDEN["findings"]}
    digests = {d for f in GOLDEN["findings"] for d in f["evidence"]["snapshot_digests"].values() if d}
    assert hashes and digests
    assert not any(h in page for h in hashes | digests)
    for word in (
        "logic_hash",
        "snapshot_digests",
        "api_calls",
        "Evidence (operator",
        "h('textarea'",
        "Operator view",
        "Collector errors",
        "apiCalls",
    ):
        assert word not in page, word
    d = _data(page)
    assert all("evidence" not in f for f in d["findings"]) and d["collectorErrors"] == [] and "apiCalls" not in d["run"]
    assert all(c["reason"] == "" for c in d["checks"])


def test_operator_file_has_the_extras(tmp_path):
    page = _page(tmp_path, "operator")
    d = _data(page)
    assert all("evidence" in f for f in d["findings"]) and d["run"]["apiCalls"] == len(GOLDEN["manifest"]["api_calls"])
    assert "Evidence (operator only)" in page and "Operator view" in page


def test_both_audiences_keep_findings_not_assessed_and_audit(tmp_path):
    a, b = _data(_page(tmp_path, "operator")), _data(_page(tmp_path, "customer"))
    assert len(a["findings"]) == len(b["findings"]) == len(GOLDEN["findings"])
    assert [f["fp"] for f in a["findings"]] == [f["fp"] for f in b["findings"]]
    na = {c["id"] for c in GOLDEN["manifest"]["checks"] if c["status"] != "ran"}
    for d in (a, b):
        assert {c["id"] for c in d["checks"] if c["status"] != "ran"} == na
        assert all(c["plain"] for c in d["checks"] if c["status"] != "ran")
        assert d["audit"]["status"] == GOLDEN["audit"]["status"] and d["run"]["fingerprint"] == GOLDEN["audit"]["report_hash"]


def test_plain_reasons_do_not_leak_collector_names_to_customers():
    r = "missing collector data: la_workspaces, app_insights"
    assert "la_workspaces" not in dash.plain_reason("not_assessed", r, "customer")
    assert "la_workspaces" in dash.plain_reason("not_assessed", r, "operator")
    assert dash.plain_reason("failed", "KeyError: x", "customer") == "The check hit an error and did not finish."


def test_hostile_strings_cannot_break_out(tmp_path):
    doc = json.loads(json.dumps(GOLDEN))
    evil = "</script><img src=x onerror=alert(1)>& "
    doc["findings"][0]["message"] = evil
    doc["findings"][0]["resource_id"] = "/subscriptions/s/resourceGroups/" + evil
    doc["findings"][0]["details"] = {"k": evil}
    for aud in dash.AUDIENCES:
        page = _page(tmp_path, aud, doc, ReportOptions(title="<b>t</b>"))
        assert page.count("</script>") == 1 and "<img" not in page and "&lt;b&gt;t&lt;/b&gt;" in page
        assert evil in _data(page)["findings"][0]["msg"]


def test_failed_audit_is_never_tucked_away_and_hide_applies_only_when_passing(tmp_path):
    o = ReportOptions(hide=("audit_detail",))
    assert _data(_page(tmp_path, "customer", opts=o))["audit"]["invariants"] == []
    bad = json.loads(json.dumps(GOLDEN))
    bad["audit"]["status"] = "fail"
    assert len(_data(_page(tmp_path, "customer", bad, o))["audit"]["invariants"]) > 0


def test_progress_sections_only_when_data_given(tmp_path):
    assert _data(_page(tmp_path, "customer"))["changes"] is None
    res = compare.compare(GOLDEN, GOLDEN)
    mat = maturity.evaluate({"answers": {"q4": "B"}, "targets": {"Budgeting": "run"}})
    d = _data(_page(tmp_path, "operator", changes=res, maturity=mat))
    assert d["changes"]["counts"]["unchanged"] == len(GOLDEN["findings"]) and d["maturity"]["counts"]["below"] == 1


def test_bad_audience_rejected(tmp_path):
    with pytest.raises(ValueError):
        dash.render(tmp_path / "x.html", GOLDEN, "everyone")


def test_no_em_dash_in_either_file(tmp_path):
    for aud in dash.AUDIENCES:
        assert "—" not in _page(tmp_path, aud)


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("aud", dash.AUDIENCES)
def test_javascript_parses(tmp_path, aud):
    from fcat.dash_assets import js_for  # noqa: PLC0415

    f = tmp_path / "x.js"
    f.write_text("const D={};" + js_for(aud))
    r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)  # noqa: S603, S607
    assert r.returncode == 0, r.stderr


def test_cli_writes_both_dashboards_with_previous_and_maturity(tmp_path):
    import make_synthetic as ms  # noqa: PLC0415

    out = tmp_path / "o"
    shutil.copytree(ms.SNAP, out / "snapshot")
    cfgp = tmp_path / "c.toml"
    cfgp.write_text('[run]\nprofile="standard"\n')
    prev = tmp_path / "prev.json"
    prev.write_text(json.dumps(GOLDEN))
    mi = tmp_path / "m.toml"
    mi.write_text('[answers]\nq4 = "B"\n[targets]\nBudgeting = "run"\n')
    rc = cli.main(
        ["analyze", "--config", str(cfgp), "--out", str(out), "--allow-unignored-out", "--previous", str(prev), "--maturity", str(mi)]
    )
    assert rc == 0
    for aud in dash.AUDIENCES:
        d = _data((out / f"dashboard-{aud}.html").read_text())
        assert d["changes"] is not None and d["maturity"]["counts"]["below"] == 1
    assert config  # imported for parity with other tests


def test_cli_redacted_run_skips_comparison_but_still_writes_dashboards(tmp_path, capsys):
    import make_synthetic as ms  # noqa: PLC0415

    out = tmp_path / "o"
    shutil.copytree(ms.SNAP, out / "snapshot")
    cfgp = tmp_path / "c.toml"
    cfgp.write_text('[run]\nprofile="standard"\n')
    prev = tmp_path / "prev.json"
    prev.write_text(json.dumps(GOLDEN))
    assert (
        cli.main(["analyze", "--config", str(cfgp), "--out", str(out), "--allow-unignored-out", "--redact", "--previous", str(prev)]) == 0
    )
    assert "comparison with the previous run skipped" in capsys.readouterr().out
    assert _data((out / "dashboard-customer.html").read_text())["changes"] is None


def test_cli_bad_previous_or_maturity_exit_2(tmp_path, capsys):
    cfgp = tmp_path / "c.toml"
    cfgp.write_text('[run]\nprofile="standard"\n')
    assert (
        cli.main(
            [
                "analyze",
                "--config",
                str(cfgp),
                "--out",
                str(tmp_path / "o"),
                "--allow-unignored-out",
                "--previous",
                str(tmp_path / "nope.json"),
            ]
        )
        == 2
    )
    assert (
        cli.main(
            [
                "analyze",
                "--config",
                str(cfgp),
                "--out",
                str(tmp_path / "o"),
                "--allow-unignored-out",
                "--maturity",
                str(tmp_path / "nope.toml"),
            ]
        )
        == 2
    )


def test_drill_down_present_in_both_audiences(tmp_path):
    """The summary has clickable severity tiles, area bars and a subscription map, and the findings page has a breadcrumb."""
    from fcat import dash_assets

    for aud in ("operator", "customer"):
        js = dash_assets.js_for(aud)
        for needle in ("function drill(", "function treemap(", "function areaBars(", "function crumbs("):
            assert needle in js


def test_tag_view_only_when_tag_checks_exist_and_mask_is_operator_only(tmp_path):
    for aud in ("operator", "customer"):
        assert "TAG-DISC-01" in _page(tmp_path, aud)
    assert "Mask tag values" in _page(tmp_path, "operator")
    assert "Mask tag values" not in _page(tmp_path, "customer")
    doc = json.loads(json.dumps(GOLDEN))
    doc["check_catalogue"] = [c for c in doc["check_catalogue"] if not c["id"].startswith("TAG-")]
    doc["findings"] = [f for f in doc["findings"] if not f["check_id"].startswith("TAG-")]
    doc["manifest"]["checks"] = [c for c in doc["manifest"]["checks"] if not c["id"].startswith("TAG-")]
    d = _data(_page(tmp_path, "customer", doc))
    assert not any(c["id"].startswith("TAG-") for c in d["checks"])


def test_tag_values_with_hostile_text_stay_inert(tmp_path):
    doc = json.loads(json.dumps(GOLDEN))
    evil = "</script><img src=x onerror=alert(1)>"
    for f in doc["findings"]:
        if f["check_id"] == "TAG-VAL-01":
            f["details"]["variants"] = [[{"value": evil, "count": 1}]]
    page = _page(tmp_path, "operator", doc)
    assert page.count("</script>") == 1 and "<img src=x" not in page


def test_changes_section_survives_reports_without_a_start_time(tmp_path):
    """Found by the accessibility gate: golden reports have no manifest 'started'; the page must still render."""
    older = json.loads(json.dumps(GOLDEN))
    older["findings"] = older["findings"][1:]
    ch = compare.compare(older, GOLDEN)
    assert ch["older"]["started"] is None
    page = _page(tmp_path, "customer", GOLDEN, changes=ch)
    d = _data(page)
    assert d["changes"]["older"]["started"] is None
    node = shutil.which("node")
    if node:
        js = re.search(r"<script>(.*)</script>", page, re.S).group(1)
        stub = (
            "const mk=()=>new Proxy(function(){},{get:(t,k)=>k==='nodeType'?1:mk(),apply:()=>mk()});"
            "globalThis.document={createElement:()=>({append(){},setAttribute(){},addEventListener(){},style:{},classList:{toggle(){},add(){}}}),"
            "createTextNode:()=>({nodeType:3}),querySelector:()=>({replaceChildren(){},focus(){},setSelectionRange(){}}),documentElement:{dataset:{}},activeElement:null};"
            "globalThis.window={scrollY:0,scrollTo(){}};globalThis.localStorage={getItem(){return null},setItem(){}};"
            "globalThis.matchMedia=()=>({matches:false});globalThis.print=()=>{};"
        )
        r = subprocess.run([node, "-e", stub + js], capture_output=True, text=True, timeout=30)  # noqa: S603
        assert r.returncode == 0, r.stderr[-400:]
