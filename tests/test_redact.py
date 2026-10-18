import json
import pathlib
import shutil

from fcat import checks, cli, redact

ROOT = pathlib.Path(__file__).resolve().parent.parent
RID = "/subscriptions/11111111-aaaa-bbbb-cccc-222222222222/resourceGroups/rg-Billing-Prod/providers/Microsoft.Compute/disks/Disk-Secret-01"


def test_resource_id_keeps_shape_hides_names():
    r = redact.resource_id(RID, "salt")
    parts = r.split("/")
    assert parts[1] == "subscriptions" and parts[3] == "resourceGroups" and "Microsoft.Compute/disks" in r
    for secret in ("11111111", "Billing", "Secret"):
        assert secret.lower() not in r.lower()


def test_stable_within_salt_different_across_salts_case_insensitive():
    assert redact.resource_id(RID, "s") == redact.resource_id(RID, "s")
    assert redact.resource_id(RID, "s") != redact.resource_id(RID, "t")
    a = redact.resource_id(RID, "s")
    b = redact.resource_id(RID.replace("Disk-Secret-01", "disk-secret-01"), "s")
    assert a == b  # same name different case maps to same pseudonym


def test_nested_resource_and_short_ids():
    r = redact.resource_id("/subscriptions/abc/resourceGroups/rg/providers/Microsoft.Sql/servers/sql1/elasticPools/p1", "s")
    assert "sql1" not in r and "p1" not in r.split("elasticPools/")[1][:3] and "/servers/" in r and "/elasticPools/" in r
    assert "abc" not in redact.resource_id("/subscriptions/abc", "s")
    assert redact.resource_id("", "s") == ""


def test_findings_scrubbed_fingerprint_recomputed_sorted():
    f = checks.Finding("X-Y-01", RID, "low", "Disk Disk-Secret-01 is orphaned", {"note": "in rg-billing-prod", "n": 3})
    f.fingerprint = checks.fingerprint(f)
    g = redact.findings([f], "s")[0]
    assert "secret" not in g.message.lower() and "billing" not in json.dumps(g.details).lower()
    assert g.details["n"] == 3 and g.fingerprint == checks.fingerprint(g) and g.fingerprint != f.fingerprint
    assert f.message.startswith("Disk Disk-Secret")  # original untouched


def test_identity_tenant_pseudonymised():
    assert redact.identity({"tenant_id": "t-123", "principal_type": "user"}, "s")["tenant_id"].startswith("tenant-")
    assert redact.identity({}, "s") == {}


def test_cli_redact_on_synthetic_estate(tmp_path):
    snap = tmp_path / "out" / "snapshot"
    shutil.copytree(ROOT / "tests" / "synthetic" / "snapshot", snap)
    cfg = tmp_path / "c.toml"
    cfg.write_text("")
    assert cli.main(["analyze", "--config", str(cfg), "--out", str(tmp_path / "out"), "--redact"]) == 0
    doc = json.loads((tmp_path / "out" / "report.json").read_text())
    assert doc["manifest"]["redacted"] is True and doc["audit"]["status"] == "pass"
    for name in ("report.json", "report.html"):
        text = (tmp_path / "out" / name).read_text().lower()
        for secret in ("sub-synth", "rg-synth", "disk-001", "disk-104", "ünïcode", "pip-orphan", "nsg-orphan", "asp-empty"):
            assert secret not in text, (name, secret)
    assert all(f["resource_id"] for f in doc["findings"]) and len(doc["findings"]) == 83


def test_purge_dry_run_then_delete_keeps_foreign_files(tmp_path, capsys):
    out = tmp_path / "out"
    (out / "snapshot").mkdir(parents=True)
    (out / "snapshot" / "x.json").write_text("{}")
    (out / "report.json").write_text("{}")
    (out / "notes.txt").write_text("mine")
    assert cli.main(["purge", "--out", str(out)]) == 0
    assert (out / "report.json").exists() and "would delete" in capsys.readouterr().out
    assert cli.main(["purge", "--out", str(out), "--yes"]) == 0
    assert not (out / "report.json").exists() and not (out / "snapshot").exists()
    assert (out / "notes.txt").read_text() == "mine"
    assert cli.main(["purge", "--out", str(tmp_path / "none")]) == 0
