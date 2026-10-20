"""Third round of front-end mock-ups (variant A refined, 2026-10-20): the dashboard rebuilt on the REAL output of the tool for the synthetic estate
(tests/golden/report.json, 121 findings, includes the new tag, policy, budget, anomaly and export checks), plus two things the tool cannot show yet:
 - a governance posture matrix (Evidenced / Partial / Not evidenced / Not assessed per subscription). The tool emits findings only today; posture
   needs each check to also record what it saw working ("passes"). Here the posture is derived in this script from the synthetic snapshot with the
   rules written in docs/COST-GOVERNANCE.md section 12, and the rules are shown in the page. It is a DESIGN, not tool output.
 - a tag hygiene panel built from the real TAG-* findings. Tag values are customer data, so the page has a mask switch (the real tool's --redact).
Output: docs/mockups/frontend3/*.html. Self-contained, system fonts, no network."""

from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "mockups" / "frontend3"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v2 = _load("v2", ROOT / "scripts" / "make_frontend_v2.py")
ms = _load("ms", ROOT / "scripts" / "make_synthetic.py")
GOVERNANCE_CHECKS = ("TAG-", "POL-", "BUD-", "ALR-", "EXP-")

ROWS = [
    # key, label, checks, needs the opt-in REST collectors
    ("alloc", "Allocation (tags)", ["TAG-DISC-01", "TAG-COV-01", "TAG-CASE-01", "TAG-VAL-01", "TAG-RG-01"], False),
    ("policy", "Policy and governance (tag policy)", ["POL-TAG-01", "POL-TAGMOD-01", "POL-COMPL-01"], False),
    ("budget", "Budgeting", ["BUD-COVER-01", "BUD-ALERT-01", "BUD-EXP-01"], True),
    ("fcst", "Forecasting", ["BUD-FCST-01"], True),
    ("anom", "Anomaly management", ["ALR-ANOM-01"], True),
    ("ingest", "Data ingestion (cost exports)", ["EXP-CFG-01"], True),
]


def posture(est, findings):
    """Per-subscription state for each row. Rules are proposals, echoed in the page."""
    subs = sorted(f"sub-synth-{i}" for i in (1, 2, 3))
    tags = est["tag_inventory"]
    sch_keys = ["env"]  # discovered from the policy assignment in the synthetic estate (TAG-DISC-01)
    variants_touch = {r["subscriptionId"] for r in tags if any(k != k.lower() for k in (r.get("tags") or {}))}
    out: dict = {k: {} for k, *_ in ROWS}
    for s in subs:
        rs = [r for r in tags if r["subscriptionId"] == s]
        have = sum(1 for r in rs if all(k in {x.lower() for x in (r.get("tags") or {})} for k in sch_keys))
        pct = 100 * have / len(rs)
        small = len(rs) < 10
        if pct < 25:
            st, why = "n", f"Only {have} of {len(rs)} resources carry the scheme tag env ({pct:.0f}%)"
        elif pct >= 75 and s not in variants_touch:
            st, why = "e", f"{have} of {len(rs)} resources carry env" + (" (small sample, under 10 resources)" if small else "")
        else:
            st, why = "p", f"{have} of {len(rs)} resources carry env ({pct:.0f}%), but tag names or values are written inconsistently"
        out["alloc"][s] = {"s": st, "why": why}
        pol = [a for a in est["policy_assignments"] if a["scope"].endswith(s)]
        if not pol:
            out["policy"][s] = {
                "s": "n",
                "why": "No tag policy assigned at this scope (management group assignments would be counted here)",
            }
        else:
            out["policy"][s] = {
                "s": "p",
                "why": "Require-tag policy is enforced, but 15 of 34 evaluated resources are non-compliant (44%) and no policy adds or inherits tags",
            }
        bs = [b for b in est["budgets"] if b["subscriptionId"] == s]
        if not bs:
            out["budget"][s] = {"s": "n", "why": "No budget visible at subscription scope"}
            out["fcst"][s] = {"s": "n", "why": "No budget, so no forecast alert"}
        else:
            bad = [
                b["name"]
                for b in bs
                if (b["endDate"] and b["endDate"] < "2026-10-01") or not any(n["enabled"] and n["hasEmail"] for n in b["notifications"])
            ]
            out["budget"][s] = (
                {"s": "p", "why": f"{len(bs)} budgets; {', '.join(bad)} ended or cannot alert anyone"}
                if bad
                else {"s": "e", "why": f"{len(bs)} budget with a working alert"}
            )
            f_ok = any(n["enabled"] and n["thresholdType"] == "Forecasted" for b in bs for n in b["notifications"])
            out["fcst"][s] = (
                {"s": "e", "why": "An enabled forecast alert exists"} if f_ok else {"s": "n", "why": "Budgets alert on actual spend only"}
            )
        rl = [r for r in est["anomaly_rules"] if r["subscriptionId"] == s]
        if any(r["status"] == "Enabled" for r in rl):
            out["anom"][s] = {"s": "e", "why": "An enabled anomaly alert rule is visible"}
        elif rl:
            out["anom"][s] = {"s": "p", "why": "An anomaly alert rule exists but is Disabled"}
        else:
            out["anom"][s] = {"s": "n", "why": "No anomaly alert rule visible to this identity (private rules cannot be seen)"}
        ex = [e for e in est["cost_exports"] if e["subscriptionId"] == s]
        if not ex:
            out["ingest"][s] = {"s": "n", "why": "No cost export visible at subscription scope"}
        else:
            bad = [
                e["name"]
                for e in ex
                if e["scheduleStatus"] == "Inactive" or e["lastRunStatus"] in ("Failed", "Timeout", "DataNotAvailable")
            ]
            out["ingest"][s] = (
                {"s": "p", "why": f"Export {bad[0]} exists but its last run failed"}
                if bad
                else {"s": "e", "why": "Export runs on schedule"}
            )
    # hand-derived expectation (docs/COST-GOVERNANCE.md section 12); generation stops if the rules and the findings ever disagree
    want = {"alloc": "pne", "policy": "pnn", "budget": "pen", "fcst": "enn", "anom": "enp", "ingest": "pnn"}
    got = {k: "".join(out[k][s]["s"] for s in subs) for k in out}
    assert got == want, got
    return {"subs": subs, "rows": [{"key": k, "label": lb, "checks": ck, "rest": rest, "cells": out[k]} for k, lb, ck, rest in ROWS]}


def tag_subs(est):
    res: dict = {}
    for r in est["tag_inventory"]:
        s = res.setdefault(r["subscriptionId"], {"total": 0, "keys": Counter()})
        s["total"] += 1
        for k in {x.lower() for x in (r.get("tags") or {})}:
            s["keys"][k] += 1
    return {s: {"total": v["total"], "keys": dict(v["keys"])} for s, v in res.items()}


def build():
    d = v2.build()
    est = ms.estate()
    gold = json.loads((ROOT / "tests" / "golden" / "report.json").read_text())
    det = {(f["check_id"], f["fingerprint"][:8]): f["details"] for f in gold["findings"] if f["check_id"].startswith(GOVERNANCE_CHECKS)}
    for c in d["checks"]:
        if c["id"].startswith(GOVERNANCE_CHECKS):
            for f in c["findings"]:
                f["d"] = det.get((c["id"], f["fp"]))
                f["tags"] = None
    d["domains"] = {**d["domains"], "governance": "Cost governance"}
    d["help"] = {
        **d["help"],
        "governance": "These show how cost is controlled, not waste. Ask who owns the control before judging it; F-CAT only sees what this identity can read.",
    }
    d["posture"] = posture(est, gold["findings"])
    d["tagSubs"] = tag_subs(est)
    d["gov"] = {"restOn": True}
    return d


CSS3 = r"""
.st{display:inline-flex;gap:6px;align-items:center;font-size:12px;white-space:nowrap}.st i{width:12px;height:12px;display:inline-block;border-radius:50%;flex:none}
.st.e i{background:var(--ok)}.st.p i{border:2px solid var(--warn);background:linear-gradient(90deg,var(--warn) 50%,transparent 50%)}.st.n i{border:2px solid var(--ink2)}
.st.a i{border-radius:2px;border:1px solid var(--warn);background:repeating-linear-gradient(45deg,transparent 0 3px,var(--warn) 3px 5px)}
table.pm{table-layout:fixed;min-width:620px}.pmw{overflow-x:auto;max-width:100%}table.pm th,table.pm td{padding:6px 8px}table.pm th:first-child{width:30%}
button.cell{width:100%;text-align:left;border:1px solid transparent;background:none;padding:4px 6px}button.cell:hover,button.cell[aria-pressed=true]{border-color:var(--acc);background:var(--accbg)}
.sw{display:flex;gap:14px;flex-wrap:wrap;align-items:center}.sw label{display:flex;gap:6px;align-items:center;cursor:pointer}
.seg{display:inline-flex}.seg button{border-radius:0}.seg button:first-child{border-radius:6px 0 0 6px}.seg button:last-child{border-radius:0 6px 6px 0}
.kv{display:grid;grid-template-columns:minmax(80px,120px) 1fr;gap:4px 10px;margin:0}.kv dt{color:var(--muted);font-size:12px}.kv dd{margin:0}
.src{display:inline-block;border-left:4px solid var(--acc);padding:2px 8px;background:var(--accbg);border-radius:0 4px 4px 0}
.var{display:inline-flex;gap:4px;margin:2px 6px 2px 0;border:1px solid var(--line);border-radius:4px;padding:0 6px;font:12px ui-monospace,Menlo,monospace}.var em{font-style:normal;color:var(--muted)}
.covrow{display:grid;grid-template-columns:minmax(70px,110px) 1fr 54px;gap:8px;align-items:center;padding:2px 0}
.covrow .bar{height:10px}.covrow.low i{background:var(--warn)}
.legend{display:flex;gap:14px;flex-wrap:wrap;color:var(--ink2);font-size:12px;margin:8px 0 0}
details.rules{margin-top:8px;color:var(--ink2);font-size:12px}details.rules summary{cursor:pointer}
@media print{.sw,.seg{display:none!important}table.pm{min-width:0}.pmw{overflow:visible}#govsec .row2{grid-template-columns:minmax(0,1fr)}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""

JS3 = r"""
const STL={e:'Evidenced',p:'Partial',n:'Not evidenced',a:'Not assessed'};
st.govOff=false;st.mask=false;st.cell=null;st.view=store.get('view','all');
const maskVal=v=>{let x=2166136261;for(const c of String(v)){x^=c.charCodeAt(0);x=Math.imul(x,16777619)}return 'val-'+(x>>>0).toString(16).padStart(8,'0')};
const shown=v=>st.mask?maskVal(v):v;
const stat=(s,t)=>h('span',{class:'st '+s},h('i'),t||STL[s]);
function cellOf(row,sub){
 if(st.govOff&&row.rest)return {s:'a',why:'Not assessed, because [run] governance_apis is off, so budgets, anomaly rules and exports were not read'};
 return row.cells[sub]}
function tenantOf(row){
 const cs=D.posture.subs.map(s=>cellOf(row,s));if(cs.every(c=>c.s==='a'))return {s:'a',why:cs[0].why};
 const r=cs.filter(c=>c.s!=='a'),e=r.filter(c=>c.s==='e').length;
 return {s:e===r.length?'e':r.every(c=>c.s==='n')?'n':'p',why:e+' of '+r.length+' subscriptions evidenced'}}
function postureMatrix(){
 const P=D.posture,subs=P.subs;
 const sel=st.cell?P.rows.find(r=>r.key===st.cell.row):null;
 const selC=sel?(st.cell.sub==='_t'?tenantOf(sel):cellOf(sel,st.cell.sub)):null;
 return [
  h('div',{class:'sw noprint'},h('label',0,h('input',{type:'checkbox',checked:st.govOff,onchange:e=>{st.govOff=e.target.checked;draw()}}),'Preview: budget, anomaly and export collectors switched off')),
  h('div',{class:'pmw'},h('table',{class:'pm'},h('thead',0,h('tr',0,h('th',0,'Capability'),h('th',0,'Whole tenant'),...subs.map(s=>h('th',0,s.replace('sub-synth-','Subscription '))))),
   h('tbody',0,...P.rows.map(r=>h('tr',0,h('td',0,r.label,h('div',{class:'id'},r.checks.join(' '))),
    ...[['_t',tenantOf(r)],...subs.map(s=>[s,cellOf(r,s)])].map(([k,c])=>h('td',0,h('button',{class:'cell','aria-pressed':!!st.cell&&st.cell.row===r.key&&st.cell.sub===k,title:c.why,onclick:()=>{st.cell={row:r.key,sub:k};draw()}},stat(c.s)))))))) ),
  h('div',{class:'legend'},stat('e'),stat('p'),stat('n'),stat('a'),h('span',0,'Never a score. Not assessed means we could not look; Not evidenced means we looked and did not find it.')),
  selC?h('div',{class:'note',style:'border-left:3px solid var(--acc)'},h('b',0,sel.label+' / '+(st.cell.sub==='_t'?'whole tenant':st.cell.sub)+': '),stat(selC.s),h('div',0,selC.why),
    h('div',{class:'mini',style:'margin-top:4px'},'Based on: ',...sel.checks.map(id=>h('a',{href:'#',style:'margin-right:8px',onclick:e=>{e.preventDefault();st.sel=id;st.view==='gov'&&(st.view='all');draw();$('#drawer')&&$('#drawer').scrollIntoView({block:'nearest'})}},id)))):h('div',{class:'mini',style:'margin-top:6px'},'Click a cell for the reason and the checks behind it.'),
  h('details',{class:'rules'},h('summary',0,'How each state is decided (proposal, change it if you disagree)'),h('ul',{style:'margin:6px 0 0;padding-left:18px'},
   h('li',0,'Allocation: Evidenced when the discovered scheme tags are on at least 75% of resources and no casing or value variants touch the scope; Not evidenced under 25%; otherwise Partial.'),
   h('li',0,'Policy: Evidenced needs an enforced tag policy at the scope with few non-compliant resources; an enforced policy with gaps is Partial; none is Not evidenced.'),
   h('li',0,'Budgeting: a working budget with a recipient is Evidenced; an ended or silent budget makes it Partial; none is Not evidenced.'),
   h('li',0,'Forecasting, anomaly management and data ingestion follow the same idea: working = Evidenced, present but broken or disabled = Partial, not visible = Not evidenced.'),
   h('li',0,'Whole tenant: Evidenced only when every readable subscription is. This needs checks to record what they saw working, not only what is wrong. That is not built yet.')))]}
function tagHygiene(){
 const F=id=>(D.checks.find(c=>c.id===id)||{findings:[]}).findings;
 const disc=F('TAG-DISC-01')[0],dd=disc&&disc.d;
 if(!dd)return h('p',{class:'mini'},'Tag discovery not assessed.');
 const srcL={policy:'Declared by your tag policy',inferred:'Inferred from what most resources already use',none:'No scheme evident'}[dd.scheme_source];
 const keys=Object.entries(dd.top_keys);
 const subsT=Object.entries(D.tagSubs);
 return [
  h('dl',{class:'kv'},h('dt',0,'Standard found'),h('dd',0,h('span',{class:'src'},srcL),' ',...dd.scheme_keys.map(k=>h('span',{class:'tag'},k))),
   h('dt',0,'How we know'),h('dd',{class:'mini'},dd.scheme_source==='policy'?'A tag policy names these tags. Nothing is judged against a list built into F-CAT.':dd.inference_rule),
   h('dt',0,'Coverage'),h('dd',0,dd.resources_with_any_tag+' of '+dd.resources+' resources carry at least one tag; '+dd.distinct_keys+' distinct tag names.')),
  h('h2',0,'TAG NAMES IN USE'),
  ...keys.map(([k,v])=>h('div',{class:'covrow'},h('span',{class:'rn'},k),h('div',{class:'bar'},h('i',{style:'width:'+v.percent+'%'})),h('em',{style:'font-style:normal;text-align:right'},v.percent+'%'))),
  h('h2',0,'COVERAGE OF THE STANDARD BY SUBSCRIPTION'),
  ...subsT.map(([s,v])=>{const have=v.keys[dd.scheme_keys[0]]||0,p=Math.round(100*have/v.total);return h('div',{class:'covrow'+(p<75&&v.total>=10?' low':'')},h('span',{class:'rn'},s.replace('sub-synth-','Sub ')),h('div',{class:'bar'},h('i',{style:'width:'+p+'%'})),h('em',{style:'font-style:normal;text-align:right'},p+'%'))}),
  h('div',{class:'mini'},'Share of resources carrying '+dd.scheme_keys[0]+'. Subscriptions with fewer than 10 resources are shown but not judged.'),
  h('h2',0,'INCONSISTENT SPELLING (MAY SPLIT COST REPORTS)'),
  ...F('TAG-CASE-01').map(f=>h('div',0,h('span',{class:'tag'},'name'),' ',...Object.entries(f.d.casings).map(([k,n])=>h('span',{class:'var'},k,h('em',0,n))),h('span',{class:'mini'},' on '+f.d.resources+' resources'))),
  ...F('TAG-VAL-01').map(f=>h('div',{style:'margin-top:4px'},h('span',{class:'tag'},'values of '+f.name.replace('tag:','')),' ',...f.d.variants.flatMap(g=>g.map(x=>h('span',{class:'var'},shown(x.value),h('em',0,x.count)))))),
  h('div',{class:'mini'},'Names are case-insensitive to Azure but the casing shows in cost reports; values are case-sensitive and appear as separate rows. Whether Cost Management merges them is not verified.'),
  ...(F('TAG-RG-01').length?[h('h2',0,'RESOURCE GROUP TAGS NOT CARRIED BY THEIR RESOURCES'),...F('TAG-RG-01').map(f=>h('div',{style:'padding:2px 0'},h('span',{class:'rn'},f.sub.replace('sub-synth-','Sub ')+' / '+f.name),h('div',{class:'mini'},f.msg)))]:[]),
  h('div',{class:'note'},'Azure does not copy resource group tags to resources. Cost Management has an optional inheritance setting that F-CAT cannot read yet, so whether it is on is not assessed.')]}
function govControls(){
 return h('div',{class:'sw noprint'},h('label',0,h('input',{type:'checkbox',checked:st.mask,onchange:e=>{st.mask=e.target.checked;draw()}}),'Mask tag values (what --redact does)'),h('span',{class:'mini'},'Tag values are stored in the snapshot and can contain names. Mask them before sharing a screenshot.'))}
function govSection(big){
 return h('section',{class:'wrap',style:'padding-bottom:0'},
  h('div',{class:'row2',style:big?'grid-template-columns:minmax(0,3fr) minmax(0,2fr)':''},
   h('div',{class:'pane'},h('h2',0,'COST GOVERNANCE: WHAT CONTROLS EXIST'),mount(h('div'),postureMatrix)),
   h('div',{class:'pane'},h('h2',0,'TAG HYGIENE'),govControls(),mount(h('div'),tagHygiene))))}
function viewSwitch(){return h('div',{class:'seg noprint',role:'group','aria-label':'View'},...[['all','Everything'],['find','Findings'],['gov','Governance and tags']].map(([k,l])=>h('button',{'aria-pressed':st.view===k,onclick:()=>{st.view=k;store.set('view',k);applyView();$$('button',$('.seg')).forEach((b,i)=>b.setAttribute('aria-pressed',['all','find','gov'][i]===k))}},l)))}
function applyView(){const g=$('#govsec'),m=$('#mainsec'),s=$('#sumsec');if(!g)return;g.classList.toggle('hide',st.view==='find');m.classList.toggle('hide',st.view==='gov');s.classList.toggle('hide',st.view==='gov')}
"""

A3 = r"""
const app=$('#app');app.append(topBar(viewSwitch()),printHead('Azure FinOps assessment'));
const sum=h('section',{class:'wrap',id:'sumsec',style:'padding-bottom:0'});
sum.append(mount(h('div'),()=>[h('p',{class:'headline'},headlineText())]),mount(h('div'),kpis),
 h('div',{class:'row2'},h('div',{class:'pane'},h('h2',0,'WHERE IT CONCENTRATES (click to filter)'),mount(h('div'),areaBars),h('h2',0,'SEVERITY'),mount(h('div'),sevBar)),
  h('div',{class:'pane'},h('h2',0,'MAP OF SUBSCRIPTIONS AND AREAS'),mount(h('div'),()=>treemap(260))),
  h('div',{class:'pane'},h('h2',0,'DID EVERY CHECK RUN?'),mount(h('div'),coverageStrip))));
const gov=govSection(false);gov.id='govsec';
const main=h('main',{class:'wrap',id:'mainsec'});const g=h('div',{class:'grid3'});
g.append(mount(h('aside',{class:'pane side'}),sideFilters),mount(h('section',{class:'pane'}),queue),mount(h('aside',{class:'pane',id:'drawer'}),()=>drawer()));main.append(g);
app.append(sum,gov,main);applyView();draw();
"""

PAGE_NOTE = "Synthetic estate. Findings are the real output of the tool's checks on it; the posture states are a design that the tool does not produce yet."


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.dumps(build(), separators=(",", ":")).replace("</", "<\\/")
    page = v2.PAGE.format(css=v2.CSS + CSS3, js=v2.JS + JS3, body=A3).replace("/*DATA*/", data)
    page = page.replace("fcat2:", "fcat3:")
    # findings that belong to no subscription (tag scheme, tag policy, exports estate) get the sub id "-": show them as tenant-wide
    page = page.replace(
        "label=s.replace('sub-synth-','Subscription ')",
        "label=s==='-'?'Tenant-wide (no single subscription)':s.replace('sub-synth-','Subscription ')",
    )
    page = page.replace("[s,s,subN(s)]", "[s,s==='-'?'Tenant-wide':s,subN(s)]")
    (OUT / "A3-dashboard.html").write_text(page)
    (OUT / "index.html").write_text(
        "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>F-CAT front-end round 3</title>"
        "<body style='font:16px/1.5 system-ui;max-width:720px;margin:24px auto;padding:0 16px'><h1>Front-end round 3</h1>"
        "<p><a href=A3-dashboard.html>A3: variant A with cost governance posture and tag hygiene</a>. Use the switch top right to show everything, only findings, or only governance and tags.</p>"
        f"<p>{PAGE_NOTE}</p></body>"
    )
    print("wrote", OUT)


if __name__ == "__main__":
    main()
