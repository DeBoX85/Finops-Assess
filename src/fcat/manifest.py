from __future__ import annotations
import datetime as dt, subprocess
from . import __version__, SCHEMA_VERSION

def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip() or None
    except Exception:
        return None

def build(config, identity, calls, check_status, collector_errors, started, ended):
    return {
        "schema_version": SCHEMA_VERSION, "tool_version": __version__, "git_commit": git_commit(),
        "started": started.isoformat(), "ended": ended.isoformat(),
        "config": config.as_dict(), "identity": identity,
        "checks": check_status, "collector_errors": collector_errors,
        "api_calls": [c.__dict__ for c in calls],
    }

def now():
    return dt.datetime.now(dt.timezone.utc)
