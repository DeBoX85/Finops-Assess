"""Single-file HTML report from the same document as the JSON. Print-friendly (browser Print -> PDF).
Phase 1 layout is functional, not final design. All values are HTML-escaped."""
import html, json, pathlib

CSS = """:root{--bg:#fff;--fg:#1b1f24;--mut:#59636e;--line:#d0d7de;--warn:#9a6700;--bad:#cf222e;--ok:#1a7f37}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--warn:#d29922;--bad:#f85149;--ok:#3fb950}}
body{background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,sans-serif;margin:0 auto;max-width:1100px;padding:16px}
h1{font-size:22px}h2{font-size:17px;margin-top:28px}table{border-collapse:collapse;width:100%;margin:8px 0}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}th{color:var(--mut);font-weight:600}
.s-ran{color:var(--ok)}.s-skipped,.s-not_assessed{color:var(--warn);font-weight:600}.s-failed{color:var(--bad);font-weight:600}
.note{color:var(--mut)}@media print{body{max-width:none}a{color:inherit}}"""

def e(x):
    return html.escape("" if x is None else str(x))

def render(path, doc):
    m = doc["manifest"]
    rows_c = "".join(f"<tr><td>{e(c['id'])}</td><td class='s-{e(c['status'])}'>{e(c['status'].replace('_',' '))}</td>"
                     f"<td>{e(c.get('reason', ''))}{e(c.get('findings', '')) if c['status']=='ran' else ''}</td></tr>" for c in m["checks"])
    rows_f = "".join(f"<tr><td>{e(f['check_id'])}</td><td>{e(f['severity'])}</td><td>{e(f['message'])}</td><td>{e(f['resource_id'])}</td></tr>"
                     for f in doc["findings"]) or "<tr><td colspan=4 class=note>No findings from the checks that ran.</td></tr>"
    sc = m.get("scope", {})
    scope = ", ".join(f"{e(k.replace('_',' '))}: {'not assessed' if v is None else v}" for k, v in sc.items()) or "not collected"
    errs = "".join(f"<li>{e(x['collector'])}: {e(x['error'])}</li>" for x in m.get("collector_errors", []))
    out = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>F-CAT assessment report</title><style>{CSS}</style></head><body>
<h1>F-CAT assessment report</h1>
<p class="note">Tool {e(m['tool_version'])} (commit {e(m.get('git_commit'))}), schema {e(doc['schema_version'])}. Run {e(m['started'])} to {e(m['ended'])}. Scope: {scope}.</p>
<p class="note">Read-only assessment. Checks marked skipped or not assessed were NOT evaluated; their absence from the findings is not a pass.</p>
<h2>Check coverage</h2><table><tr><th>Check</th><th>Status</th><th>Detail</th></tr>{rows_c}</table>
{('<h2>Collector errors</h2><ul>'+errs+'</ul>') if errs else ''}
<h2>Findings ({len(doc['findings'])})</h2><table><tr><th>Check</th><th>Severity</th><th>Finding</th><th>Resource</th></tr>{rows_f}</table>
</body></html>"""
    pathlib.Path(path).write_text(out, encoding="utf-8")
