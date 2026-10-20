import pathlib
import sys

from fcat import checks, config, manifest, render_html, render_json
from fcat.snapshot import Snapshot

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import checkpoint


def doc(tmp):
    snap = Snapshot(tmp / "s")
    snap.save("unattached_disks", {"rows": [{"id": "/d<1>", "sizeGB": 1, "skuName": "S"}]})
    snap.save("subscriptions", {"rows": [{"id": "/s", "quotaId": "EnterpriseAgreement_2014-09-01"}]})
    cfg = config.Config()
    f, st = checks.run_all(cfg, snap)
    m = manifest.build(cfg, {}, [], st, [], manifest.now(), manifest.now(), manifest.scope_summary(snap))
    return render_json.render(tmp / "r.json", m, f)


def test_all_renderers_share_the_same_counts(tmp_path):
    d = doc(tmp_path)
    render_html.render(tmp_path / "r.html", d)
    h = (tmp_path / "r.html").read_text()
    assert "Findings (1)" in h and "&lt;1&gt;" in h and "<1>" not in h  # escaped
    assert "management groups: not assessed" in h
    assert "offline-only" in h  # validation level is shown to the reader  # not collected is never shown as zero
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


# ---- ADR 0009: narrow exemption in the customer data guard ----
PUBLIC_TAG_POLICY_IDS = {
    "871b6d14-10aa-478d-b590-94f262ecfa99",
    "1e30110a-5ceb-460c-a204-c1c3969c6d62",
    "96670d01-0a4d-4649-9c89-2d3abc0a5025",
    "8ce3da23-7156-49e4-b145-24f95f9dcb46",
    "726aca4c-86e9-4b04-b0c5-073027359532",
    "4f9dc7db-30c1-420c-b61a-e1d640128d26",
    "96d9a89c-0d67-41fc-899d-2b9599f76a24",
    "d157c373-a6c4-483d-aaad-570756956268",
    "5ffd78d9-436d-4b41-a421-5baa819e3008",
    "61a4d60b-7326-440e-8051-9f94394d4dd1",
    "cd3aa116-8754-49c9-a813-ad46512ece54",
    "ea3f2387-9b95-492a-a190-fcdc54f7b070",
    "b27a0cbd-a167-4dfa-ae64-4337be671140",
    "40df99da-1232-49b1-a39a-6da8d878f469",
    "9ea02ca2-71db-412d-8b00-7c7ca9fcd32d",
    "49c88fc8-6fd1-46fd-a676-f12d1d3a4c71",
    "2a0e14a6-b0a6-4fab-991a-187a4f81c498",
}  # Microsoft Learn "Assign policy definitions for tag compliance", read 2026-10-20


def test_guard_allows_only_the_exact_table_row_shape_in_tags_py():
    row = '    "871b6d14-10aa-478d-b590-94f262ecfa99": "require",'
    assert not checkpoint.line_hit("src/fcat/tags.py", row)
    assert checkpoint.line_hit("src/fcat/checks.py", row)  # same line, other file: blocked
    assert checkpoint.line_hit("src/fcat/tags.py", row.replace('"require",', '"require",  # tenant'))  # extra text: blocked
    assert checkpoint.line_hit("src/fcat/tags.py", 'TENANT = "871b6d14-10aa-478d-b590-94f262ecfa99"')  # other shape: blocked
    assert checkpoint.line_hit("src/fcat/tags.py", '    "871b6d14-10aa-478d-b590-94f262ecfa99": "owner",')  # other value: blocked
    assert checkpoint.line_hit("docs/COST-GOVERNANCE.md", row)


def test_tag_policy_table_holds_exactly_the_pinned_public_ids():
    from fcat import tags

    assert set(tags.TAG_DEFINITIONS) == PUBLIC_TAG_POLICY_IDS
