"""Generate static dashboard mock-ups from tests/golden/report.json.

Mock-ups only: synthetic data, no real tenant, no cost figures (cost data does
not exist yet). Output: docs/mockups/*.html, self-contained, system fonts only.
Edit the BRAND block at the top of each page to try other branding.
"""

from __future__ import annotations

import collections
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "mockups"

CAPABILITIES = [
    ("Data Ingestion", "cost"),
    ("Allocation", "cost"),
    ("Reporting and Analytics", "cost"),
    ("Anomaly Management", "cost"),
    ("Planning and Estimating", "customer"),
    ("Forecasting", "cost"),
    ("Budgeting", "cost"),
    ("KPIs and Benchmarking", "customer"),
    ("Unit Economics", "customer"),
    ("Architecting and Workload Placement", "partial"),
    ("Usage Optimization", "partial"),
    ("Rate Optimization", "cost"),
    ("Sustainability", "customer"),
    ("Licensing and SaaS", "cost"),
    ("FinOps Practice Operations", "customer"),
    ("Governance, Policy and Risk", "unbuilt"),
    ("FinOps Assessment", "customer"),
    ("Automation, Tools and Services", "unbuilt"),
    ("Education and Enablement", "customer"),
    ("Invoicing and Chargeback", "cost"),
    ("Intersecting Disciplines", "customer"),
    ("Executive Strategy Alignment", "customer"),
]
CAP_TEXT = {
    "cost": "Not assessed: needs Cost Management data (not collected yet)",
    "customer": "Needs input: answered by your team, not readable from Azure",
    "partial": "Partial evidence from resource checks; no score yet",
    "unbuilt": "Not assessed: readable from Azure with Reader, check not built yet",
}

DOMAIN_NAMES = {
    "orphaned": "Orphaned resources",
    "billing": "Billing",
    "monitoring": "Monitoring",
    "compute": "Compute",
    "security": "Security",
    "modernization": "Retired and legacy SKUs",
    "licensing": "Licensing",
    "optimization": "Optimization",
    "advisor": "Azure Advisor",
}
SEV_ORDER = ["high", "medium", "low", "info"]

# Palette: validated default categorical slots (dataviz palette.md), light and dark.
CSS_TOKENS = """
:root{--bg:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#6b6963;
--grid:#e1e0d9;--axis:#c3c2b7;--ring:rgba(11,11,11,.10);--c1:#2a78d6;--c2:#eb6834;
--c3:#1baf7a;--c4:#eda100;--c5:#e87ba4;--seq:#2a78d6;--ok:#006300;--warn:#8a5a00;--crit:#b02a2a;}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0d0d0d;--surface:#1a1a19;
--ink:#f0efec;--ink2:#c3c2b7;--muted:#a09e96;--grid:#2c2c2a;--axis:#383835;
--ring:rgba(255,255,255,.10);--ok:#0ca30c;--warn:#fab219;--crit:#ec6a6a;}}
:root[data-theme=dark]{--bg:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;
--muted:#a09e96;--grid:#2c2c2a;--axis:#383835;--ring:rgba(255,255,255,.10);
--ok:#0ca30c;--warn:#fab219;--crit:#ec6a6a;}
"""

BASE_CSS = """
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:28px;line-height:1.2;margin:0 0 4px}h2{font-size:18px;margin:32px 0 8px}
p{max-width:68ch}.muted{color:var(--muted)}.sub{color:var(--ink2);margin:0 0 16px}
.banner{border:1px dashed var(--axis);padding:8px 12px;border-radius:6px;color:var(--ink2);
font-size:13px;margin-bottom:20px}
.panel{overflow-x:auto;background:var(--surface);border-radius:8px;box-shadow:0 0 0 1px var(--ring);padding:16px}
table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:6px 8px;
border-bottom:1px solid var(--grid);vertical-align:top}th{color:var(--ink2);font-weight:600;font-size:13px}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:0 8px;border-radius:10px;font-size:12px;
box-shadow:inset 0 0 0 1px var(--axis);color:var(--ink2)}
.bar{height:12px;border-radius:0 4px 4px 0;background:var(--seq)}
.tt{position:fixed;pointer-events:none;background:var(--surface);color:var(--ink);
box-shadow:0 0 0 1px var(--ring),0 4px 12px rgba(0,0,0,.15);padding:4px 8px;border-radius:6px;
font-size:12px;display:none;z-index:9}
button,select,input{font:inherit;color:var(--ink);background:var(--surface);
border:1px solid var(--axis);border-radius:6px;padding:4px 8px}
button:focus-visible,select:focus-visible,input:focus-visible,summary:focus-visible,a:focus-visible
{outline:2px solid var(--c1);outline-offset:2px}
.tabs button[aria-pressed=true]{border-color:var(--ink)}
@media (max-width:640px){.hide-sm{display:none}}
"""

TT_JS = """
const tt=document.createElement('div');tt.className='tt';document.body.append(tt);
document.querySelectorAll('[data-tip]').forEach(e=>{
e.addEventListener('mousemove',ev=>{tt.textContent=e.dataset.tip;tt.style.display='block';
tt.style.left=ev.clientX+12+'px';tt.style.top=ev.clientY+12+'px'});
e.addEventListener('mouseleave',()=>tt.style.display='none');
e.addEventListener('focus',()=>{tt.textContent=e.dataset.tip;const r=e.getBoundingClientRect();
tt.style.display='block';tt.style.left=r.left+'px';tt.style.top=r.bottom+6+'px'});
e.addEventListener('blur',()=>tt.style.display='none')});
"""

BANNER = (
    '<div class="banner" role="note">Mock-up. Synthetic data from the test estate, '
    "not a real tenant. No cost or savings figures are shown because the tool does not "
    "collect cost data yet. All checks are offline-only (not yet run on a real tenant).</div>"
)


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def load():
    doc = json.loads((ROOT / "tests/golden/report.json").read_text())
    cat = {c["id"]: c for c in doc["check_catalogue"]}
    findings = doc["findings"]
    by_check = collections.Counter(f["check_id"] for f in findings)
    by_domain = collections.Counter(cat[f["check_id"]]["domain"] for f in findings)
    by_sev = collections.Counter(f["severity"] for f in findings)
    by_sub = collections.Counter()
    for f in findings:
        parts = f["resource_id"].split("/")
        by_sub[parts[2] if len(parts) > 2 and parts[1] == "subscriptions" else "(tenant)"] += 1
    return doc, cat, findings, by_check, by_domain, by_sev, by_sub


def head(title: str, brand: str, extra_css: str = "") -> str:
    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(title)}</title><style>{CSS_TOKENS}{BASE_CSS}{extra_css}</style></head>"
        f"<body><!-- BRAND: edit the variables below to try other branding -->"
        f"<style>{brand}</style>"
    )


def hbar_chart(rows, title, unit="findings"):
    """Single-series horizontal bars, direct labels, hover tips, table view toggle."""
    mx = max(v for _, v in rows) or 1
    bars = "".join(
        f'<tr><td style="width:34%">{esc(k)}</td><td><div class="bar" tabindex="0" '
        f'data-tip="{esc(k)}: {v} {unit}" style="width:{max(2, 100 * v / mx):.1f}%"></div></td>'
        f'<td class="num" style="width:56px">{v}</td></tr>'
        for k, v in rows
    )
    return (
        f'<div class="panel"><div style="display:flex;justify-content:space-between">'
        f"<strong>{esc(title)}</strong></div>"
        f'<table aria-label="{esc(title)}"><tbody>{bars}</tbody></table></div>'
    )


# ---------------------------------------------------------------- A: brief
def mock_brief(ctx) -> str:
    doc, cat, findings, by_check, by_domain, by_sev, by_sub = ctx
    n = len(findings)
    big = by_check.most_common(1)[0]
    brand = ":root{--seq:#2a78d6;--accent:#184f95}.brandbar{border-left:6px solid var(--accent);padding-left:12px}"
    rows = [(DOMAIN_NAMES.get(k, k), v) for k, v in by_domain.most_common()]
    top = "".join(
        f"<tr><td>{esc(cat[c]['title'])}</td><td class='num'>{v}</td>"
        f"<td class='hide-sm'><span class='pill'>{esc(cat[c]['confidence'])} confidence</span></td></tr>"
        for c, v in by_check.most_common(5)
    )
    return (
        head("F-CAT brief mock-up", brand)
        + f"""<div class="wrap">{BANNER}
<div class="brandbar"><h1>Azure cost hygiene: where to look first</h1>
<p class="sub">Prepared for [Customer name] by [Your company]. Scope: {doc["manifest"]["scope"]["subscriptions"]} subscriptions, {doc["manifest"]["scope"]["management_groups"]} management groups.</p></div>
<div class="panel"><p style="font-size:20px;margin:0">We found <strong>{n} things worth reviewing</strong> across {len(by_check)} types of waste or misconfiguration.
Most ({big[1]}) are {esc(cat[big[0]]["title"].lower())}.</p>
<p class="muted" style="margin:8px 0 0">Money is not shown yet. Cost data is not part of this run, so we do not guess at savings.</p></div>
<h2>Where the findings are</h2>
{hbar_chart(rows, "Findings by area")}
<h2>The five biggest groups</h2>
<div class="panel"><table><thead><tr><th>What</th><th class="num">Count</th><th class="hide-sm">How sure we are</th></tr></thead><tbody>{top}</tbody></table></div>
<h2>What this report cannot tell you yet</h2>
<div class="panel"><ul style="margin:0;padding-left:20px">
<li>How much each item costs. Cost Management data is needed for that.</li>
<li>FinOps maturity. 22 capabilities are listed in the maturity view; none is scored without evidence.</li>
<li>Whether the checks are right for your estate. They have not been run on a live tenant.</li></ul></div>
<h2>Report integrity</h2>
<p>Self-audit: <strong style="color:var(--ok)">&#10003; passed</strong> ({len(doc["audit"]["invariants"])} invariants). {len(doc["manifest"]["checks"])} checks ran, none skipped.</p>
</div><script>{TT_JS}</script></body></html>"""
    )


# -------------------------------------------------------------- B: ledger
def mock_ledger(ctx) -> str:
    doc, cat, findings, by_check, by_domain, by_sev, by_sub = ctx
    brand = ":root{--seq:#1c5cab}"
    extra = ".f{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}tr.row{cursor:pointer}tr.row:hover{background:var(--grid)}.mono{overflow-wrap:anywhere}td.nw,.pill{white-space:nowrap}td.mono{font-family:ui-monospace,Consolas,monospace;font-size:12px;word-break:break-all}"
    subs = sorted(by_sub)
    doms = sorted(DOMAIN_NAMES)
    cr = []
    for cid, v in sorted(by_check.items(), key=lambda kv: (-kv[1], kv[0])):
        c = cat[cid]
        fs = [f for f in findings if f["check_id"] == cid]
        sev = sorted({f["severity"] for f in fs}, key=SEV_ORDER.index)
        det = "".join(
            f"<div class='mono' style='padding:2px 0'>{esc(f['resource_id'])}<br><span class='muted'>{esc(f['message'])}</span></div>"
            for f in fs[:5]
        )
        more = f"<div class='muted'>and {len(fs) - 5} more</div>" if len(fs) > 5 else ""
        cr.append(
            f"<tr class='row' data-domain='{esc(c['domain'])}' data-sev='{esc(' '.join(sev))}' data-text='{esc((cid + ' ' + c['title']).lower())}'>"
            f"<td><details><summary><strong>{esc(cid)}</strong> {esc(c['title'])}</summary>"
            f"<p class='muted'>{esc(c['framework'])}. Needs {esc(', '.join(c['permissions']))}. Savings basis: {esc(c['savings_basis'])}.</p>{det}{more}</details></td>"
            f"<td>{esc(DOMAIN_NAMES.get(c['domain'], c['domain']))}</td>"
            f"<td class='nw'>{esc(', '.join(sev))}</td><td class='num'>{v}</td>"
            f"<td class='hide-sm'><span class='pill'>{esc(c['validation'])}</span></td></tr>"
        )
    sub_rows = "".join(f"<tr><td>{esc(s)}</td><td class='num'>{by_sub[s]}</td></tr>" for s in subs)
    dopt = "".join(f"<option value='{d}'>{esc(DOMAIN_NAMES[d])}</option>" for d in doms)
    return (
        head("F-CAT ledger mock-up", brand, extra)
        + f"""<div class="wrap">{BANNER}
<h1>Assessment ledger</h1><p class="sub">{len(findings)} findings, {len(by_check)} checks, {len(subs)} scopes. One row per check; open a row for resources.</p>
<div class="f"><input id="q" type="search" placeholder="Filter by check or title" aria-label="Filter by text">
<select id="d" aria-label="Domain"><option value="">All domains</option>{dopt}</select>
<select id="s" aria-label="Severity"><option value="">All severities</option>{"".join(f"<option>{x}</option>" for x in SEV_ORDER)}</select>
<button id="th" type="button">Toggle dark</button></div>
<div class="panel"><table id="t"><thead><tr><th>Check</th><th>Domain</th><th>Severity</th><th class="num">Findings</th><th class="hide-sm">Validation</th></tr></thead><tbody>{"".join(cr)}</tbody></table>
<p id="none" class="muted" style="display:none">No checks match. Clear a filter.</p></div>
<h2>Findings per scope</h2><div class="panel"><table><thead><tr><th>Scope</th><th class="num">Findings</th></tr></thead><tbody>{sub_rows}</tbody></table></div>
<h2>Audit</h2><p>&#10003; All {len(doc["audit"]["invariants"])} self-audit invariants passed.</p>
</div><script>{TT_JS}
const q=document.getElementById('q'),d=document.getElementById('d'),s=document.getElementById('s');
function f(){{let n=0;document.querySelectorAll('#t tbody tr').forEach(r=>{{
const ok=(!q.value||r.dataset.text.includes(q.value.toLowerCase()))&&(!d.value||r.dataset.domain===d.value)&&(!s.value||r.dataset.sev.split(' ').includes(s.value));
r.style.display=ok?'':'none';if(ok)n++}});document.getElementById('none').style.display=n?'none':'block'}}
[q,d,s].forEach(e=>e.addEventListener('input',f));
document.getElementById('th').onclick=()=>{{const r=document.documentElement;
r.dataset.theme=(r.dataset.theme==='dark')?'light':'dark'}};</script></body></html>"""
    )


# ------------------------------------------------------------ C: maturity
def mock_maturity(ctx) -> str:
    doc, cat, findings, by_check, by_domain, by_sev, by_sub = ctx
    brand = ":root{--seq:#3987e5}"
    extra = ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:8px}.cap{padding:10px 12px;border-radius:8px;box-shadow:0 0 0 1px var(--ring);background:var(--surface)}.cap b{display:block}.k{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;box-shadow:inset 0 0 0 2px var(--axis)}.k.partial{background:var(--c1);box-shadow:none}.k.cost{background:repeating-linear-gradient(45deg,var(--axis) 0 2px,transparent 2px 4px)}.k.customer{background:transparent}.k.unbuilt{background:var(--axis)}"
    legend = (
        "<span><i class='k partial'></i>Partial evidence</span> "
        "<span><i class='k cost'></i>Needs cost data</span> "
        "<span><i class='k unbuilt'></i>Check not built yet</span> "
        "<span><i class='k customer'></i>Needs customer input</span>"
    )
    caps = "".join(
        f"<div class='cap' tabindex='0' data-tip='{esc(CAP_TEXT[kind])}'><b>{i}. {esc(name)}</b>"
        f"<span class='muted' style='font-size:13px'><i class='k {kind}'></i>{esc(CAP_TEXT[kind].split(':')[0])}</span></div>"
        for i, (name, kind) in enumerate(CAPABILITIES, 1)
    )
    cnt = collections.Counter(k for _, k in CAPABILITIES)
    usage = by_domain
    return (
        head("F-CAT maturity mock-up", brand, extra)
        + f"""<div class="wrap" data-view="maturity">{BANNER}
<h1>FinOps maturity</h1>
<p class="sub">No score is shown. A capability is scored only from technical evidence plus answers from your team. Today: {cnt["partial"]} have partial evidence, {cnt["cost"]} wait for cost data, {cnt["unbuilt"]} need a check we have not built, {cnt["customer"]} wait for your input.</p>
<div style="display:flex;gap:16px;flex-wrap:wrap;margin:0 0 12px;color:var(--ink2)">{legend}</div>
<div class="grid">{caps}</div>
<h2>Evidence behind "Usage Optimization"</h2>
{hbar_chart([(DOMAIN_NAMES.get(k, k), v) for k, v in usage.most_common()], "Resource-check findings by area")}
<p class="muted">Counts show what the checks found, not how mature the practice is. Names follow the FinOps Foundation capability list.</p>
<h2>Next</h2><p>Answer the leadership questions (Part 2) to unlock the {cnt["customer"]} input-only capabilities. Grant Cost Management Reader to unlock {cnt["cost"]} more.</p>
<p><button id="th" type="button">Toggle dark</button></p>
</div><script>{TT_JS}
document.getElementById('th').onclick=()=>{{const r=document.documentElement;
r.dataset.theme=(r.dataset.theme==='dark')?'light':'dark'}};</script></body></html>"""
    )


def main() -> None:
    ctx = load()
    OUT.mkdir(parents=True, exist_ok=True)
    pages = {
        "A-brief.html": mock_brief,
        "B-ledger.html": mock_ledger,
        "C-maturity.html": mock_maturity,
    }
    for name, fn in pages.items():
        (OUT / name).write_text(fn(ctx), encoding="utf-8")
        print("wrote", OUT / name)


if __name__ == "__main__":
    main()
