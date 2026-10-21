"""Roll-up of several finished analyses (backlog 41, owner option B: one customer, several tenants or scopes). Pure offline function over report.json
documents; no Azure access, no login, no new collector. Each scope is analysed by its own normal run (its own login, its own config); this
module only puts the results side by side. Switching the roll-up on or off therefore means running `fcat rollup` or not; the single-scope
default is unchanged.

Limits, stated in every output:
- Scopes are not de-duplicated against each other: a resource visible from two logins would count twice.
- Amounts are never added (currencies and billing types differ); only counts are summed.
- Counts of findings are not comparable across scopes that ran different checks, so every cell says whether the check ran.
- Contents of the output: labels, counts, check ids and reasons only. No resource ids, tenant ids or subscription ids."""

from __future__ import annotations

import html
import json
import pathlib
from typing import Any

from .compare import CompareError, load
from .errors import FcatError

VERSION = "0.1"
SEVERITIES = ("high", "medium", "low", "info")


class RollupError(FcatError):
    pass


def _label(path, given):
    return given or pathlib.Path(path).resolve().parent.name or "scope"


def build(paths, labels=None) -> dict:
    if len(paths) < 2:
        raise RollupError("a roll-up needs at least two report.json files; for one scope use the normal dashboards")
    labels = list(labels or [])
    if labels and len(labels) != len(paths):
        raise RollupError(f"{len(labels)} labels given for {len(paths)} reports; give one --label per report or none")
    docs = []
    for i, p in enumerate(paths):
        try:
            docs.append((_label(p, labels[i] if labels else None), load(p)))
        except CompareError as e:
            raise RollupError(str(e)) from e
    names = [n for n, _ in docs]
    if len(set(names)) != len(names):
        raise RollupError("scope labels must be unique; use --label to name each report")
    scopes, check_ids, meta = [], set(), {}
    for name, doc in docs:
        m = doc["manifest"]
        cat = {c["id"]: c for c in doc.get("check_catalogue", []) if isinstance(c, dict) and "id" in c}
        meta.update({k: {"title": v.get("title"), "domain": v.get("domain")} for k, v in cat.items()})
        st = {c["id"]: c for c in m.get("checks", []) if isinstance(c, dict) and "id" in c}
        sev = dict.fromkeys(SEVERITIES, 0)
        dom: dict = {}
        for f in doc["findings"]:
            sev[f.get("severity", "info")] = sev.get(f.get("severity", "info"), 0) + 1
            d = (cat.get(f["check_id"]) or {}).get("domain", "unknown")
            dom[d] = dom.get(d, 0) + 1
        reasons: dict = {}
        for c in st.values():
            if c.get("status") != "ran":
                key = f"{c.get('status')}: {str(c.get('reason') or '')[:120]}"
                reasons[key] = reasons.get(key, 0) + 1
        logic = {}
        for f in doc["findings"]:
            h = (f.get("evidence") or {}).get("logic_hash")
            if h:
                logic[f["check_id"]] = h
        check_ids |= set(st)
        scopes.append(
            {
                "label": name,
                "redacted": bool(m.get("redacted")),
                "tool_version": m.get("tool_version"),
                "audit": (doc.get("audit") or {}).get("status"),
                "audit_fingerprint": (doc.get("audit") or {}).get("report_hash"),
                "subscriptions": (m.get("scope") or {}).get("subscriptions"),
                "findings": len(doc["findings"]),
                "by_severity": sev,
                "by_domain": dict(sorted(dom.items())),
                "checks_ran": sum(1 for c in st.values() if c.get("status") == "ran"),
                "checks_not_ran": sum(1 for c in st.values() if c.get("status") != "ran"),
                "not_run_reasons": dict(sorted(reasons.items(), key=lambda kv: (-kv[1], kv[0]))),
                "_status": {k: v.get("status") for k, v in st.items()},
                "_counts": {k: v.get("findings", 0) for k, v in st.items()},
                "_logic": logic,
            }
        )
    matrix = []
    for cid in sorted(check_ids):
        cells: list[dict[str, Any]] = []
        for s in scopes:
            status = s["_status"].get(cid)
            cells.append({"state": status or "not in this run", "findings": s["_counts"].get(cid, 0) if status == "ran" else None})
        total = sum(c["findings"] or 0 for c in cells)
        ran = sum(1 for c in cells if c["state"] == "ran")
        if total or ran < len(scopes):
            matrix.append({"check_id": cid, "title": (meta.get(cid) or {}).get("title"), "total": total, "ran_in": ran, "cells": cells})
    matrix.sort(key=lambda r: (-r["total"], r["check_id"]))
    warnings = []
    bad_audit = [s["label"] for s in scopes if s["audit"] != "pass"]
    if bad_audit:
        warnings.append(f"self-audit did not pass for: {', '.join(bad_audit)}. Do not use those scopes' numbers.")
    red = [s["label"] for s in scopes if s["redacted"]]
    if red and len(red) != len(scopes):
        warnings.append(
            f"redacted and unredacted reports are mixed (redacted: {', '.join(red)}); counts are fine, names are not comparable"
        )
    versions = sorted({str(s["tool_version"]) for s in scopes})
    if len(versions) > 1:
        warnings.append(f"reports come from different tool versions ({', '.join(versions)}); a check may behave differently between scopes")
    drift = sorted(cid for cid in check_ids if len({s["_logic"][cid] for s in scopes if cid in s["_logic"]}) > 1)
    if drift:
        warnings.append(
            f"{len(drift)} check(s) ran with different logic versions across scopes (for example {drift[0]}): counts are not strictly comparable"
        )
    for s in scopes:
        for k in ("_status", "_counts", "_logic"):
            del s[k]
    totals = {
        "scopes": len(scopes),
        "findings": sum(s["findings"] for s in scopes),
        "by_severity": {k: sum(s["by_severity"].get(k, 0) for s in scopes) for k in SEVERITIES},
    }
    return {"version": VERSION, "scopes": scopes, "totals": totals, "checks": matrix, "warnings": warnings, "limits": LIMITS}


LIMITS = [
    "Scopes are analysed separately; nothing is de-duplicated between them, so a resource visible from two logins counts twice.",
    "Amounts are never added; only counts are summed.",
    "A check that did not run in a scope shows its state instead of a zero.",
    "Counts show what the checks found, not what is true: every check is offline-only until it passes the live test gate.",
]


def markdown(r: dict) -> str:
    out = ["# Roll-up of several scopes", ""]
    out += [f"- Warning: {w}" for w in r["warnings"]] + ([""] if r["warnings"] else [])
    out += [
        "| Scope | Self-audit | Findings | High | Medium | Low | Info | Checks ran | Not run |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for s in r["scopes"]:
        b = s["by_severity"]
        out.append(
            f"| {s['label']} | {s['audit']} | {s['findings']} | {b['high']} | {b['medium']} | {b['low']} | {b['info']} | {s['checks_ran']} | {s['checks_not_ran']} |"
        )
    t = r["totals"]
    out += [
        f"| **Total ({t['scopes']} scopes)** |  | {t['findings']} | {t['by_severity']['high']} | {t['by_severity']['medium']} | {t['by_severity']['low']} | {t['by_severity']['info']} |  |  |",
        "",
    ]
    out += ["## Checks across scopes (findings, or why the check did not run)", ""]
    head = "| Check | " + " | ".join(s["label"] for s in r["scopes"]) + " | Total |"
    out += [head, "|" + "---|" * (len(r["scopes"]) + 2)]
    for row in r["checks"]:
        cells = [str(c["findings"]) if c["state"] == "ran" else c["state"] for c in row["cells"]]
        out.append(f"| {row['check_id']} {row['title'] or ''} | " + " | ".join(cells) + f" | {row['total']} |")
    out += ["", "## Limits", ""] + [f"- {x}" for x in r["limits"]] + [""]
    return "\n".join(out)


def _e(x):
    return html.escape("" if x is None else str(x))


CSS = """:root{--bg:#fff;--fg:#1b1f24;--mut:#4a5560;--line:#c4ccd4;--warn:#7d4e00;--bad:#b3141f;--ok:#17692f}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--mut:#a5afba;--line:#3a424b;--warn:#e3b341;--bad:#ff7b72;--ok:#56d364}}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0 auto;max-width:1200px;padding:16px}
h1{font-size:24px}h2{font-size:18px;margin-top:28px}table{border-collapse:collapse;width:100%;margin:8px 0}
caption{text-align:left;color:var(--mut);padding-bottom:4px}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}th{color:var(--mut);font-weight:600}
td.n,th.n{text-align:right}.warn{color:var(--warn);font-weight:600}.bad{color:var(--bad);font-weight:600}.ok{color:var(--ok)}
.scroll{overflow-x:auto}@media print{body{max-width:none}}"""


def html_page(r: dict, title="Roll-up of several scopes") -> str:
    def audit(s):
        return f'<span class="{"ok" if s["audit"] == "pass" else "bad"}">{_e(s["audit"])}</span>'

    rows = "".join(
        f"<tr><th scope='row'>{_e(s['label'])}</th><td>{audit(s)}</td><td class='n'>{s['findings']}</td>"
        + "".join(f"<td class='n'>{s['by_severity'][k]}</td>" for k in SEVERITIES)
        + f"<td class='n'>{s['checks_ran']}</td><td class='n'>{s['checks_not_ran']}</td></tr>"
        for s in r["scopes"]
    )
    t = r["totals"]
    foot = (
        f"<tr><th scope='row'>Total ({t['scopes']} scopes)</th><td></td><td class='n'>{t['findings']}</td>"
        + "".join(f"<td class='n'>{t['by_severity'][k]}</td>" for k in SEVERITIES)
        + "<td></td><td></td></tr>"
    )
    heads = "".join(f"<th scope='col'>{_e(s['label'])}</th>" for s in r["scopes"])
    mrows = "".join(
        f"<tr><th scope='row'>{_e(x['check_id'])} {_e(x['title'])}</th>"
        + "".join(f"<td>{c['findings'] if c['state'] == 'ran' else _e(c['state'])}</td>" for c in x["cells"])
        + f"<td class='n'>{x['total']}</td></tr>"
        for x in r["checks"]
    )
    warn = "".join(f"<li class='warn'>{_e(w)}</li>" for w in r["warnings"])
    lim = "".join(f"<li>{_e(x)}</li>" for x in r["limits"])
    return (
        f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{_e(title)}</title><style>{CSS}</style></head><body><main><h1>{_e(title)}</h1>"
        + (f"<ul>{warn}</ul>" if warn else "")
        + "<h2>Scopes</h2><div class='scroll'><table><caption>One row per analysed scope</caption><thead><tr><th scope='col'>Scope</th><th scope='col'>Self-audit</th>"
        "<th scope='col' class='n'>Findings</th><th scope='col' class='n'>High</th><th scope='col' class='n'>Medium</th><th scope='col' class='n'>Low</th>"
        f"<th scope='col' class='n'>Info</th><th scope='col' class='n'>Checks ran</th><th scope='col' class='n'>Not run</th></tr></thead><tbody>{rows}</tbody><tfoot>{foot}</tfoot></table></div>"
        f"<h2>Checks across scopes</h2><div class='scroll'><table><caption>Findings per check and scope, or the reason the check did not run</caption><thead><tr><th scope='col'>Check</th>{heads}<th scope='col' class='n'>Total</th></tr></thead><tbody>{mrows}</tbody></table></div>"
        f"<h2>Limits</h2><ul>{lim}</ul></main></body></html>"
    )


def write(result: dict, out) -> None:
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "rollup.json").write_text(json.dumps(result, indent=1))
    (out / "rollup.md").write_text(markdown(result))
    (out / "rollup.html").write_text(html_page(result))
