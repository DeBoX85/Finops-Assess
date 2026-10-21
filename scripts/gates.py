#!/usr/bin/env python3
"""Quality gates. G0 fast (lint, format, docs), G1 offline tests + coverage threshold. Reports verification debt and live-gate status.
Usage: python scripts/gates.py [--fast] [--full]    Exit 0 only if every executed gate passes. See docs/QUALITY.md.
--full adds the checks that need network or a browser (dependency audit, accessibility). When their prerequisites are missing they are reported
as "NOT RUN, because X" and never as a pass."""

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import docs_check  # noqa: E402


def run(*cmd):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)  # noqa: S603


def verification_debt():
    """Count UNVERIFIED markers in decision records, plan and principles (KB notes tracked separately)."""
    files = list((ROOT / "docs" / "decisions").glob("*.md")) + [ROOT / "docs" / "PLAN.md", ROOT / "docs" / "DEV-PRINCIPLES.md"]
    out = {}
    for f in files:
        n = len(re.findall(r"UNVERIFIED", f.read_text()))
        if n:
            out[str(f.relative_to(ROOT))] = n
    kb = sum(len(re.findall(r"UNVERIFIED|NOT SEEN", p.read_text())) for p in (ROOT / "docs" / "KB" / "notes").glob("*.md"))
    return out, kb


def main():
    fast = "--fast" in sys.argv
    results = []

    def gate(name, ok, detail=""):
        results.append((name, ok, detail))

    r = run(sys.executable, "-m", "ruff", "check", ".")
    gate("G0 lint (ruff check)", r.returncode == 0, "" if r.returncode == 0 else r.stdout[-600:])
    r = run(sys.executable, "-m", "ruff", "format", "--check", ".")
    gate("G0 format (ruff format --check)", r.returncode == 0, "" if r.returncode == 0 else r.stdout[-300:])
    r = run(sys.executable, "-m", "mypy")
    gate("G0 types (mypy)", r.returncode == 0, "" if r.returncode == 0 else r.stdout[-600:])
    errs, warns = docs_check.check()
    gate("G0 documentation check", not errs, "; ".join(errs + warns)[:400])
    if fast:
        r = run(sys.executable, "-m", "pytest", "-q", "-x")
        gate("G1 offline tests (no coverage)", r.returncode == 0, "" if r.returncode == 0 else r.stdout[-800:])
    else:
        r = run(sys.executable, "-m", "pytest", "-q", "--cov", "--cov-report=term")
        tail = r.stdout.strip().splitlines()
        cov = next((ln for ln in reversed(tail) if "Total coverage" in ln or "TOTAL" in ln), "")
        gate("G1 offline tests + coverage threshold", r.returncode == 0, cov if r.returncode == 0 else r.stdout[-800:])
    not_run = []
    if "--full" in sys.argv:
        r = run(sys.executable, "-m", "pip_audit", "--require-hashes", "-r", "requirements/runtime.txt", "--progress-spinner", "off")
        if r.returncode == 0:
            gate("G1 dependency audit (pip-audit, runtime)", True)
        elif "vulnerabilit" in (r.stdout + r.stderr).lower() and "Found" in (r.stdout + r.stderr):
            gate("G1 dependency audit (pip-audit, runtime)", False, (r.stdout + r.stderr)[-500:])
        else:
            not_run.append(
                (
                    "G1 dependency audit",
                    "pip-audit could not complete (no network or tool missing): " + (r.stderr or r.stdout)[-200:].strip(),
                )
            )
        r = run(sys.executable, "scripts/a11y_check.py")
        if r.returncode == 0:
            gate("G1 accessibility (axe-core, both dashboards)", True)
        elif r.returncode == 1:
            gate("G1 accessibility (axe-core, both dashboards)", False, r.stdout[-600:])
        else:
            not_run.append(("G1 accessibility", "axe or browser unavailable: " + (r.stderr or r.stdout)[-200:].strip()))
    debt, kb = verification_debt()
    print("\nQuality gates")
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
    for name, why in not_run:
        print(f"  [NOT RUN] {name}, because {why}")
    print("  [NOT RUN] G2 live smoke tests (need test tenant): FCAT_LIVE=1 pytest -m live")
    print(f"  [INFO] verification debt: {sum(debt.values())} UNVERIFIED in plan/decisions {debt}; {kb} UNVERIFIED/NOT SEEN in KB notes")
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
