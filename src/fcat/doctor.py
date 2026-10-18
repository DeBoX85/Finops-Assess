"""`fcat doctor`: what access the checks need (offline, from the registry) and what the current login can see (read-only probes). docs/DOCTOR.md.
Probes use only calls the allowlist already permits (ARG POST). Results are counts and statuses, never names or ids. All probe semantics are UNVERIFIED live."""

from __future__ import annotations

import re

from . import arg, checks
from .errors import AuthError, FcatError

PROBES = (
    (
        "subscriptions_visible",
        "resourcecontainers | where type == 'microsoft.resources/subscriptions' | summarize n=count()",
        "Reader on at least one subscription",
    ),
    ("resources_readable", "resources | summarize n=count()", "Reader on the subscriptions to assess"),
    (
        "management_groups_visible",
        "resourcecontainers | where type =~ 'microsoft.management/managementgroups' | summarize n=count()",
        "read access at management group level (optional)",
    ),
    ("advisor_readable", "advisorresources | summarize n=count()", "Reader (Advisor recommendations feed ADV-COST-01)"),
)


def needs() -> list[dict]:
    """Access need list grouped by permission, straight from check metadata so it cannot drift from the code."""
    checks.load_builtin()
    by: dict[str, list] = {}
    for m, _ in checks.REGISTRY:
        for perm in m.permissions:
            by.setdefault(perm, []).append({"id": m.id, "title": m.title, "collectors": list(m.collectors), "run_cost": m.run_cost})
    return [{"permission": p, "checks": sorted(v, key=lambda c: c["id"])} for p, v in sorted(by.items())]


def needs_markdown() -> str:
    out = [
        "# Access F-CAT needs, and why",
        "",
        "Generated from the check catalogue. F-CAT only reads; it never changes anything in your environment.",
        "",
    ]
    for n in needs():
        out += [f"## {n['permission']}", "", "| Check | What it looks at | Cost of running |", "|---|---|---|"]
        out += [f"| {c['id']}: {c['title']} | {', '.join(c['collectors'])} | {c['run_cost']} |" for c in n["checks"]]
        out.append("")
    out += ["Without this access the affected checks are reported as 'not assessed', never as 'no findings'.", ""]
    return "\n".join(out)


def _status_from_error(msg: str) -> str:
    m = re.search(r"HTTP (\d{3})", msg)
    code = m.group(1) if m else ""
    return {"403": "not_allowed", "401": "not_allowed", "429": "throttled"}.get(code, "unknown")


def probe(client, token_provider, subscriptions=None, management_groups=None) -> list[dict]:
    """Never raises for a failing probe: each result is pass | not_allowed | throttled | unknown, with a reason. Unknown is never guessed as pass."""
    res = []
    try:
        token_provider.token()
        res.append({"probe": "token", "status": "pass", "detail": "token obtained"})
    except AuthError as e:
        return [{"probe": "token", "status": "not_allowed", "detail": f"{e}; the other probes were not run"}]
    ident = token_provider.identity()
    res.append(
        {
            "probe": "identity",
            "status": "pass" if ident.get("tenant_id") else "unknown",
            "detail": f"principal type: {ident.get('principal_type', 'unknown')}",
        }
    )
    for name, kql, needs_ in PROBES:
        try:
            qr = arg.query(client, kql, subscriptions or None, management_groups or None)
            n = qr.rows[0].get("n") if qr.rows and isinstance(qr.rows[0], dict) else None
            ok = isinstance(n, int) and not isinstance(n, bool) and n > 0
            detail = f"count {n}" + (f"; warnings: {len(qr.warnings)}" if qr.warnings else "")
            res.append(
                {
                    "probe": name,
                    "status": "pass" if ok else "unknown",
                    "detail": detail if ok else f"{detail}; zero or unreadable, cannot tell whether {needs_} is missing",
                }
            )
        except FcatError as e:
            st = _status_from_error(str(e))
            res.append({"probe": name, "status": st, "detail": f"{e}; needs {needs_}"})
    return res


def render_probe_table(results: list[dict]) -> str:
    return "\n".join(f"{r['probe']:<28}{r['status']:<13}{r['detail']}" for r in results)
