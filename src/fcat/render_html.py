"""Single-file HTML report from the same document as the JSON. Print-friendly (browser Print -> PDF).
Phase 1 layout is functional, not final design. All values are HTML-escaped."""

import html
import pathlib

CSS = """:root{--bg:#fff;--fg:#1b1f24;--mut:#59636e;--line:#d0d7de;--warn:#9a6700;--bad:#cf222e;--ok:#1a7f37}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--warn:#d29922;--bad:#f85149;--ok:#3fb950}}
body{background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,sans-serif;margin:0 auto;max-width:1100px;padding:16px}
h1{font-size:22px}h2{font-size:17px;margin-top:28px}table{border-collapse:collapse;width:100%;margin:8px 0}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}th{color:var(--mut);font-weight:600}
.s-ran{color:var(--ok)}.s-skipped,.s-not_assessed{color:var(--warn);font-weight:600}.s-failed{color:var(--bad);font-weight:600}
.note{color:var(--mut)}@media print{body{max-width:none}a{color:inherit}}"""


def e(x):
    return html.escape("" if x is None else str(x))


def _accent_css(o):
    return f":root{{--accent:{o.accent}}}" if o and o.accent else ":root{--accent:var(--fg)}"


def render(path, doc, opts=None):
    from .config import ReportOptions  # noqa: PLC0415

    o = opts or ReportOptions()
    m = doc["manifest"]
    val = {c["id"]: c.get("validation", "") for c in doc["check_catalogue"]}
    rows_c = "".join(
        f"<tr><td>{e(c['id'])}</td><td class='s-{e(c['status'])}'>{e(c['status'].replace('_', ' '))}</td>"
        f"<td>{e(c.get('reason', ''))}{e(c.get('findings', '')) if c['status'] == 'ran' else ''}</td><td>{e(val.get(c['id'], ''))}</td></tr>"
        for c in m["checks"]
    )
    rows_f = (
        "".join(
            f"<tr><td>{e(f['check_id'])}</td><td>{e(f['severity'])}</td><td>{e(f['message'])}</td><td>{e(f['resource_id'])}</td></tr>"
            for f in doc["findings"]
        )
        or "<tr><td colspan=4 class=note>No findings from the checks that ran.</td></tr>"
    )
    sc = m.get("scope", {})
    scope = ", ".join(f"{e(k.replace('_', ' '))}: {'not assessed' if v is None else v}" for k, v in sc.items()) or "not collected"
    au = doc.get("audit", {})
    rows_a = "".join(
        f"<tr><td>{e(i['id'])}</td><td class='s-{'ran' if i['passed'] else 'failed'}'>{'pass' if i['passed'] else 'FAIL'}</td>"
        f"<td>{e(i['description'])}{(' (' + e(i['violation_count']) + ' violations)') if not i['passed'] else ''}</td></tr>"
        for i in au.get("invariants", [])
    )
    hide_detail = "audit_detail" in o.hide and au.get("status") == "pass"  # a failed audit is never tucked away
    audit_html = (
        f"<h2>Self-audit: {e(au.get('status', 'not run')).upper()}</h2>"
        f"<p class='note'>Report fingerprint {e(au.get('report_hash'))}. {e(au.get('limits', ''))}</p>"
        + ("" if hide_detail else f"<table><tr><th>Check</th><th>Result</th><th>What it verifies</th></tr>{rows_a}</table>")
        if au
        else ""
    )
    logo = f'<img alt="" src="{o.logo_data_uri}" style="max-height:56px;float:right">' if o.logo_data_uri else ""
    meta = " | ".join(
        x
        for x in (f"Prepared for {o.prepared_for}" if o.prepared_for else "", f"Prepared by {o.prepared_by}" if o.prepared_by else "")
        if x
    )
    head_extra = (f"<p>{e(o.subtitle)}</p>" if o.subtitle else "") + (f"<p class='note'>{e(meta)}</p>" if meta else "")
    foot = f"<hr><p class='note'>{e(o.footer)}</p>" if o.footer else ""
    counts: dict = {}
    for c in m["checks"]:
        counts[c["status"]] = counts.get(c["status"], 0) + 1
    summary = f"{len(m['checks'])} checks: " + ", ".join(f"{n} {k.replace('_', ' ')}" for k, n in sorted(counts.items())) + "."
    coverage_html = (
        f"<h2>Check coverage</h2><p class='note'>{e(summary)} Checks that did not run were not evaluated; the full table is in the Excel and JSON files.</p>"
        if "coverage" in o.hide
        else f"<h2>Check coverage</h2><table><tr><th>Check</th><th>Status</th><th>Detail</th><th>Validation</th></tr>{rows_c}</table>"
    )
    errs = "".join(f"<li>{e(x['collector'])}: {e(x['error'])}</li>" for x in m.get("collector_errors", []))
    out = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(o.title)}</title><style>{CSS}{_accent_css(o)}h1,h2{{border-left:4px solid var(--accent);padding-left:8px}}</style></head><body>
{logo}<h1>{e(o.title)}</h1>{head_extra}
<p class="note">Tool {e(m["tool_version"])} (commit {e(m.get("git_commit"))}), schema {e(doc["schema_version"])}. Run {e(m["started"])} to {e(m["ended"])}. Scope: {scope}.</p>
<p class="note">Read-only assessment. Checks marked skipped or not assessed were NOT evaluated; their absence from the findings is not a pass.</p>
{coverage_html}
{("<h2>Collector errors</h2><ul>" + errs + "</ul>") if errs and "collector_errors" not in o.hide else ""}
<h2>Findings ({len(doc["findings"])})</h2><table><tr><th>Check</th><th>Severity</th><th>Finding</th><th>Resource</th></tr>{rows_f}</table>
{audit_html}
{foot}
</body></html>"""
    pathlib.Path(path).write_text(out, encoding="utf-8")
