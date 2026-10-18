"""Threat-model tests (docs/THREAT-MODEL.md): T-01 output folder guard, T-02 token never in outputs, T-05 hostile strings in HTML."""

import subprocess

import pytest

from fcat import checks, cli, config, manifest, render_html, render_json
from fcat.http import Client, Response
from fcat.snapshot import Snapshot

checks.load_builtin()


# ---- T-01 ----
def _git(*a, cwd):
    subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    _git("init", "-q", cwd=tmp_path)
    (tmp_path / ".gitignore").write_text("output/\n")
    return tmp_path


def test_out_dir_outside_any_repo_is_fine(tmp_path):
    assert manifest.out_dir_problem(tmp_path / "anything") is None


def test_ignored_out_dir_in_repo_is_fine(repo):
    assert manifest.out_dir_problem(repo / "output") is None
    assert manifest.out_dir_problem(repo / "output" / "sub" / "deeper") is None


def test_unignored_out_dir_in_repo_is_refused(repo):
    msg = manifest.out_dir_problem(repo / "customer-run")
    assert msg and "not ignored" in msg


def test_cli_refuses_then_allows_with_flag(repo, capsys):
    snap = repo / "customer-run" / "snapshot"
    snap.mkdir(parents=True)
    cfgf = repo / "c.json"
    cfgf.write_text("")
    rc = cli.main(["analyze", "--config", str(cfgf), "--out", str(repo / "customer-run")])
    assert rc == 2 and "not ignored" in capsys.readouterr().err
    assert not list((repo / "customer-run").glob("report.*"))
    rc = cli.main(["analyze", "--config", str(cfgf), "--out", str(repo / "customer-run"), "--allow-unignored-out"])
    assert rc in (0, 3) and (repo / "customer-run" / "report.json").exists()


# ---- T-02 ----
SECRET = "eyJ-STUB-TOKEN-must-never-be-written-1234567890"


class StubProvider:
    def token(self):
        return SECRET

    def identity(self):
        return {"tenant_id": "t", "principal_type": "user"}


class EmptyArg:
    def send(self, method, url, headers, body):
        assert headers.get("Authorization") == f"Bearer {SECRET}"  # the token IS used on the wire...
        return Response(200, {}, {"data": [], "count": 0, "totalRecords": 0, "resultTruncated": False})


def test_token_never_reaches_any_output(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "AzCliTokenProvider", StubProvider)
    monkeypatch.setattr(cli, "Client", lambda tp: Client(tp, EmptyArg(), sleep=lambda s: None))
    cfgf = tmp_path / "c.json"
    cfgf.write_text("")
    out = tmp_path / "out"
    assert cli.main(["run", "--config", str(cfgf), "--out", str(out)]) in (0, 3)
    files = [p for p in out.rglob("*") if p.is_file()]
    assert files
    for p in files:
        assert SECRET.encode() not in p.read_bytes(), p  # ...but nowhere on disk
    cap = capsys.readouterr()
    assert SECRET not in cap.out + cap.err


# ---- T-05 ----
HOSTILE = [
    "<script>alert(1)</script>",
    '"><img src=x onerror=alert(1)>',
    "' onmouseover='alert(1)",
    "</td><td>injected",
    "javascript:alert(1)",
    "&lt;already&gt;",
]


@pytest.mark.parametrize("evil", HOSTILE)
def test_html_escapes_hostile_strings(tmp_path, evil):
    snap = Snapshot(tmp_path / "s")
    snap.save("subscriptions", {"rows": [{"id": evil, "name": evil, "quotaId": evil}]})
    snap.save("unattached_disks", {"rows": [{"id": f"/d/{evil}", "skuName": evil, "sizeGB": 1, "tags": {evil: evil}}]})
    cfg = config.Config()
    f, st = checks.run_all(cfg, snap)
    m = manifest.build(cfg, {}, [], st, [], manifest.now(), manifest.now(), manifest.scope_summary(snap))
    doc = render_json.render(tmp_path / "r.json", m, f)
    render_html.render(tmp_path / "r.html", doc)
    html = (tmp_path / "r.html").read_text()
    assert evil in html or "&" in html  # content is present, in some form
    for raw in ("<script>alert", "<img src=x", '"><img', "onmouseover='alert", "</td><td>injected"):
        assert raw not in html, raw


# ---- T-10 ----
def test_manifest_records_runtime_versions():
    r = manifest.runtime_info()
    assert r["python"].count(".") == 2 and set(r["packages"]) >= {"azure-identity", "openpyxl"}
    assert all(isinstance(v, str) and v for v in r["packages"].values())
    assert "/" not in str(r) and "\\" not in str(r)  # no paths


def test_runtime_lock_matches_declared_extras_and_has_hashes():
    import pathlib
    import re
    import tomllib

    root = pathlib.Path(__file__).resolve().parent.parent
    ext = tomllib.loads((root / "pyproject.toml").read_text())["project"]["optional-dependencies"]
    declared = {re.split(r"[<>=\[]", d)[0].lower() for k in ("azure", "excel") for d in ext[k]}
    wanted = {ln.strip().lower() for ln in (root / "requirements" / "runtime.in").read_text().splitlines() if ln.strip()}
    assert declared == wanted
    lock = (root / "requirements" / "runtime.txt").read_text()
    pinned = re.findall(r"^([a-z0-9_.-]+)==", lock, re.M)
    assert declared <= set(pinned) and lock.count("--hash=sha256:") >= len(pinned)


def test_notice_covers_every_locked_dependency_and_upstream_licence():
    import pathlib
    import re

    root = pathlib.Path(__file__).resolve().parent.parent
    notice = (root / "NOTICE.md").read_text().lower().replace("_", "-")
    lock = (root / "requirements" / "runtime.txt").read_text()
    for name in re.findall(r"^([a-z0-9_.-]+)==", lock, re.M):
        assert name.lower().replace("_", "-") in notice, f"{name} is in the lock file but not in NOTICE.md"
    assert "copyright (c) microsoft corporation" in notice and "permission is hereby granted" in notice
