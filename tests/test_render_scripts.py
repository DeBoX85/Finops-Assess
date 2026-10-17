import json, pathlib, sys
from fcat import checks, config, manifest, render_json, render_html
from fcat.snapshot import Snapshot
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import checkpoint

def doc(tmp):
    snap = Snapshot(tmp / "s")
    snap.save("unattached_disks", {"rows": [{"id": "/d<1>", "sizeGB": 1, "skuName": "S"}]})
    snap.save("subscriptions", {"rows": [{"id": "/s"}]})
    cfg = config.Config()
    f, st = checks.run_all(cfg, snap)
    m = manifest.build(cfg, {}, [], st, [], manifest.now(), manifest.now(), manifest.scope_summary(snap))
    return render_json.render(tmp / "r.json", m, f)

def test_all_renderers_share_the_same_counts(tmp_path):
    d = doc(tmp_path)
    render_html.render(tmp_path / "r.html", d)
    h = (tmp_path / "r.html").read_text()
    assert "Findings (1)" in h and "&lt;1&gt;" in h and "<1>" not in h   # escaped
    assert "management groups: not assessed" in h                      # not collected is never shown as zero
    import openpyxl
    from fcat import render_xlsx
    render_xlsx.render(tmp_path / "r.xlsx", d)
    wb = openpyxl.load_workbook(tmp_path / "r.xlsx")
    assert wb["Findings"].max_row - 1 == len(d["findings"]) == 1

def test_secret_and_guid_scan_patterns():
    assert checkpoint.GUID.search("sub 11111111-2222-3333-4444-555555555555")
    assert checkpoint.SECRET.search("client_secret = abcdefghijk")
    assert checkpoint.SECRET.search("Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0aWQiOiJ4eHh4eHh4eHh4eHh4In0")
    assert not checkpoint.GUID.search("no ids here")

def test_narrative_hash_ignores_auto_block_and_timestamp():
    a = "Last updated: 1\n<!-- auto:start -->x<!-- auto:end -->\n## State\nfoo"
    b = "Last updated: 2\n<!-- auto:start -->y<!-- auto:end -->\n## State\nfoo"
    assert checkpoint.narrative_hash(a) == checkpoint.narrative_hash(b)
    assert checkpoint.narrative_hash(a) != checkpoint.narrative_hash(a + "bar")
