"""Maturity screening with a target level per capability (backlog 36, owner agreed 2026-10-21; design in docs/maturity/README.md).

Input is a TOML file the owner prepares from the customer's answers:
    [answers]   q1 = "B" ... q13 = "D"     (A Crawl, B Walk, C Run, D Not sure)
    [targets]   "Budgeting" = "walk"       (optional; only capabilities the owner wants a target for)
Current level of a capability = the LOWEST level among the answered questions that map to it (cautious), "needs input" when none is answered.
This is a screening level (docs/maturity/README.md, known weakness: one answer cannot separate Budgeting from Forecasting).
Technical evidence from the Azure scan is NOT folded in yet; a capability's level here comes from answers only, and the output says so.
Target levels are the owner's input: finops.org says the goal is not Run everywhere, and no default target is invented.
"""

from __future__ import annotations

import pathlib
import tomllib

from .errors import FcatError

LEVELS = ("crawl", "walk", "run")
ANSWER = {"A": "crawl", "B": "walk", "C": "run"}
QUESTIONS = 13

# Question to capability map, copied from docs/maturity/README.md (kept in step by tests/test_maturity.py).
QMAP = {
    1: ("Practice Operations", "Executive Strategy Alignment"),
    2: ("Executive Strategy Alignment", "KPIs and Benchmarking"),
    3: ("Planning and Estimating", "Architecting and Workload Placement"),
    4: ("Forecasting", "Budgeting"),
    5: ("Allocation", "Invoicing and Chargeback"),
    6: ("Anomaly Management",),
    7: ("Unit Economics", "KPIs and Benchmarking"),
    8: ("Usage Optimization", "Sustainability"),
    9: ("Rate Optimization", "Licensing and SaaS"),
    10: ("Governance, Policy and Risk",),
    11: ("FinOps Education and Enablement",),
    12: ("Intersecting Disciplines", "Sustainability"),
    13: ("Reporting and Analytics", "Data Ingestion", "Automation Tools and Services", "FinOps Assessment"),
}
CAPABILITIES = tuple(dict.fromkeys(c for q in sorted(QMAP) for c in QMAP[q]))  # 22, in first-mention order
# FinOps Framework domains (finops.org/framework/domains, read 2026-10-21). Our capability names drop the words FinOps, "&" is written "and".
DOMAINS = {
    "Understand Usage and Cost": ("Data Ingestion", "Allocation", "Reporting and Analytics", "Anomaly Management"),
    "Quantify Business Value": ("Planning and Estimating", "Forecasting", "Budgeting", "KPIs and Benchmarking", "Unit Economics"),
    "Optimize Usage and Cost": (
        "Architecting and Workload Placement",
        "Rate Optimization",
        "Usage Optimization",
        "Sustainability",
        "Licensing and SaaS",
    ),
    "Manage the FinOps Practice": (
        "Practice Operations",
        "Governance, Policy and Risk",
        "FinOps Assessment",
        "Automation Tools and Services",
        "FinOps Education and Enablement",
        "Invoicing and Chargeback",
        "Intersecting Disciplines",
        "Executive Strategy Alignment",
    ),
}
DOMAIN_OF = {c: d for d, cs in DOMAINS.items() for c in cs}
DISCLAIMER = (
    "Screening level from questionnaire answers only. Technical evidence from the Azure scan is not part of these levels. "
    "Targets are set by the owner; a level below target is a prompt for a conversation, not a failure."
)


class MaturityError(FcatError):
    pass


def load(path) -> dict:
    try:
        d = tomllib.loads(pathlib.Path(path).read_text())
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise MaturityError(f"cannot read maturity input {path}: {e}") from e
    extra = set(d) - {"answers", "targets", "meta"}
    if extra:
        raise MaturityError(f"unknown tables in maturity input: {sorted(extra)}")
    return d


def evaluate(d: dict) -> dict:
    answers = {}
    for k, v in (d.get("answers") or {}).items():
        key = str(k).lower()
        if not key.startswith("q") or not key[1:].isdigit() or not 1 <= int(key[1:]) <= QUESTIONS:
            raise MaturityError(f"unknown answer key '{k}': use q1 to q{QUESTIONS}")
        a = str(v).strip().upper()
        if a not in {"A", "B", "C", "D"}:
            raise MaturityError(f"answer {k} must be A, B, C or D, got '{v}'")
        answers[int(key[1:])] = a
    targets = {}
    for cap, lvl in (d.get("targets") or {}).items():
        match = next((c for c in CAPABILITIES if c.lower() == str(cap).lower()), None)
        if match is None:
            raise MaturityError(f"unknown capability '{cap}' in [targets]; valid names: {', '.join(CAPABILITIES)}")
        if str(lvl).lower() not in LEVELS:
            raise MaturityError(f"target for '{cap}' must be one of {', '.join(LEVELS)}, got '{lvl}'")
        targets[match] = str(lvl).lower()

    rows = []
    for cap in CAPABILITIES:
        qs = [q for q in sorted(QMAP) if cap in QMAP[q]]
        got = {q: answers.get(q) for q in qs}
        levels = [ANSWER[a] for a in got.values() if a in ANSWER]
        unsure = [q for q, a in got.items() if a == "D"]
        unanswered = [q for q, a in got.items() if a is None]
        current = min(levels, key=LEVELS.index) if levels else None
        target = targets.get(cap)
        if current is None:
            status = "needs_input"
        elif target is None:
            status = "no_target"
        else:
            diff = LEVELS.index(current) - LEVELS.index(target)
            status = "below" if diff < 0 else "meets" if diff == 0 else "above"
        rows.append(
            {
                "capability": cap,
                "domain": DOMAIN_OF[cap],
                "questions": qs,
                "current": current,
                "target": target,
                "status": status,
                "partial": bool(levels) and bool(unsure or unanswered),
                "unsure_questions": unsure,
                "unanswered_questions": unanswered,
            }
        )
    counts = {s: sum(1 for r in rows if r["status"] == s) for s in ("below", "meets", "above", "no_target", "needs_input")}
    return {"version": "0.1", "disclaimer": DISCLAIMER, "counts": counts, "capabilities": rows}


def markdown(res: dict) -> str:
    c = res["counts"]
    lines = [
        "# Maturity screening with targets",
        "",
        res["disclaimer"],
        "",
        f"Below target: {c['below']}. Meets target: {c['meets']}. Above target: {c['above']}. No target set: {c['no_target']}. Needs input: {c['needs_input']}.",
        "",
        "| Capability | Current | Target | Status | Note |",
        "|---|---|---|---|---|",
    ]
    for r in res["capabilities"]:
        note = []
        if r["partial"]:
            note.append("some mapped questions unsure or unanswered")
        if r["status"] == "needs_input":
            note.append("no usable answer")
        lines.append(
            f"| {r['capability']} | {r['current'] or 'needs input'} | {r['target'] or 'none set'} | {r['status'].replace('_', ' ')} | {'; '.join(note)} |"
        )
    return "\n".join(lines) + "\n"
