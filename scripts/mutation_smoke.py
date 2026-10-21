#!/usr/bin/env python3
"""Mutation smoke test: apply deliberate bugs to a COPY of the code and confirm the tests fail.
A mutation that survives means a test gap. Not a replacement for real mutation testing. mutmut 3.8.0 was tried on 2026-10-21 and does not fit (src layout, tests that read source text); see docs/KB/notes/16."""

import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
MUTATIONS = [
    ("src/fcat/http.py", "if r.status in (429, 503):", "if r.status in (503,):", "no retry on 429"),
    ("src/fcat/http.py", 'if method == "GET":\n            return', 'if method in ("GET", "PUT"):\n            return', "PUT allowed"),
    ("src/fcat/http.py", 'u.scheme != "https"', "False", "plain http allowed"),
    (
        "src/fcat/http.py",
        'or u.netloc.lower() not in ALLOWED_HOSTS | {f"{h}:443" for h in ALLOWED_HOSTS}',
        "or False",
        "user info and odd ports allowed",
    ),
    ("src/fcat/http.py", "or ord(ch) < 33 or ord(ch) == 127", "or False", "control characters and spaces allowed in URLs"),
    ("src/fcat/http.py", "if wait is None or retries >= self.max_retries:", "if wait is None:", "retry without a limit"),
    (
        "src/fcat/compare.py",
        "if cid not in both_ran:\n            continue",
        "if False:\n            continue",
        "checks that did not run in both runs are compared",
    ),
    ("src/fcat/compare.py", 'a["fingerprint"] == b["fingerprint"] and', "True and", "changed details reported as unchanged"),
    (
        "src/fcat/maturity.py",
        "current = min(levels, key=LEVELS.index)",
        "current = max(levels, key=LEVELS.index)",
        "maturity takes the highest answer",
    ),
    (
        "src/fcat/dash.py",
        '        if op:\n            item["evidence"]',
        '        if True:\n            item["evidence"]',
        "customer file carries evidence",
    ),
    ("src/fcat/dash.py", 'or au.get("status") != "pass"  #', "or False  #", "a failed audit can be hidden"),
    ("src/fcat/dash_assets.py", 'return _OPSEG.sub("null", JS)', "return JS", "customer file carries operator code"),
    ("src/fcat/dash.py", '.replace("<", "\\\\u003c")', "", "script data not escaped"),
    ("src/fcat/arg.py", "raise IncompleteResult(", "print(", "truncation ignored"),
    ("src/fcat/arg.py", 'body["options"]["$skipToken"] = skip', "pass", "skip token not sent"),
    ("src/fcat/checks.py", '"not_assessed"', '"ran"', "missing data reported as ran"),
    ("src/fcat/checks.py", "if missing:", "if False:", "missing collectors ignored"),
    ("src/fcat/config.py", "if self.checks.get(meta.id) is False:", "if False:", "check toggle ignored"),
    (
        "src/fcat/manifest.py",
        'out[k] = len(d["rows"]) if d else None',
        'out[k] = len(d["rows"]) if d else 0',
        "not collected shown as zero",
    ),
    ("src/fcat/collectors.py", "| order by id asc", "", "order by removed from queries"),
]


def main():
    survived = []
    for rel, old, new, label in MUTATIONS:
        with tempfile.TemporaryDirectory() as td:
            t = pathlib.Path(td)
            for d in ("src", "tests", "docs", "scripts"):
                shutil.copytree(ROOT / d, t / d, ignore=shutil.ignore_patterns("__pycache__", "KB"))
            shutil.copy(ROOT / "pyproject.toml", t)
            f = t / rel
            s = f.read_text()
            if old not in s:
                print(f"SKIP   {label} (pattern not found)")
                continue
            f.write_text(s.replace(old, new))
            r = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-x", "--no-cov", "-p", "no:cacheprovider"], cwd=t, capture_output=True, text=True
            )  # noqa: S603
            killed = r.returncode != 0
            print(f"{'KILLED' if killed else 'SURVIVED'} {label}")
            if not killed:
                survived.append(label)
    print(f"\n{len(survived)} survived: {survived}")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
