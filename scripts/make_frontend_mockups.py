"""Generate three early front-end design variations from tests/golden/report.json (synthetic data only, no cost figures).
Output: docs/mockups/frontend/*.html. Self-contained, system fonts, no network. Mock-ups only: nothing here is a verified result."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "mockups" / "frontend"
spec = importlib.util.spec_from_file_location("mm", ROOT / "scripts" / "make_mockups.py")
mm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mm)

DOMAIN_HELP = {
    "orphaned": "Confirm nothing depends on it before removing. F-CAT never deletes anything.",
    "modernization": "Check the retirement date applies to your workload, then plan the move.",
    "licensing": "F-CAT cannot see your licence agreements. Someone who knows them must confirm eligibility.",
    "optimization": "A prompt to ask the workload owner, not an instruction.",
    "advisor": "Microsoft's own recommendation, passed through. We have not verified its saving figure.",
    "monitoring": "Review whether the retention or cap matches what the team needs.",
    "security": "Review whether the plan is needed in this environment.",
    "billing": "Affects how much cost data F-CAT can read for this subscription.",
}


def build_data():
    doc = json.loads((ROOT / "tests" / "golden" / "report.json").read_text())
    cat = {c["id"]: c for c in doc["check_catalogue"]}
    status = {s["id"]: s for s in doc["manifest"]["checks"]}
    by = {}
    for f in doc["findings"]:
        m = re.search(r"/subscriptions/([^/]+)", f["resource_id"], re.I)
        by.setdefault(f["check_id"], []).append(
            {
                "sub": m.group(1).lower() if m else "-",
                "name": f["resource_id"].rstrip("/").rsplit("/", 1)[-1],
                "sev": f["severity"],
                "msg": f["message"],
                "fp": f["fingerprint"][:8],
            }
        )
    checks = []
    for cid, c in cat.items():
        s = status.get(cid, {})
        fl = by.get(cid, [])
        checks.append(
            {
                "id": cid, "title": c["title"], "domain": c["domain"], "framework": c["framework"], "conf": c["confidence"],
                "valid": c["validation"], "status": s.get("status", "?"),
                "reason": s.get("reason", ""), "findings": fl, "logic": (doc["findings"] and next((f["evidence"]["logic_hash"] for f in doc["findings"] if f["check_id"] == cid), "")),
            }
        )  # fmt: skip
    subs = sorted({f["sub"] for c in checks for f in c["findings"]})
    caps = [{"name": n, "kind": k, "text": mm.CAP_TEXT[k]} for n, k in mm.CAPABILITIES]
    return {
        "checks": checks, "subs": subs, "caps": caps, "domains": mm.DOMAIN_NAMES, "help": DOMAIN_HELP,
        "audit": {"status": doc["audit"]["status"], "invariants": len(doc["audit"]["invariants"]) if isinstance(doc["audit"]["invariants"], (list, dict)) else doc["audit"]["invariants"]},
        "scope": doc["manifest"]["scope"],
    }  # fmt: skip


COMMON_JS = r"""
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
function h(t,a,...k){const e=document.createElement(t);for(const[x,v]of Object.entries(a||{})){if(x==='class')e.className=v;else if(x.startsWith('on'))e.addEventListener(x.slice(2),v);else if(v!==false&&v!=null)e.setAttribute(x,v===true?'':v)}for(const c of k.flat())if(c!=null)e.append(c.nodeType?c:document.createTextNode(c));return e}
const SEV={high:3,medium:2,low:1,info:0};
const dn=d=>D.domains[d]||d;
const ran=D.checks.filter(c=>c.status==='ran'), na=D.checks.filter(c=>c.status!=='ran');
const total=D.checks.reduce((a,c)=>a+c.findings.length,0);
"""

# ---------------------------------------------------------------- 1. Workbench
WORKBENCH = (
    r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>F-CAT workbench</title><style>
:root{--bg:#e9eef4;--pane:#f7f9fb;--ink:#13233a;--ink2:#46556b;--muted:#66758a;--line:#d3dce7;--acc:#1f5fbf;--accbg:#dce8fa;--ok:#0b6b2e;--warn:#8a5700;--bad:#a12626;--r:6px}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0e141c;--pane:#16202c;--ink:#e6edf6;--ink2:#b3c0d1;--muted:#8e9db1;--line:#2a3a4d;--acc:#6fa3f0;--accbg:#1e3350;--ok:#4cc27a;--warn:#f2b84b;--bad:#f08a8a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
header{display:flex;gap:16px;align-items:center;flex-wrap:wrap;padding:10px 16px;background:var(--pane);border-bottom:1px solid var(--line)}
.logo{font-weight:700;letter-spacing:.02em}.logo b{color:var(--acc)}
.chip{border:1px solid var(--line);border-radius:99px;padding:2px 10px;color:var(--ink2);font-size:12px}
.chip.ok{color:var(--ok);border-color:currentColor}.chip.mock{border-style:dashed}
main{display:grid;grid-template-columns:230px minmax(0,1fr) 340px;gap:12px;padding:12px;align-items:start}
.pane{background:var(--pane);border:1px solid var(--line);border-radius:var(--r);padding:12px}
h2{font-size:12px;margin:14px 0 6px;color:var(--muted);font-weight:600;letter-spacing:.04em}h2:first-child{margin-top:0}
label{display:flex;gap:8px;align-items:center;padding:3px 0;cursor:pointer}label span.n{margin-left:auto;color:var(--muted);font-variant-numeric:tabular-nums}
table{border-collapse:collapse;width:100%}th{white-space:nowrap;font-size:12px;color:var(--muted);text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--pane)}
td{padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}tr.row{cursor:pointer}tr.row:hover td{background:var(--accbg)}tr.row[aria-selected=true] td{background:var(--accbg);box-shadow:inset 3px 0 0 var(--acc)}
td.num{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}.id{font:12px ui-monospace,Menlo,Consolas,monospace;color:var(--muted)}
.sev{display:inline-flex;gap:5px;align-items:center;font-size:12px}.sev i{width:9px;height:9px;display:inline-block}
.sev.medium i{background:var(--warn);border-radius:50%}.sev.low i{border:2px solid var(--ink2);border-radius:50%}.sev.info i{border:1.5px dashed var(--muted);border-radius:2px}.sev.high i{background:var(--bad);transform:rotate(45deg)}
.pill{font-size:11px;border:1px solid var(--line);border-radius:4px;padding:0 6px;color:var(--ink2);white-space:nowrap}
.note{background:var(--accbg);border-radius:var(--r);padding:8px 10px;margin:10px 0;color:var(--ink2)}
.bar{height:6px;background:var(--line);border-radius:3px;overflow:hidden}.bar>i{display:block;height:100%;background:var(--acc)}
ul.res{margin:0;padding:0;list-style:none;font:12px ui-monospace,Menlo,Consolas,monospace}ul.res li{padding:2px 0;border-bottom:1px dotted var(--line)}
button{font:inherit;color:var(--ink);background:var(--pane);border:1px solid var(--line);border-radius:var(--r);padding:4px 10px;cursor:pointer}button[aria-pressed=true]{background:var(--accbg);border-color:var(--acc)}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
.na{opacity:.85}.na td:first-child{box-shadow:inset 3px 0 0 var(--warn)}
section.pane{max-height:calc(100vh - 90px);overflow:auto}#drawer{position:sticky;top:12px}td,th{overflow-wrap:anywhere}
@media (max-width:1000px){main{grid-template-columns:minmax(0,1fr)}section.pane{max-height:none}#drawer{position:static}}
</style></head><body>
<header><span class="logo">F<b>-</b>CAT <span style="font-weight:400;color:var(--muted)">workbench</span></span>
<span class="chip mock">Design mock-up, synthetic data</span><span class="chip" id="aud"></span><span class="chip">Recommends only. Never changes anything in Azure.</span>
<span style="margin-left:auto"><button id="theme" aria-pressed="false">Light / dark</button></span></header>
<main><aside class="pane" aria-label="Filters"></aside><section class="pane" aria-label="Findings by check"></section><aside class="pane" id="drawer" aria-live="polite"></aside></main>
<script>const D=/*DATA*/;"""
    + COMMON_JS
    + r"""
const st={sub:'all',doms:new Set(Object.keys(D.domains)),sev:new Set(['high','medium','low','info']),sel:null};
$('#aud').textContent='Self-audit: '+D.audit.status+' ('+D.audit.invariants+' invariants)';$('#aud').classList.add('ok');
$('#theme').onclick=e=>{const r=document.documentElement,d=r.dataset.theme==='dark'||(!r.dataset.theme&&matchMedia('(prefers-color-scheme:dark)').matches);r.dataset.theme=d?'light':'dark';e.target.setAttribute('aria-pressed',!d)};
const vis=c=>c.findings.filter(f=>(st.sub==='all'||f.sub===st.sub)&&st.sev.has(f.sev));
function side(){const a=$('aside');a.replaceChildren(h('h2',0,'SCOPE'),
 ...[['all','All subscriptions',total],...D.subs.map(s=>[s,s,D.checks.reduce((n,c)=>n+c.findings.filter(f=>f.sub===s).length,0)])].map(([v,l,n])=>h('label',0,h('input',{type:'radio',name:'sc',value:v,checked:st.sub===v,onchange:()=>{st.sub=v;draw()}}),l,h('span',{class:'n'},n))),
 h('h2',0,'AREA'),...Object.keys(D.domains).filter(d=>D.checks.some(c=>c.domain===d)).map(d=>h('label',0,h('input',{type:'checkbox',checked:st.doms.has(d),onchange:e=>{e.target.checked?st.doms.add(d):st.doms.delete(d);draw()}}),dn(d),h('span',{class:'n'},D.checks.filter(c=>c.domain===d).reduce((n,c)=>n+c.findings.length,0)))),
 h('h2',0,'SEVERITY'),...['high','medium','low','info'].map(s=>h('label',0,h('input',{type:'checkbox',checked:st.sev.has(s),onchange:e=>{e.target.checked?st.sev.add(s):st.sev.delete(s);draw()}}),h('span',{class:'sev '+s},h('i'),s))),
 h('div',{class:'note'},'Money is not shown. Cost data is not part of this run, so there are no savings figures to trust yet.'));}
function main(){const rows=D.checks.filter(c=>st.doms.has(c.domain)).map(c=>({c,v:vis(c)})).filter(x=>x.v.length||x.c.status!=='ran'&&st.sub==='all');
 rows.sort((a,b)=>b.v.length*(1+Math.max(0,...b.v.map(f=>SEV[f.sev])))-a.v.length*(1+Math.max(0,...a.v.map(f=>SEV[f.sev]))));
 const n=rows.reduce((a,x)=>a+x.v.length,0),mx=Math.max(1,...rows.map(x=>x.v.length));
 const s=$('section');s.replaceChildren(h('h2',0,'WHAT TO LOOK AT FIRST'),h('p',{style:'margin:0 0 8px;color:var(--ink2)'},n+' findings in '+rows.filter(x=>x.v.length).length+' kinds. Ordered by how many there are and how serious. Click a row for evidence.'),
 h('table',0,h('thead',0,h('tr',0,...['Check','Severity','Count','Confidence'].map(t=>h('th',{class:t==='Count'?'num':''},t)))),
 h('tbody',0,...rows.map(({c,v})=>{const top=v.reduce((m,f)=>SEV[f.sev]>SEV[m]?f.sev:m,'info');
  return h('tr',{class:'row'+(c.status!=='ran'?' na':''),tabindex:0,role:'button','aria-selected':st.sel===c.id,onclick:()=>{st.sel=c.id;draw()},onkeydown:e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();st.sel=c.id;draw()}}},
  h('td',0,c.title,h('div',{class:'id'},c.id)),
  h('td',0,c.status==='ran'?h('span',{class:'sev '+top},h('i'),top):h('span',{class:'pill'},'not assessed')),
  h('td',{class:'num'},c.status==='ran'?[v.length,h('div',{class:'bar'},h('i',{style:'width:'+Math.round(100*v.length/mx)+'%'}))]:'-'),
  h('td',0,h('span',{class:'pill'},c.conf)))}))))}
function drawer(){const d=$('#drawer'),c=D.checks.find(x=>x.id===st.sel);
 if(!c){d.replaceChildren(h('h2',0,'DETAIL'),h('p',{style:'color:var(--muted)'},'Select a check to see what was found, the evidence behind it, and what a person still has to confirm.'));return}
 const v=vis(c);
 d.replaceChildren(h('h2',0,c.id),h('h3',{style:'margin:0 0 6px;font-size:16px'},c.title),
  h('div',{style:'display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px'},h('span',{class:'pill'},dn(c.domain)),h('span',{class:'pill'},c.conf+' confidence'),h('span',{class:'pill'},c.framework),h('span',{class:'pill'},'not yet verified on a real tenant')),
  ...(c.status!=='ran'?[h('div',{class:'note'},'Not assessed, because: '+c.reason+'. Turn on rightsizing in the config to assess it.')]:[
  h('p',{style:'margin:0 0 6px'},v[0]?v[0].msg:''),
  h('h2',0,'RESOURCES ('+v.length+')'),h('ul',{class:'res'},...v.slice(0,10).map(f=>h('li',0,f.name,'  ',h('span',{style:'color:var(--muted)'},f.sub)))),v.length>10?h('p',{style:'color:var(--muted)'},'+ '+(v.length-10)+' more in the Excel export'):null,
  h('h2',0,'WHAT A PERSON MUST CONFIRM'),h('div',{class:'note'},D.help[c.domain]||'Review before acting.'),
  h('h2',0,'EVIDENCE'),h('div',{class:'id'},'logic '+c.logic+'  first fingerprint '+(v[0]?v[0].fp:'-'))]));}
function draw(){side();main();drawer()}draw();
</script></body></html>"""
)

# ---------------------------------------------------------------- 2. Atlas
ATLAS = (
    r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>F-CAT atlas</title><style>
:root{--bg:#e8efea;--pane:#f6f9f6;--ink:#10302a;--ink2:#3d5a52;--muted:#5f7a71;--line:#c5d5cc;--t0:#dbe9e1;--t1:#a9cdbb;--t2:#6aa68c;--t3:#2f7a60;--t4:#0f4d3a;--ochre:#9a6200;--r:3px}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0c1713;--pane:#13241d;--ink:#e3f0e9;--ink2:#b3ccc1;--muted:#8aa89b;--line:#27423a;--t0:#1b3329;--t1:#25503f;--t2:#2f7a60;--t3:#5db08f;--t4:#9fdcc0;--ochre:#f0b44a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
.w{max-width:1180px;margin:0 auto;padding:20px 16px 56px}
h1{font:600 34px/1.15 Georgia,"Iowan Old Style",serif;margin:0 0 4px;letter-spacing:-.01em}h2{font:600 20px Georgia,serif;margin:28px 0 6px}
.sub{color:var(--ink2);max-width:70ch;margin:0 0 14px}.chip{border:1px dashed var(--muted);border-radius:99px;padding:1px 10px;font-size:12px;color:var(--ink2)}
.tm{position:relative;height:460px;background:var(--pane);border:1px solid var(--line)}
.tile{position:absolute;overflow:hidden;border:2px solid var(--pane);padding:6px 8px;cursor:pointer;color:var(--ink);font-size:12px;line-height:1.25;text-align:left;background:var(--t1);font-family:inherit}
.tile:hover,.tile[aria-pressed=true]{outline:3px solid var(--ochre);outline-offset:-3px;z-index:2}.tile b{display:block;font-size:13px}
.tile.d3,.tile.d4{color:#fff}@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .tile.d3,:root:not([data-theme=light]) .tile.d4{color:#07140f}}
.subl{position:absolute;top:-22px;font:600 12px system-ui;color:var(--ink2);white-space:nowrap}
.cov{display:flex;flex-wrap:wrap;gap:3px}.sq{width:18px;height:18px;border:1px solid var(--line);background:var(--t2);border-radius:var(--r)}
.sq.na{background:repeating-linear-gradient(45deg,transparent 0 3px,var(--ochre) 3px 5px);border-color:var(--ochre)}.sq.zero{background:var(--t0)}
.key{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--ink2);margin:8px 0}.key i{display:inline-block;width:12px;height:12px;vertical-align:-1px;margin-right:4px;border:1px solid var(--line)}
table{border-collapse:collapse;width:100%;background:var(--pane)}th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{font-size:12px;color:var(--muted)}td.n{text-align:right;font-variant-numeric:tabular-nums}
.pn{overflow-x:auto}.btn{font:inherit;border:1px solid var(--line);background:var(--pane);color:var(--ink);padding:3px 10px;border-radius:99px;cursor:pointer}.btn[aria-pressed=true]{border-color:var(--ochre);box-shadow:inset 0 0 0 1px var(--ochre)}
:focus-visible{outline:2px solid var(--ochre);outline-offset:2px}.cols{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr);gap:24px}@media (max-width:860px){.cols{grid-template-columns:minmax(0,1fr)}.tm{height:520px}}
</style></head><body><div class="w">
<span class="chip">Design mock-up, synthetic data</span>
<h1>Where the findings sit</h1>
<p class="sub" id="lead"></p>
<div style="margin-top:34px"><div class="tm" id="tm" role="group" aria-label="Findings by subscription and area"></div></div>
<div class="key"><span>Tile area = number of findings</span><span><i style="background:var(--t1)"></i>fewer</span><span><i style="background:var(--t4)"></i>more per tile</span><span>Click a tile to list its checks</span></div>
<div class="cols"><div><h2 id="lt">Pick a tile</h2><div class="pn" id="list"></div></div>
<div><h2>Did every check run?</h2><p class="sub" style="font-size:14px">One square per check. Hatched means not assessed, and a finding count of zero never stands in for that.</p><div class="cov" id="cov"></div><div class="key"><span><i style="background:var(--t2)"></i>ran, has findings</span><span><i style="background:var(--t0)"></i>ran, none</span><span><i style="background:repeating-linear-gradient(45deg,transparent 0 3px,var(--ochre) 3px 5px)"></i>not assessed</span></div>
<h2>What is missing</h2><ul id="miss" style="padding-left:18px;margin:0;color:var(--ink2)"></ul></div></div>
<script>const D=/*DATA*/;"""
    + COMMON_JS
    + r"""
$('#lead').textContent=total+' findings across '+D.subs.length+' subscriptions. Dark tiles are where waste concentrates, which is where a first conversation with the owners usually pays off. This is an inventory of review prompts, not a savings estimate.';
// slice-and-dice treemap: subscriptions left to right, areas top to bottom
const cell={};D.checks.forEach(c=>c.findings.forEach(f=>{(cell[f.sub]??={});(cell[f.sub][c.domain]??=[]).push({c,f})}));
const subTot=s=>Object.values(cell[s]||{}).reduce((n,a)=>n+a.length,0);
const W=()=>$('#tm').clientWidth,H=()=>$('#tm').clientHeight;let selK=null;
function split(parts,total,min){// sqrt-damped weights, then a minimum size so small tiles stay readable
 const w=parts.map(Math.sqrt),S=w.reduce((a,b)=>a+b,0),free=Math.max(0,total-min*parts.length);return w.map(x=>min+free*x/S)}
function tm(){const el=$('#tm');el.replaceChildren();const w=W(),hgt=H(),subs=D.subs.filter(s=>subTot(s));
 const sw=split(subs.map(subTot),w,Math.min(130,0.7*w/subs.length));let x=0;
 const mx=Math.max(...subs.flatMap(s=>Object.values(cell[s]).map(a=>a.length)));
 subs.forEach((s,i)=>{const cw=sw[i],doms=Object.keys(cell[s]),dw=split(doms.map(d=>cell[s][d].length),hgt,40);let y=0;
  el.append(h('div',{class:'subl',style:`left:${x+2}px;width:${cw-4}px;overflow:hidden;text-overflow:ellipsis`,title:s},s.replace('sub-synth-','sub ')+' · '+subTot(s)));
  doms.forEach((d,j)=>{const ch=dw[j],n=cell[s][d].length,lv=Math.min(4,Math.floor(4*Math.sqrt(n/mx)+ (n>0?.5:0)));const k=s+'|'+d;
   el.append(h('button',{class:'tile d'+lv,'aria-pressed':selK===k,style:`left:${x}px;top:${y}px;width:${cw}px;height:${ch}px;background:var(--t${lv})`,onclick:()=>{selK=k;tm();list(s,d)}},h('b',0,dn(d)),n+(n===1?' finding':' findings')));y+=ch});x+=cw})}
function list(s,d){$('#lt').textContent=dn(d)+' in '+s;const by={};cell[s][d].forEach(({c,f})=>{(by[c.id]??={c,n:0,ex:[]});by[c.id].n++;if(by[c.id].ex.length<3)by[c.id].ex.push(f.name)});
 $('#list').replaceChildren(h('table',0,h('thead',0,h('tr',0,h('th',0,'Check'),h('th',0,'Examples'),h('th',{class:'n'},'Count'))),h('tbody',0,...Object.values(by).sort((a,b)=>b.n-a.n).map(({c,n,ex})=>h('tr',0,h('td',0,c.title),h('td',{style:'font:12px ui-monospace,monospace;color:var(--muted)'},ex.join(', ')),h('td',{class:'n'},n))))),h('p',{class:'sub',style:'margin-top:8px;font-size:14px'},D.help[d]||''))}
$('#cov').replaceChildren(...D.checks.map(c=>h('div',{class:'sq '+(c.status!=='ran'?'na':c.findings.length?'':'zero'),title:c.id+': '+(c.status==='ran'?c.findings.length+' findings':'not assessed')})));
$('#miss').replaceChildren(...na.map(c=>h('li',0,c.id+' not assessed: '+c.reason)),h('li',0,'Cost data: not collected, so no money figures and no cost-based checks.'),h('li',0,D.caps.filter(c=>c.kind==='customer').length+' maturity capabilities wait for answers from your team.'));
tm();addEventListener('resize',()=>{tm()});
</script></div></body></html>"""
)

# ---------------------------------------------------------------- 3. Briefing
BRIEFING = (
    r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>F-CAT briefing</title><style>
:root{--bg:#ffffff;--ink:#14110f;--ink2:#4a4540;--muted:#6e675f;--line:#dcd7d0;--acc:#7a1f3d;--accbg:#f6e9ee;--ok:#1d6b3a;--warn:#8a5700;--r:10px}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#15110f;--ink:#f4efe9;--ink2:#cfc7bd;--muted:#a49b8f;--line:#352f2a;--acc:#e58aa8;--accbg:#2a1820;--ok:#6fd094;--warn:#f2b84b}}
*{box-sizing:border-box}html{scroll-snap-type:y proximity}body{margin:0;background:var(--bg);color:var(--ink);font:18px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
nav{position:fixed;top:0;left:0;right:0;display:flex;gap:4px;align-items:center;padding:10px 16px;background:var(--bg);border-bottom:1px solid var(--line);z-index:5;overflow-x:auto}
nav button{font:14px system-ui;border:0;background:none;color:var(--muted);padding:6px 10px;border-radius:99px;cursor:pointer;white-space:nowrap}nav button[aria-current=true]{background:var(--accbg);color:var(--acc);font-weight:600}
nav .mk{margin-left:auto;font-size:12px;border:1px dashed var(--muted);border-radius:99px;padding:1px 10px;color:var(--muted);white-space:nowrap}
section{min-height:100vh;padding:96px max(16px,calc((100vw - 980px)/2)) 56px;scroll-snap-align:start;border-bottom:1px solid var(--line)}
.k{font:14px system-ui;color:var(--acc);font-weight:600;margin:0 0 8px}h1,h2{font:600 clamp(32px,5vw,54px)/1.1 Georgia,"Iowan Old Style",serif;margin:0 0 18px;letter-spacing:-.015em;max-width:20ch}
.big{font:600 clamp(64px,12vw,140px)/1 Georgia,serif;color:var(--acc);margin:12px 0;font-variant-numeric:lining-nums}
.facts{display:flex;gap:32px;flex-wrap:wrap;margin:24px 0}.facts div{min-width:120px}.facts b{display:block;font:600 40px Georgia,serif}.facts span{color:var(--muted);font-size:15px}
p.l{max-width:60ch;color:var(--ink2)}.bars div{display:grid;grid-template-columns:minmax(120px,240px) 1fr 48px;gap:12px;align-items:center;padding:6px 0;font-size:16px}.bars i{display:block;height:14px;background:var(--acc);border-radius:0 4px 4px 0}.bars em{font-style:normal;text-align:right;font-variant-numeric:tabular-nums}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}.card{border:1px solid var(--line);border-radius:var(--r);padding:18px}.card h3{margin:0 0 6px;font-size:18px}.card p{margin:0;font-size:16px;color:var(--ink2)}.card .t{font:600 13px system-ui;color:var(--warn);margin-bottom:6px}
.caps{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:8px}.cap{border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:14px}.cap small{display:block;color:var(--muted);font-size:12px}.cap.partial{border-color:var(--acc)}
.plan{border-collapse:collapse;width:100%;font-size:16px}.plan td,.plan th{border-bottom:1px solid var(--line);padding:10px 8px;text-align:left;vertical-align:top}.plan input{font:inherit;width:100%;border:1px dashed var(--muted);background:none;color:var(--ink);padding:4px 6px;border-radius:6px}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px}.foot{margin-top:28px;color:var(--muted);font-size:14px}
@media print{nav{display:none}section{min-height:0;page-break-after:always;padding-top:24px}}@media (max-width:640px){body{font-size:16px}.bars div{grid-template-columns:100px 1fr 40px}}
</style></head><body>
<nav id="nav" aria-label="Sections"></nav>
<section id="s1"><p class="k">What we looked at</p><h1>A first look at your Azure estate</h1><p class="l">We read your subscriptions with read-only access. We did not change, stop or delete anything, and we never will. What follows is a set of things worth a conversation, with the limits of what we could see stated plainly.</p><div class="facts" id="facts"></div></section>
<section id="s2"><p class="k">What we found</p><h2>Most of it is leftovers</h2><div class="big" id="big"></div><p class="l" id="bigt"></p><div class="bars" id="bars"></div></section>
<section id="s3"><p class="k">What we could not see</p><h2>Three honest gaps</h2><p class="l">A missing result is never shown as zero. Each gap says why and what would close it.</p><div class="cards" id="gaps"></div></section>
<section id="s4"><p class="k">FinOps maturity</p><h2>No score yet, on purpose</h2><p class="l">A capability is scored only from technical evidence plus answers from your team. Today most are waiting for one or the other.</p><div class="caps" id="caps"></div></section>
<section id="s5"><p class="k">Suggested next 30 days</p><h2>Three moves, with owners</h2><table class="plan"><thead><tr><th>What</th><th>Why</th><th>Owner</th><th>By</th></tr></thead><tbody id="plan"></tbody></table><p class="foot">Design mock-up with synthetic data. Owner and date cells are editable in the browser only; nothing is saved or sent.</p></section>
<script>const D=/*DATA*/;"""
    + COMMON_JS
    + r"""
const nm=['Scope','Findings','Gaps','Maturity','Next steps'];
$('#nav').replaceChildren(...nm.map((t,i)=>h('button',{onclick:()=>$('#s'+(i+1)).scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'})},t)),h('span',{class:'mk'},'Design mock-up, synthetic data'));
$('#facts').replaceChildren(...[[D.scope.subscriptions,'subscriptions'],[D.scope.management_groups,'management groups'],[ran.length,'checks ran'],[na.length,'not assessed']].map(([n,l])=>h('div',0,h('b',0,n),h('span',0,l))));
const dom={};D.checks.forEach(c=>dom[c.domain]=(dom[c.domain]||0)+c.findings.length);const ds=Object.entries(dom).sort((a,b)=>b[1]-a[1]);
const orph=dom.orphaned||0;$('#big').textContent=orph;$('#bigt').textContent='of our '+total+' findings are orphaned resources: disks, addresses and similar items that nothing seems to use. They are the easiest first conversation, because the question is simply "does anyone still need this?"';
$('#bars').replaceChildren(...ds.map(([d,n])=>h('div',0,dn(d),h('i',{style:'width:'+Math.max(2,100*n/ds[0][1])+'%'}),h('em',0,n))));
$('#gaps').replaceChildren(
 h('div',{class:'card'},h('div',{class:'t'},'NOT ASSESSED'),h('h3',0,'Rightsizing'),h('p',0,'Needs usage history from Azure Monitor, which is switched off by default. '+(na[0]?na[0].id+' did not run.':''))),
 h('div',{class:'card'},h('div',{class:'t'},'NEEDS COST DATA'),h('h3',0,'Money'),h('p',0,'No cost data was collected, so there are no savings figures. We would rather show none than guess.')),
 h('div',{class:'card'},h('div',{class:'t'},'NEEDS YOUR INPUT'),h('h3',0,'How your teams work'),h('p',0,D.caps.filter(c=>c.kind==='customer').length+' maturity topics, such as budgeting habits and ownership, cannot be read from Azure. A short questionnaire covers them.')));
$('#caps').replaceChildren(...D.caps.map(c=>h('div',{class:'cap '+c.kind},c.name,h('small',0,{cost:'Waiting for cost data',customer:'Needs your input',partial:'Partial evidence, no score',unbuilt:'Check not built yet'}[c.kind]))));
$('#plan').replaceChildren(...[['Review the unattached disks and addresses','Largest group of findings; the question is only "is it still needed?"'],['Grant read access to cost data','Unlocks savings figures and the cost-based checks'],['Answer the leadership questions','Unlocks the maturity view for the topics Azure cannot show']].map(([a,b])=>h('tr',0,h('td',0,a),h('td',{style:'color:var(--ink2)'},b),h('td',0,h('input',{'aria-label':'Owner for '+a,placeholder:'name'})),h('td',0,h('input',{'aria-label':'Date for '+a,placeholder:'date'})))));
const secs=$$('section'),btns=$$('#nav button');secs.forEach(s=>new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)btns.forEach((b,i)=>b.setAttribute('aria-current',secs[i]===e.target))}),{threshold:.5}).observe(s));
</script></body></html>"""
)

INDEX = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>F-CAT front-end variations</title>
<style>body{font:16px/1.5 system-ui,sans-serif;max-width:760px;margin:0 auto;padding:24px 16px;color:#14110f}@media (prefers-color-scheme:dark){body{background:#15110f;color:#f4efe9}a{color:#8ab4f8}}
h1{font-size:28px}li{margin:14px 0}small{color:#777}</style></head><body><h1>F-CAT front-end: three early variations</h1>
<p>Same synthetic data, three different ideas of the product. Super early drafts to react to, not designs to implement.</p><ol>
<li><a href="1-workbench.html"><b>Workbench</b></a> for the practitioner: filters left, a ranked queue in the middle, evidence and "what a person must confirm" on the right.</li>
<li><a href="2-atlas.html"><b>Atlas</b></a> for finding where to look: a treemap of subscriptions and areas, plus a coverage strip that shows which checks did not run.</li>
<li><a href="3-briefing.html"><b>Briefing</b></a> for the customer workshop: five large-type sections that can be read top to bottom or printed, ending in an owner-and-date plan.</li></ol>
<p><small>Generated by scripts/make_frontend_mockups.py from tests/golden/report.json. System fonts, no network, light and dark.</small></p></body></html>"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.dumps(build_data(), separators=(",", ":")).replace("</", "<\\/")
    for name, tpl in (("1-workbench", WORKBENCH), ("2-atlas", ATLAS), ("3-briefing", BRIEFING)):
        (OUT / f"{name}.html").write_text(tpl.replace("/*DATA*/", data))
    (OUT / "index.html").write_text(INDEX)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
