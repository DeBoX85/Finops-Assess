from __future__ import annotations

import datetime as dt
import subprocess

from . import SCHEMA_VERSION, __version__


def git_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5)  # noqa: S603, S607  fixed args
        return out.stdout.strip() or None
    except Exception:  # noqa: BLE001  git is optional metadata
        return None


def out_dir_problem(out) -> str | None:
    """Threat T-01: refuse to write customer data into a git work tree where git would not ignore it.
    Returns a message, or None when the folder is outside any repo, or inside one that ignores it. git missing means no repo to protect."""
    import pathlib  # noqa: PLC0415

    p = pathlib.Path(out).resolve()
    probe = p
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    try:
        top = subprocess.run(["git", "-C", str(probe), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5)  # noqa: S603, S607  fixed args
        if top.returncode != 0:
            return None
        for name in ("report.json", "snapshot/x.json"):
            r = subprocess.run(["git", "-C", top.stdout.strip(), "check-ignore", "-q", str(p / name)], capture_output=True, timeout=5)  # noqa: S603, S607  fixed args
            if r.returncode != 0:
                return f"output folder {p} is inside git work tree {top.stdout.strip()} and is not ignored; customer data could be committed (hard rule 2)"
    except Exception:  # noqa: BLE001  if git cannot be asked, do not block the run
        return None
    return None


def scope_summary(snapshot):
    """Counts only (no names or IDs) so the manifest stays safe to show; details stay in the snapshot."""
    out = {}
    for k in ("subscriptions", "management_groups"):
        d = snapshot.load(k)
        out[k] = len(d["rows"]) if d else None  # None = not collected / not assessed
    inv = snapshot.load("inventory_counts")
    rows = [
        r for r in (inv or {}).get("rows", []) if isinstance(r, dict) and isinstance(r.get("n"), int) and not isinstance(r.get("n"), bool)
    ]
    ok = inv is not None and not (isinstance(inv.get("total_records"), int) and inv["total_records"] > len(inv.get("rows") or []))
    out["resources"] = sum(r["n"] for r in rows) if ok else None
    out["resource_types"] = len({r.get("type") for r in rows if r.get("type")}) if ok else None
    out["regions"] = len({r.get("location") for r in rows if r.get("location")}) if ok else None
    return out


def runtime_info() -> dict:
    """Interpreter and installed versions of the optional runtime dependencies (a minimal bill of materials, threat T-10).
    Versions only; no paths, no user names. 'absent' means not installed."""
    import importlib.metadata as md  # noqa: PLC0415
    import platform  # noqa: PLC0415

    pk = {}
    for n in ("azure-identity", "azure-core", "msal", "openpyxl"):
        try:
            pk[n] = md.version(n)
        except md.PackageNotFoundError:
            pk[n] = "absent"
    return {"python": platform.python_version(), "packages": pk}


def build(config, identity, calls, check_status, collector_errors, started, ended, scope=None):
    return {
        "schema_version": SCHEMA_VERSION,
        "tool_version": __version__,
        "git_commit": git_commit(),
        "runtime": runtime_info(),
        "started": started.isoformat(),
        "ended": ended.isoformat(),
        "config": config.as_dict(),
        "identity": identity,
        "scope": scope or {},
        "checks": check_status,
        "collector_errors": collector_errors,
        "api_calls": [c.__dict__ for c in calls],
    }


def now():
    return dt.datetime.now(dt.UTC)
