"""Environment-independent coverage of manifest.py edge branches. Found by a clean-venv CI desk check (2026-10-21): the per-module coverage floor
failed there because 'package absent' only happened to be exercised on the developer machine."""

import importlib.metadata as md
import subprocess

from fcat import manifest


def _boom(*a, **k):
    raise OSError("git cannot run")


def test_git_commit_is_none_when_git_cannot_run(monkeypatch):
    monkeypatch.setattr(subprocess, "run", _boom)
    assert manifest.git_commit() is None


def test_out_dir_check_does_not_block_when_git_cannot_be_asked(monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, "run", _boom)
    assert manifest.out_dir_problem(tmp_path / "out") is None


def test_runtime_info_reports_absent_and_present_packages(monkeypatch):
    def fake(name):
        if name == "msal":
            return "1.2.3"
        raise md.PackageNotFoundError(name)

    monkeypatch.setattr(md, "version", fake)
    pk = manifest.runtime_info()["packages"]
    assert pk["msal"] == "1.2.3" and pk["azure-identity"] == "absent"
