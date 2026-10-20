#!/usr/bin/env python3
"""Checkpoint: test, refresh the auto block in docs/HANDOVER.md, log, scan for customer data, commit, push.
Usage: python scripts/checkpoint.py -m "what changed" [--log "one line for today's log"] [--session-url URL] [--no-push]
Exit codes: 0 ok, 3 push failed (bundle written), 4 possible customer data in staged changes (nothing committed), 5 tests failed and --require-tests.
"""

import argparse
import datetime as dt
import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import docs_check  # noqa: E402

GUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
SECRET = re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}|(?i:client_secret|accountkey|sharedaccesskey)\s*[=:]\s*\S{8,}")
SCAN_EXCLUDE = ("docs/KB/", "tests/", "NOTICE.md")
# ADR 0009: Microsoft built-in tag policy definition ids are public, not customer data. Exempt ONLY lines of the exact table shape
# `    "<guid>": "require|modify|inherit|append",` in ONE file. Everything else in that file, and every other file, is still scanned.
# tests/test_render_scripts.py pins the exact set of ids in that table, so a swapped-in id fails the tests.
PUBLIC_GUID_FILE = "src/fcat/tags.py"
PUBLIC_GUID_ROW = re.compile(r'^    "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}": "(?:require|modify|inherit|append)",$')


def sh(*a, check=False):
    return subprocess.run(a, cwd=ROOT, capture_output=True, text=True, check=check)


def line_hit(path, text):
    """True when an added line (text without the leading '+') must block the commit."""
    if path == PUBLIC_GUID_FILE and PUBLIC_GUID_ROW.match(text):
        return bool(SECRET.search(text))
    return bool(SECRET.search(text) or GUID.search(text))


def scan_staged():
    out = sh("git", "diff", "--cached", "-U0").stdout
    hits, cur = [], None
    for line in out.splitlines():
        if line.startswith("+++ b/"):
            cur = line[6:]
        elif line.startswith("+") and not line.startswith("+++") and cur and not cur.startswith(SCAN_EXCLUDE):
            if line_hit(cur, line[1:]):
                hits.append(f"{cur}: {line[1:80]}")
    return hits


def narrative_hash(text):
    body = re.sub(r"<!-- auto:start -->.*?<!-- auto:end -->", "", text, flags=re.S)
    body = re.sub(r"^Last updated:.*$", "", body, flags=re.M)
    return hashlib.sha256(body.encode()).hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-m", "--message", required=True)
    ap.add_argument("--log")
    ap.add_argument("--session-url")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--require-tests", action="store_true")
    a = ap.parse_args()
    now = dt.datetime.now(dt.UTC)
    g = sh(sys.executable, "scripts/gates.py")
    tests = "pass" if g.returncode == 0 else "FAIL"
    print(g.stdout[-1800:])
    if tests == "FAIL" and a.require_tests:
        return 5
    base = sh("git", "rev-parse", "--short", "HEAD").stdout.strip()
    changed = [ln[3:] for ln in sh("git", "status", "--porcelain").stdout.splitlines()]
    hp = ROOT / "docs/HANDOVER.md"
    text = hp.read_text()
    prev = re.search(r"narrative_hash: (\w+).*?stale_count: (\d+)", text, flags=re.S)
    nh = narrative_hash(text)
    stale = 0
    if prev and prev.group(1) == nh and any(c.startswith(("src/", "scripts/", "tests/")) for c in changed):
        stale = int(prev.group(2)) + 1
    block = (
        "<!-- auto:start -->\n"
        f"Last checkpoint (UTC): {now:%Y-%m-%d %H:%M}\nBase commit: {base}\nGates: {tests}\n"
        f"Files changed in this checkpoint: {len(changed)}\n"
        f"narrative_hash: {nh}\nstale_count: {stale}\n"
        + (
            "WARNING: code changed in several checkpoints without the narrative sections being updated. Review State/Done/Next step.\n"
            if stale >= 3
            else ""
        )
        + "<!-- auto:end -->"
    )
    text = re.sub(r"<!-- auto:start -->.*?<!-- auto:end -->", block, text, flags=re.S)
    text = re.sub(r"^Last updated:.*$", f"Last updated: {now:%Y-%m-%d %H:%M} UTC", text, flags=re.M)
    hp.write_text(text)
    if a.log:
        lp = ROOT / f"docs/log/{now:%Y-%m-%d}.md"
        lp.parent.mkdir(exist_ok=True)
        with lp.open("a") as f:
            if lp.stat().st_size == 0:
                f.write(f"# {now:%Y-%m-%d}\n")
            f.write(f"- {now:%H:%M} {a.log}\n")
    errs, warns = docs_check.check()
    for w in warns:
        print("WARN:", w)
    for e in errs:
        print("ERROR:", e)
    sh("git", "add", "-A")
    hits = scan_staged()
    if hits:
        sh("git", "reset", "-q")
        print("BLOCKED: possible customer data or secrets in staged changes (R8). Nothing committed:")
        for h in hits:
            print("  ", h)
        return 4
    if not sh("git", "diff", "--cached", "--name-only").stdout.strip():
        print("nothing to commit")
        return 0
    msg = a.message + "\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
    if a.session_url:
        msg += f"\nClaude-Session: {a.session_url}"
    c = sh("git", "-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com", "commit", "-q", "-m", msg)
    if c.returncode:
        print(c.stderr)
        return 1
    sha = sh("git", "rev-parse", "--short", "HEAD").stdout.strip()
    print(f"committed {sha}; tests: {tests}; stale_count: {stale}")
    if a.no_push:
        return 0
    # Always push to wip/auto (full state incl. handover). Push to main only when every gate passed (main must always work).
    p = sh("git", "push", "origin", "HEAD:wip/auto")
    if p.returncode == 0 and tests == "pass":
        p = sh("git", "push", "origin", "HEAD:main")
        print("pushed to wip/auto and main")
    elif p.returncode == 0:
        print("gates FAILED: pushed to wip/auto only; main unchanged. HANDOVER must say so.")
    if p.returncode:
        bp = ROOT.parent / f"fcat-backup-{now:%Y%m%d-%H%M%S}.bundle"
        sh("git", "bundle", "create", str(bp), "main")
        print(f"PUSH FAILED. Bundle written to {bp}. Tell the user; do not claim this is saved.\n{p.stderr[-300:]}")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
