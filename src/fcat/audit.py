"""Layer A self-audit (docs/AUDIT.md): machine-checked invariants over the finished report document.
Runs on every report. Failing invariants are shown in every output format, never hidden.
These checks prove internal consistency only. They do NOT prove findings are true; that needs the human sampling audit."""

from __future__ import annotations

import hashlib
import json
import re

from .checks import fingerprint

AUDIT_VERSION = "0.1"
SEVERITIES = {"info", "low", "medium", "high"}
# Certainty wording we never want in a recommendation (docs/AUDIT.md section 2, language lint).
BANNED = re.compile(r"\b(will save|guarantee[ds]?|definitely|certainly|no risk|risk[- ]free|always saves?)\b", re.I)


class _F:  # minimal adapter so fingerprint() works on report dicts
    def __init__(self, d):
        self.check_id, self.resource_id, self.details = d["check_id"], d["resource_id"], d.get("details", {})


def report_hash(doc) -> str:
    """Hash of what the assessment concluded, excluding run times and API call logs, so re-analysing a snapshot must reproduce it."""
    core = {
        "catalogue": doc["check_catalogue"],
        "checks": [{k: v for k, v in c.items()} for c in doc["manifest"]["checks"]],
        "findings": doc["findings"],
    }
    return hashlib.sha256(json.dumps(core, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _inv(iid, text, violations):
    return {"id": iid, "description": text, "passed": not violations, "violations": violations[:20], "violation_count": len(violations)}


def build(doc) -> dict:
    findings = doc["findings"]
    catalogue = {c["id"] for c in doc["check_catalogue"]}
    checks = {c["id"]: c for c in doc["manifest"]["checks"]}
    errored = {e["collector"] for e in doc["manifest"].get("collector_errors", [])}
    cat_by_id = {c["id"]: c for c in doc["check_catalogue"]}
    out = []

    seen, dups = set(), []
    for f in findings:
        k = (f["check_id"], f["resource_id"])
        if k in seen:
            dups.append(f"{k[0]} {k[1]}")
        seen.add(k)
    out.append(_inv("INV-01", "No resource is reported twice by the same check", dups))

    out.append(
        _inv(
            "INV-02",
            "Every finding belongs to a check in the catalogue",
            [f["check_id"] for f in findings if f["check_id"] not in catalogue],
        )
    )

    out.append(
        _inv(
            "INV-03",
            "Every finding comes from a check that ran",
            [f["check_id"] for f in findings if checks.get(f["check_id"], {}).get("status") != "ran"],
        )
    )

    count_bad = []
    for cid, c in checks.items():
        if c["status"] == "ran":
            n = sum(1 for f in findings if f["check_id"] == cid)
            if n != c.get("findings"):
                count_bad.append(f"{cid}: manifest says {c.get('findings')}, report has {n}")
    out.append(_inv("INV-04", "Finding counts per check match the coverage table", count_bad))

    out.append(
        _inv(
            "INV-05",
            "Severity is one of info, low, medium, high",
            [f"{f['check_id']}: {f['severity']}" for f in findings if f["severity"] not in SEVERITIES],
        )
    )

    out.append(
        _inv(
            "INV-06",
            "Each finding's fingerprint recomputes from its content",
            [f["check_id"] for f in findings if f.get("fingerprint") != fingerprint(_F(f))],
        )
    )

    out.append(
        _inv(
            "INV-07",
            "Every finding names a resource and has a message",
            [f["check_id"] for f in findings if not f["resource_id"] or not f["message"]],
        )
    )

    out.append(
        _inv(
            "INV-08",
            "No certainty wording in finding text (language lint)",
            [f"{f['check_id']}: {f['message'][:60]}" for f in findings if BANNED.search(f["message"])],
        )
    )

    neg = []
    for f in findings:
        for k, v in f.get("details", {}).items():
            if k.lower().startswith("savings") and isinstance(v, (int, float)) and v < 0:
                neg.append(f"{f['check_id']}.{k}={v}")
    out.append(_inv("INV-09", "No negative savings figure", neg))

    ran_with_error = []
    for cid, c in checks.items():
        if c["status"] == "ran" and errored & set(cat_by_id.get(cid, {}).get("collectors", [])):
            ran_with_error.append(cid)
    out.append(_inv("INV-10", "No check reports as ran when a collector it needs had an error", ran_with_error))

    unevidenced = [f["check_id"] for f in findings if not f.get("evidence", {}).get("logic_hash")]
    out.append(_inv("INV-11", "Every finding carries an evidence trail (rule version and data digests)", unevidenced))

    status = "pass" if all(i["passed"] for i in out) else "fail"
    return {
        "version": AUDIT_VERSION,
        "status": status,
        "report_hash": report_hash(doc),
        "invariants": out,
        "limits": "Consistency checks only. They do not show that findings are true; precision needs the human sampling audit (docs/AUDIT.md layer C).",
    }
