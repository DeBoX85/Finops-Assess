"""Interactive dashboard in two audiences from the same report document (backlog 39, owner agreed 2026-10-21).

operator: everything, plus evidence, notes and review status (kept in the browser only), collector errors and the API call count.
customer: read-only like a PDF with browsing. No notes, no rule versions or data digests, no collector error text, no API call log, no config or
          branding controls. Branding is fixed at generation time.
Findings, "not assessed, because X" and the self-audit result are in BOTH versions and cannot be left out.
Anything a version must not contain is left out of the data at generation time; nothing is hidden with CSS or script, because everything in an
HTML file can be read by whoever holds it. Report values only ever reach the page through text nodes (see dash_assets.JS)."""

from __future__ import annotations

import json
import pathlib
import re

from .config import ReportOptions
from .dash_assets import CSS, js_for

AUDIENCES = ("operator", "customer")
DOMAIN_NAMES = {
    "orphaned": "Orphaned resources",
    "governance": "Cost governance",
    "billing": "Billing",
    "monitoring": "Monitoring",
    "compute": "Compute",
    "storage": "Storage",
    "security": "Security",
    "modernization": "Retired and legacy SKUs",
    "licensing": "Licensing",
    "optimization": "Optimization",
    "advisor": "Azure Advisor",
}
# Domain-level wording for "why it matters" and "what to check first". Per-check wording is a later step (backlog 39).
HELP = {
    "orphaned": {
        "why": "Resources nothing uses can still be billed.",
        "check": "Confirm with the owner that nothing depends on it. F-CAT never deletes anything.",
    },
    "governance": {
        "why": "These show how cost is controlled, not waste. Missing controls make cost hard to assign and surprises hard to catch.",
        "check": "Ask who owns the control. F-CAT only sees what this identity can read, so a control may exist elsewhere.",
    },
    "optimization": {
        "why": "A setting or size that may be more expensive than the workload needs.",
        "check": "Ask the workload owner whether the current setting is needed. This is a prompt, not an instruction.",
    },
    "modernization": {
        "why": "Retired or legacy SKUs can lose support or cost more.",
        "check": "Check that the retirement date applies to your workload, then plan the move.",
    },
    "licensing": {
        "why": "Licence benefits you already own may not be applied.",
        "check": "F-CAT cannot see your licence agreements. Someone who knows them must confirm eligibility.",
    },
    "advisor": {
        "why": "Microsoft's own recommendation, passed through as is.",
        "check": "We have not verified its saving figure. Open it in Azure Advisor for the detail.",
    },
    "monitoring": {"why": "Retention and caps drive monitoring cost.", "check": "Review whether the setting matches what the team needs."},
    "security": {
        "why": "Paid security plans cost money in every environment they cover.",
        "check": "Review whether the plan is needed in this environment.",
    },
    "billing": {
        "why": "Affects how much cost data F-CAT can read for this subscription.",
        "check": "Confirm the billing account type with whoever manages the agreement.",
    },
    "compute": {
        "why": "Virtual machines that run when nobody needs them are billed for compute.",
        "check": "Ask the owner whether the machine needs to run around the clock.",
    },
    "storage": {
        "why": "Storage settings decide what old or duplicate data costs.",
        "check": "Ask the owner whether the tier or redundancy matches the need, such as a test workload.",
    },
    "_": {"why": "This item may add cost without adding value.", "check": "Ask the owner of the resource."},
}
VALIDATION = {
    "offline-only": "Not yet verified on a live tenant. Treat as a prompt to look, not as a confirmed fact.",
    "live": "Verified on a live tenant.",
}
_MISSING = re.compile(r"^missing collector data: (.*)$")


def plain_reason(status: str, reason: str, audience: str) -> str:
    """One sentence a non-specialist can read. Custom reasons written by a check are already sentences and pass through."""
    if status == "failed":
        return "The check hit an error and did not finish." + (f" ({reason})" if audience == "operator" and reason else "")
    if status == "skipped":
        return "Switched off for this run." + (f" ({reason})" if audience == "operator" and reason else "")
    m = _MISSING.match(reason or "")
    if m:
        return "The data this check needs could not be read from this environment, so it did not run." + (
            f" ({m.group(1)})" if audience == "operator" else ""
        )
    return reason or "Not assessed."


def _sub_of(rid: str) -> str:
    m = re.search(r"/subscriptions/([^/]+)", rid, re.I)
    return m.group(1) if m else "-"


def view_data(
    doc: dict, audience: str, opts: ReportOptions | None = None, changes: dict | None = None, maturity: dict | None = None
) -> dict:
    if audience not in AUDIENCES:
        raise ValueError(f"audience must be one of {AUDIENCES}")
    op = audience == "operator"
    o = opts or ReportOptions()
    m = doc["manifest"]
    status = {c["id"]: c for c in m["checks"]}
    cat = {c["id"]: c for c in doc["check_catalogue"]}
    counts: dict = {}
    for f in doc["findings"]:
        counts[f["check_id"]] = counts.get(f["check_id"], 0) + 1
    checks = []
    for cid, c in cat.items():
        s = status.get(cid, {"status": "not_assessed", "reason": "no status recorded"})
        checks.append(
            {
                "id": cid,
                "title": c["title"],
                "domain": c["domain"],
                "conf": c["confidence"],
                "status": s["status"],
                "count": counts.get(cid, 0),
                "plain": plain_reason(s["status"], s.get("reason", ""), audience),
                "reason": s.get("reason", "") if op else "",
                "validationText": VALIDATION.get(c.get("validation", ""), "Validation state unknown.")
                + " "
                + str(c.get("confidence_note", "")),
            }
        )
    findings = []
    for f in doc["findings"]:
        item = {
            "check": f["check_id"],
            "sev": f["severity"],
            "msg": f["message"],
            "res": f["resource_id"],
            "name": f["resource_id"].rstrip("/").rsplit("/", 1)[-1],
            "sub": _sub_of(f["resource_id"]),
            "fp": f["fingerprint"],
            "details": f.get("details", {}),
        }
        if op:
            item["evidence"] = f.get("evidence", {})
        findings.append(item)
    au = doc.get("audit", {})
    show_detail = op or ("audit_detail" not in o.hide) or au.get("status") != "pass"  # a failed audit is never tucked away
    scope = (
        ", ".join(f"{k.replace('_', ' ')}: {'not assessed' if v is None else v}" for k, v in m.get("scope", {}).items())
        or "scope not collected"
    )
    data = {
        "audience": audience,
        "title": o.title,
        "subtitle": o.subtitle,
        "preparedFor": o.prepared_for,
        "preparedBy": o.prepared_by,
        "footer": o.footer,
        "logo": o.logo_data_uri,
        "scopeText": f"Scope: {scope}.",
        "run": {
            "started": m.get("started") or "not recorded",
            "tool": m.get("tool_version") or "not recorded",
            "fingerprint": au.get("report_hash", "n/a"),
            **({"apiCalls": len(m.get("api_calls", []))} if op else {}),
        },
        "audit": {
            "status": au.get("status", "not run"),
            "limits": au.get("limits", ""),
            "invariants": [{k: i[k] for k in ("id", "description", "passed", "violation_count")} for i in au.get("invariants", [])]
            if show_detail
            else [],
        },
        "domains": DOMAIN_NAMES,
        "help": HELP,
        "checks": checks,
        "findings": findings,
        "collectorErrors": m.get("collector_errors", []) if op else [],
        "changes": changes,
        "maturity": maturity,
    }
    return data


def render(
    path, doc: dict, audience: str, opts: ReportOptions | None = None, changes: dict | None = None, maturity: dict | None = None
) -> None:
    o = opts or ReportOptions()
    data = json.dumps(view_data(doc, audience, o, changes, maturity), separators=(",", ":"))
    data = (
        data.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    import html  # noqa: PLC0415

    accent = f":root{{--acc:{o.accent}}}" if o.accent else ""
    title = html.escape(o.title)
    page = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{title}</title><style>{CSS}{accent}</style></head><body><div id="app"></div>'
        f"<noscript><p>This report needs JavaScript. The same findings are in report.json and report.xlsx, and report.html is the static version.</p></noscript>"
        f"<script>const D={data};{js_for(audience)}</script></body></html>"
    )
    pathlib.Path(path).write_text(page, encoding="utf-8")
