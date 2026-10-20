"""Second round of front-end design mock-ups (owner feedback 2026-10-20): workbench base + at-a-glance summary + atlas-style map,
adjustable branding slot, notes fields, Azure tag views, PDF export by browser print. Synthetic data only, tags are SYNTHETIC (the real report does not carry tags yet).
Output: docs/mockups/frontend2/*.html. Self-contained, system fonts, no network."""

from __future__ import annotations

import importlib.util
import json
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "mockups" / "frontend2"
spec = importlib.util.spec_from_file_location("v1", ROOT / "scripts" / "make_frontend_mockups.py")
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)

TAGS = {
    "env": ["prod", "dev", "test"],
    "owner": ["team-apps", "team-data", "team-infra"],
    "costcenter": ["CC-100", "CC-200", "CC-300"],
    "app": ["web", "data", "net"],
}
PRESENT = {"env": 0.75, "owner": 0.55, "costcenter": 0.4, "app": 0.3}


def synth_tags(name: str):
    out = {}
    for k, vals in TAGS.items():
        h = zlib.crc32(f"{name}|{k}".encode())
        if (h % 100) / 100 < PRESENT[k]:
            out[k] = vals[(h >> 8) % len(vals)]
    return out


def build():
    d = v1.build_data()
    for c in d["checks"]:
        for f in c["findings"]:
            f["tags"] = None if c["id"] in ("BILL-OFFER-01", "SEC-DEFDEV-01") else synth_tags(f["name"])
    d["tagKeys"] = list(TAGS)
    return d


CSS = r"""
:root{--bg:#e9eef4;--pane:#f7f9fb;--ink:#13233a;--ink2:#46556b;--muted:#66758a;--line:#d3dce7;--acc:#1f5fbf;--ok:#0b6b2e;--warn:#8a5700;--bad:#a12626;--r:6px}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0e141c;--pane:#16202c;--ink:#e6edf6;--ink2:#b3c0d1;--muted:#8e9db1;--line:#2a3a4d;--ok:#4cc27a;--warn:#f2b84b;--bad:#f08a8a}}
:root[data-theme=dark]{--bg:#0e141c;--pane:#16202c;--ink:#e6edf6;--ink2:#b3c0d1;--muted:#8e9db1;--line:#2a3a4d;--ok:#4cc27a;--warn:#f2b84b;--bad:#f08a8a}
:root{--accbg:color-mix(in srgb,var(--acc) 14%,var(--pane))}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
button,select,input,textarea{font:inherit;color:var(--ink);background:var(--pane);border:1px solid var(--line);border-radius:var(--r);padding:4px 8px}
button{cursor:pointer}button:hover{border-color:var(--acc)}button[aria-pressed=true],button.on{background:var(--accbg);border-color:var(--acc)}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px}textarea{width:100%;resize:vertical;min-height:54px}
header.top{display:flex;gap:14px;align-items:center;flex-wrap:wrap;padding:8px 16px;background:var(--pane);border-bottom:1px solid var(--line);position:relative}
.brand{display:flex;gap:10px;align-items:center;min-width:0}.logo{width:40px;height:40px;border-radius:8px;background:var(--acc);color:#fff;display:grid;place-items:center;font-weight:700;font-size:18px;overflow:hidden;flex:none}.logo img{width:100%;height:100%;object-fit:contain;background:#fff}
.bn{font-weight:700;line-height:1.15}.bt{color:var(--muted);font-size:12px}
.gear{border:0;background:none;color:var(--muted);padding:2px 6px}
.pop{position:absolute;left:12px;top:56px;z-index:20;width:300px;background:var(--pane);border:1px solid var(--line);border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,.25);padding:12px;display:none}.pop.open{display:block}
.pop label{display:block;margin:8px 0 2px;color:var(--muted);font-size:12px}.pop input[type=text]{width:100%}.pop input[type=color]{padding:0;height:30px;width:60px}
.tools{margin-left:auto;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.chip{border:1px solid var(--line);border-radius:99px;padding:2px 10px;color:var(--ink2);font-size:12px;white-space:nowrap}.chip.ok{color:var(--ok);border-color:currentColor}.chip.mock{border-style:dashed}
.pane{background:var(--pane);border:1px solid var(--line);border-radius:var(--r);padding:12px;min-width:0}
h2{font-size:12px;margin:14px 0 6px;color:var(--muted);font-weight:600;letter-spacing:.04em;text-transform:none}h2:first-child{margin-top:0}
h3{margin:0 0 6px;font-size:16px}
.wrap{padding:12px;display:grid;gap:12px}
.grid3{display:grid;grid-template-columns:230px minmax(0,1fr) 350px;gap:12px;align-items:start}
@media (max-width:1050px){.grid3{grid-template-columns:minmax(0,1fr)}}
label.opt{display:flex;gap:8px;align-items:center;padding:3px 0;cursor:pointer}label.opt span.n{margin-left:auto;color:var(--muted);font-variant-numeric:tabular-nums}
table{border-collapse:collapse;width:100%}th{white-space:nowrap;font-size:12px;color:var(--muted);text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--pane);z-index:1}
td{padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top;overflow-wrap:anywhere}tr.row{cursor:pointer}tr.row:hover td,tr.row[aria-selected=true] td{background:var(--accbg)}tr.row[aria-selected=true] td:first-child{box-shadow:inset 3px 0 0 var(--acc)}
td.num{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}.id{font:12px ui-monospace,Menlo,Consolas,monospace;color:var(--muted)}
.sev{display:inline-flex;gap:5px;align-items:center;font-size:12px}.sev i{width:9px;height:9px;display:inline-block}.sev.medium i{background:var(--warn);border-radius:50%}.sev.low i{border:2px solid var(--ink2);border-radius:50%}.sev.info i{border:1.5px dashed var(--muted);border-radius:2px}.sev.high i{background:var(--bad);transform:rotate(45deg)}
.pill{font-size:11px;border:1px solid var(--line);border-radius:4px;padding:0 6px;color:var(--ink2);white-space:nowrap;display:inline-block}
.tag{font:11px ui-monospace,Menlo,monospace;background:var(--accbg);border-radius:4px;padding:0 5px;margin:0 3px 3px 0;display:inline-block;cursor:pointer;color:var(--ink)}.tag.none{background:none;border:1px dashed var(--muted);color:var(--muted);cursor:default}
.note{background:var(--accbg);border-radius:var(--r);padding:8px 10px;margin:10px 0;color:var(--ink2)}
.bar{height:6px;background:var(--line);border-radius:3px;overflow:hidden}.bar>i{display:block;height:100%;background:var(--acc)}
ul.res{margin:0;padding:0;list-style:none}ul.res li{padding:4px 0;border-bottom:1px dotted var(--line)}.rn{font:12px ui-monospace,Menlo,Consolas,monospace}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}.kpi{border:1px solid var(--line);border-radius:var(--r);padding:10px 12px;background:var(--pane)}.kpi b{display:block;font-size:30px;line-height:1.1;font-variant-numeric:tabular-nums}.kpi span{color:var(--muted);font-size:12px}
.kpi.warn{border-color:var(--warn)}.kpi.warn b{color:var(--warn)}
.headline{font-size:17px;max-width:90ch;margin:0}.sub{color:var(--ink2);margin:2px 0 0}
.abars div.r{display:grid;grid-template-columns:minmax(90px,170px) 1fr 36px;gap:8px;align-items:center;padding:2px 0;cursor:pointer;font-size:13px}.abars div.r:hover{background:var(--accbg)}.abars .bar{height:10px}.abars em{font-style:normal;text-align:right;font-variant-numeric:tabular-nums}
.sevbar{display:flex;height:14px;border-radius:4px;overflow:hidden;gap:2px}.sevbar i{display:block;min-width:3px}
.tm{position:relative;height:300px;background:var(--bg);border:1px solid var(--line);border-radius:var(--r)}
.tile{position:absolute;overflow:hidden;border:2px solid var(--pane);padding:5px 7px;cursor:pointer;color:var(--ink);font-size:12px;line-height:1.25;text-align:left;font-family:inherit;border-radius:3px}
.tile:hover,.tile[aria-pressed=true]{outline:3px solid var(--ink);outline-offset:-3px;z-index:2}.tile b{display:inline;font-size:12px;margin-right:6px}.tile{white-space:nowrap;text-overflow:ellipsis;display:flex;align-items:flex-start;gap:0}.tile.dk{color:#fff}
.subl{position:absolute;top:-18px;font:600 11px system-ui;color:var(--ink2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cov{display:flex;flex-wrap:wrap;gap:3px}.sq{width:16px;height:16px;border-radius:3px;background:var(--acc);opacity:.75}.sq.na{background:repeating-linear-gradient(45deg,transparent 0 3px,var(--warn) 3px 5px);border:1px solid var(--warn);opacity:1}
.tabs{display:flex;gap:4px;flex-wrap:wrap;border-bottom:1px solid var(--line);padding:0 12px;background:var(--pane)}.tabs button{border:0;border-bottom:3px solid transparent;border-radius:0;background:none;padding:10px 12px}.tabs button[aria-selected=true]{border-bottom-color:var(--acc);font-weight:600}
.row2{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}
.grid3>section.pane{max-height:calc(100vh - 70px);overflow:auto}.grid3>aside#drawer{position:sticky;top:8px;max-height:calc(100vh - 20px);overflow:auto}
@media (max-width:1050px){.grid3>section.pane,.grid3>aside#drawer{max-height:none;position:static}}
@media print{.grid3>section.pane,.grid3>aside#drawer{max-height:none!important;overflow:visible!important;position:static!important}}
.mini{font-size:12px;color:var(--muted)}.right{margin-left:auto}.hide{display:none!important}
.printonly{display:none}
@media (max-width:640px){.tm{height:340px}.tools{margin-left:0}}
@media print{
 @page{margin:14mm}
 html,body{background:#fff!important;color:#000}
 .noprint,.tools,.tabs,.pop,aside.side,.gear{display:none!important}.printonly{display:block}
 .grid3{display:block}.pane,.kpi{border-color:#bbb}.kpi,.note,.basket-print .pane{break-inside:avoid}tr{break-inside:avoid}.wrap{padding:0}
 header.top{background:none;border-bottom:2px solid var(--acc);padding:0 0 8px;margin-bottom:8px}
 th{position:static}textarea{border:0;padding:0;min-height:0;height:auto;resize:none;overflow:visible}
 .tm{height:260px}
}
"""

JS = r"""
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
function h(t,a,...k){const e=document.createElement(t);for(const[x,v]of Object.entries(a||{})){if(x==='class')e.className=v;else if(x==='value')e.value=v;else if(x.startsWith('on'))e.addEventListener(x.slice(2),v);else if(v!==false&&v!=null)e.setAttribute(x,v===true?'':v)}for(const c of k.flat(2))if(c!=null&&c!==false)e.append(c.nodeType?c:document.createTextNode(c));return e}
const store={get(k,d){try{const v=localStorage.getItem('fcat2:'+k);return v===null?d:JSON.parse(v)}catch(e){return d}},set(k,v){try{localStorage.setItem('fcat2:'+k,JSON.stringify(v))}catch(e){}}};
const SEV={high:3,medium:2,low:1,info:0},SEVC={high:'var(--bad)',medium:'var(--warn)',low:'var(--ink2)',info:'var(--muted)'};
const STATUSES=['To review','Confirmed','Ask owner',"Won't fix"];
const dn=d=>D.domains[d]||d, ran=D.checks.filter(c=>c.status==='ran'), na=D.checks.filter(c=>c.status!=='ran');
const total=D.checks.reduce((a,c)=>a+c.findings.length,0);
const st={sub:'all',area:null,sev:new Set(['high','medium','low','info']),tag:null,sel:null,group:'costcenter'};
const R=[];const mount=(el,fn)=>{R.push([el,fn]);return el};
function draw(){for(const[el,fn]of R){const x=fn();el.replaceChildren(...[].concat(x).filter(Boolean))}}
const stOf=id=>store.get('st:'+id,'To review'), noteOf=id=>store.get('note:'+id,''), ownOf=id=>store.get('own:'+id,'');
const hasTag=(f,t)=>!t||(f.tags&&f.tags[t.k]===t.v)||(t.v==='(none)'&&f.tags&&!f.tags[t.k]);
const vis=c=>c.findings.filter(f=>(st.sub==='all'||f.sub===st.sub)&&st.sev.has(f.sev)&&hasTag(f,st.tag));
const rows=()=>D.checks.filter(c=>!st.area||c.domain===st.area).map(c=>({c,v:vis(c)})).filter(x=>x.v.length);
const score=x=>x.v.length*(1+Math.max(0,...x.v.map(f=>SEV[f.sev])));
const allVis=()=>rows().flatMap(x=>x.v.map(f=>({...f,c:x.c})));
function sevIcon(s){return h('span',{class:'sev '+s},h('i'),s)}
/* ---------- branding ---------- */
function applyBrand(b){document.documentElement.style.setProperty('--acc',b.accent);document.title=b.name+' | assessment'}
function brandBlock(){
 let b={...BRAND,...store.get('brand',{})};applyBrand(b);
 const logo=h('div',{class:'logo',id:'logo','aria-hidden':'true'}),nm=h('div',{class:'bn'}),tg=h('div',{class:'bt'});
 const paint=()=>{logo.replaceChildren(b.logo?h('img',{src:b.logo,alt:''}):(b.name||'?').trim().charAt(0).toUpperCase());nm.textContent=b.name;tg.textContent=b.tag;applyBrand(b)};
 const save=()=>{store.set('brand',b);paint()};
 const pop=h('div',{class:'pop',role:'dialog','aria-label':'Branding'},
  h('b',0,'Your branding'),h('p',{class:'mini'},'Applies to this view and to the PDF. In the real tool this comes from the config file, with a logo file path.'),
  h('label',0,'Company name'),h('input',{type:'text',value:b.name,oninput:e=>{b.name=e.target.value;save()}}),
  h('label',0,'Tagline'),h('input',{type:'text',value:b.tag,oninput:e=>{b.tag=e.target.value;save()}}),
  h('label',0,'Accent colour'),h('input',{type:'color',value:b.accent,oninput:e=>{b.accent=e.target.value;save();draw()}}),
  h('label',0,'Logo (PNG, SVG or JPG, up to 200 KB)'),h('input',{type:'file',accept:'image/*',onchange:e=>{const f=e.target.files[0];if(!f||f.size>200000)return;const r=new FileReader();r.onload=()=>{b.logo=r.result;save()};r.readAsDataURL(f)}}),
  h('div',{style:'display:flex;gap:8px;margin-top:10px'},h('button',{onclick:()=>{b={...BRAND};store.set('brand',{});paint();pop.querySelectorAll('input[type=text]').forEach((i,n)=>i.value=n?b.tag:b.name);pop.classList.remove('open')}},'Reset'),h('button',{onclick:()=>pop.classList.remove('open')},'Done')));
 paint();
 const gear=h('button',{class:'gear noprint','aria-label':'Edit branding',title:'Edit branding',onclick:()=>pop.classList.toggle('open')},'⚙');
 return [h('div',{class:'brand'},logo,h('div',0,nm,tg),gear),pop];
}
/* ---------- shared components ---------- */
function topBar(extra){
 const t=h('header',{class:'top'});t.append(...brandBlock(),h('div',{class:'tools'},
  h('span',{class:'chip mock noprint'},'Design mock-up, synthetic data'),h('span',{class:'chip ok'},'Self-audit: '+D.audit.status),
  extra||null,
  h('button',{class:'noprint',title:'Opens the print dialog. Choose Save as PDF.',onclick:()=>window.print()},'Export PDF'),
  h('button',{class:'noprint',id:'theme',onclick:()=>{const r=document.documentElement,d=r.dataset.theme==='dark'||(!r.dataset.theme&&matchMedia('(prefers-color-scheme:dark)').matches);r.dataset.theme=d?'light':'dark'}},'Light / dark')));
 return t}
function filterText(){const p=[];if(st.sub!=='all')p.push('scope '+st.sub);if(st.area)p.push('area '+dn(st.area));if(st.tag)p.push('tag '+st.tag.k+'='+st.tag.v);if(st.sev.size<4)p.push('severity '+[...st.sev].join('/'));return p.length?'Filters: '+p.join(', '):'No filters: all scopes, areas and severities'}
function headlineText(){const rs=rows(),n=rs.reduce((a,x)=>a+x.v.length,0);const by={};rs.forEach(x=>by[x.c.domain]=(by[x.c.domain]||0)+x.v.length);const top=Object.entries(by).sort((a,b)=>b[1]-a[1])[0];
 return n+' findings in '+rs.length+' kinds'+(top?'. '+dn(top[0])+' is the biggest area ('+Math.round(100*top[1]/n)+'%)':'')+'. '+na.length+' check'+(na.length===1?'':'s')+' not assessed. No savings are shown: no cost data was collected.'}
function ring(p,label,sub){const r=26,c=2*Math.PI*r;return h('div',{class:'kpi',style:'display:flex;gap:10px;align-items:center'},(()=>{const s=document.createElementNS('http://www.w3.org/2000/svg','svg');s.setAttribute('width',64);s.setAttribute('height',64);s.setAttribute('viewBox','0 0 64 64');s.setAttribute('role','img');s.setAttribute('aria-label',label+' '+Math.round(p*100)+'%');
 s.innerHTML='<circle cx="32" cy="32" r="'+r+'" fill="none" stroke="var(--line)" stroke-width="7"/><circle cx="32" cy="32" r="'+r+'" fill="none" stroke="var(--acc)" stroke-width="7" stroke-dasharray="'+(c*p)+' '+c+'" transform="rotate(-90 32 32)" stroke-linecap="round"/><text x="32" y="36" text-anchor="middle" font-size="14" font-weight="700" fill="var(--ink)">'+Math.round(p*100)+'%</text>';return s})(),h('div',0,h('b',{style:'font-size:15px'},label),h('span',0,sub)))}
function kpis(){const rs=rows(),n=rs.reduce((a,x)=>a+x.v.length,0),all=D.checks.filter(c=>c.findings.length);const rev=all.filter(c=>stOf(c.id)!=='To review').length;
 return h('div',{class:'kpis'},
  h('div',{class:'kpi'},h('b',0,n),h('span',0,'findings'+(n!==total?' (of '+total+')':''))),
  h('div',{class:'kpi'},h('b',0,rs.length),h('span',0,'kinds of issue')),
  h('div',{class:'kpi warn',title:na.map(c=>c.id+': '+c.reason).join('\n')},h('b',0,na.length),h('span',0,'check not assessed (hover for why)')),
  ring(all.length?rev/all.length:0,'Reviewed',rev+' of '+all.length+' kinds triaged'),
  ring(ran.length/D.checks.length,'Coverage',ran.length+' of '+D.checks.length+' checks ran'))}
function areaBars(){const by={};D.checks.forEach(c=>{if(!st.area||c.domain===st.area)by[c.domain]=(by[c.domain]||0)+vis(c).length});const es=Object.entries(by).filter(e=>e[1]).sort((a,b)=>b[1]-a[1]),mx=Math.max(1,es[0]?es[0][1]:1);
 const all={};D.checks.forEach(c=>all[c.domain]=(all[c.domain]||0)+vis(c).length);const e2=Object.entries(all).filter(e=>e[1]).sort((a,b)=>b[1]-a[1]);
 return h('div',{class:'abars'},...e2.map(([d,n])=>h('div',{class:'r',role:'button',tabindex:0,title:'Filter to this area',onclick:()=>{st.area=st.area===d?null:d;draw()},onkeydown:e=>{if(e.key==='Enter'){st.area=st.area===d?null:d;draw()}}},h('span',{style:st.area===d?'font-weight:700':''},dn(d)),h('div',{class:'bar'},h('i',{style:'width:'+Math.max(2,100*n/e2[0][1])+'%'})),h('em',0,n))))}
function sevBar(){const c={high:0,medium:0,low:0,info:0};D.checks.forEach(k=>vis(k).forEach(f=>c[f.sev]++));const t=Object.values(c).reduce((a,b)=>a+b,0)||1;
 return h('div',0,h('div',{class:'sevbar',role:'img','aria-label':'Severity split'},...Object.entries(c).filter(e=>e[1]).map(([s,n])=>h('i',{style:'flex:'+n+';background:'+SEVC[s],title:s+': '+n}))),h('div',{style:'display:flex;gap:12px;flex-wrap:wrap;margin-top:6px'},...Object.entries(c).map(([s,n])=>h('span',{class:'mini'},sevIcon(s),' ',n))))}
function treemap(height){
 const cell={};D.checks.forEach(c=>c.findings.forEach(f=>{if(st.sev.has(f.sev)&&hasTag(f,st.tag)){(cell[f.sub]??={});(cell[f.sub][c.domain]??=[]).push(f)}}));
 const subs=D.subs.filter(s=>cell[s]);const el=h('div',{class:'tm',style:height?'height:'+height+'px':''});
 requestAnimationFrame(()=>{const w=el.clientWidth,hg=el.clientHeight;if(!w)return;const split=(parts,tot,min)=>{const x=parts.map(Math.sqrt),S=x.reduce((a,b)=>a+b,0),free=Math.max(0,tot-min*parts.length);return x.map(v=>min+free*v/S)};
  const sw=split(subs.map(s=>Object.values(cell[s]).reduce((a,b)=>a+b.length,0)),w,Math.min(110,.7*w/Math.max(1,subs.length)));let x=0;const mx=Math.max(1,...subs.flatMap(s=>Object.values(cell[s]).map(a=>a.length)));
  subs.forEach((s,i)=>{const ds=Object.keys(cell[s]),dh=split(ds.map(d=>cell[s][d].length),hg,Math.min(30,.9*hg/ds.length));let y=0;el.append(h('div',{class:'subl',style:`left:${x+2}px;width:${sw[i]-4}px`,title:s},s.replace('sub-synth-','sub ')));
   ds.forEach((d,j)=>{const n=cell[s][d].length,lv=Math.sqrt(n/mx),sel=st.sub===s&&st.area===d;el.append(h('button',{class:'tile'+(lv>.55?' dk':''),'aria-pressed':sel,title:dn(d)+' in '+s+': '+n,style:`left:${x}px;top:${y}px;width:${sw[i]}px;height:${dh[j]}px;background:color-mix(in srgb,var(--acc) ${Math.round(14+78*lv)}%,var(--pane))`,onclick:()=>{if(sel){st.sub='all';st.area=null}else{st.sub=s;st.area=d}draw()}},h('b',0,dn(d)),h('span',0,String(n))));y+=dh[j]});x+=sw[i]})});
 return h('div',0,h('div',{style:'height:20px'}),el,h('div',{class:'mini',style:'margin-top:4px'},'Tile area follows the number of findings. Click a tile to filter everything else; click again to clear.'))}
function sideFilters(){
 const subN=s=>D.checks.reduce((n,c)=>n+c.findings.filter(f=>f.sub===s&&st.sev.has(f.sev)&&hasTag(f,st.tag)).length,0);
 return [h('h2',0,'SCOPE'),...[['all','All subscriptions',null],...D.subs.map(s=>[s,s,subN(s)])].map(([v,l,n])=>h('label',{class:'opt'},h('input',{type:'radio',name:'sc',value:v,checked:st.sub===v,onchange:()=>{st.sub=v;draw()}}),l,h('span',{class:'n'},n===null?total:n))),
  h('h2',0,'AREA'),...Object.keys(D.domains).filter(d=>D.checks.some(c=>c.domain===d)).map(d=>h('label',{class:'opt'},h('input',{type:'radio',name:'ar',checked:st.area===d,onclick:e=>{if(st.area===d){st.area=null;e.target.checked=false}else st.area=d;draw()}}),dn(d),h('span',{class:'n'},D.checks.filter(c=>c.domain===d).reduce((n,c)=>n+vis(c).length,0)))),
  h('h2',0,'SEVERITY'),...['high','medium','low','info'].map(s=>h('label',{class:'opt'},h('input',{type:'checkbox',checked:st.sev.has(s),onchange:e=>{e.target.checked?st.sev.add(s):st.sev.delete(s);draw()}}),sevIcon(s))),
  h('h2',0,'AZURE TAG'),st.tag?h('div',0,h('span',{class:'tag'},st.tag.k+'='+st.tag.v),' ',h('button',{onclick:()=>{st.tag=null;draw()}},'Clear')):h('div',{class:'mini'},'Click a tag on any resource, or open the Tags view.'),
  h('div',{class:'note'},'Money is not shown. Cost data is not part of this run, so there are no savings figures to trust yet.')]}
function queue(onPick){const rs=rows().sort((a,b)=>score(b)-score(a));const mx=Math.max(1,...rs.map(x=>x.v.length));
 return [h('h2',0,'WHAT TO LOOK AT FIRST'),h('p',{style:'margin:0 0 8px;color:var(--ink2)'},'Ordered by how many there are and how serious. Click a row for evidence and notes.'),
  h('table',0,h('thead',0,h('tr',0,...['Check','Severity','Count','Status'].map(t=>h('th',{class:t==='Count'?'num':''},t)))),h('tbody',0,...rs.map(({c,v})=>{const top=v.reduce((m,f)=>SEV[f.sev]>SEV[m]?f.sev:m,'info');
  return h('tr',{class:'row',tabindex:0,role:'button','aria-selected':st.sel===c.id,onclick:()=>{st.sel=c.id;(onPick||draw)();draw()},onkeydown:e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();st.sel=c.id;draw()}}},
   h('td',0,c.title,noteOf(c.id)?h('span',{title:'Has a note'},' ✎'):null,h('div',{class:'id'},c.id)),h('td',0,sevIcon(top)),h('td',{class:'num'},v.length,h('div',{class:'bar'},h('i',{style:'width:'+Math.round(100*v.length/mx)+'%'}))),h('td',0,h('span',{class:'pill'},stOf(c.id))))}))),
  na.filter(c=>!st.area||c.domain===st.area).length&&st.sub==='all'&&!st.tag?h('div',{class:'note',style:'border-left:3px solid var(--warn)'},na.map(c=>'Not assessed: '+c.title+' ('+c.id+'). '+c.reason)):null]}
function tagChips(f,small){if(f.tags===null)return h('span',{class:'tag none'},'tags n/a');const ks=Object.keys(f.tags);return ks.length?ks.map(k=>h('span',{class:'tag',title:'Filter by this tag',onclick:e=>{e.stopPropagation();st.tag={k,v:f.tags[k]};draw()}},k+'='+f.tags[k])):h('span',{class:'tag none'},'no tags')}
function drawer(extra){const c=D.checks.find(x=>x.id===st.sel);
 if(!c)return [h('h2',0,'DETAIL'),h('p',{style:'color:var(--muted)'},'Select a check to see what was found, the resources and their Azure tags, and to add status and notes.')];
 const v=vis(c);
 return [h('h2',0,c.id),h('h3',0,c.title),h('div',{style:'display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px'},h('span',{class:'pill'},dn(c.domain)),h('span',{class:'pill'},c.conf+' confidence'),h('span',{class:'pill'},'not yet verified on a real tenant')),
  c.status!=='ran'?h('div',{class:'note'},'Not assessed, because: '+c.reason):null,
  v[0]?h('p',{style:'margin:0 0 6px'},v[0].msg):null,
  h('h2',0,'YOUR REVIEW'),
  h('div',{style:'display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:6px'},h('select',{'aria-label':'Status',onchange:e=>{store.set('st:'+c.id,e.target.value);draw()}},...STATUSES.map(s=>h('option',{selected:stOf(c.id)===s},s))),h('input',{type:'text',style:'width:100%','aria-label':'Owner',placeholder:'Owner (name or team)',value:ownOf(c.id),oninput:e=>store.set('own:'+c.id,e.target.value)})),
  h('textarea',{'aria-label':'Notes',placeholder:'Notes for this check, for example who you asked and what they said',style:'margin-top:6px',oninput:e=>store.set('note:'+c.id,e.target.value),onchange:()=>draw()},noteOf(c.id)),
  h('div',{class:'mini'},'Stored in this browser only in the mock-up. The real tool would save notes beside the report, keyed by finding fingerprint, so they survive a re-run.'),
  extra?extra(c):null,
  h('h2',0,'RESOURCES ('+v.length+')'),
  h('ul',{class:'res'},...v.slice(0,8).map(f=>h('li',0,h('span',{class:'rn'},f.name),' ',h('span',{class:'mini'},f.sub),h('div',0,tagChips(f)),h('input',{type:'text',placeholder:'Note on this resource','aria-label':'Note on '+f.name,style:'width:100%;margin-top:2px;font-size:12px',value:store.get('fn:'+f.fp,''),oninput:e=>store.set('fn:'+f.fp,e.target.value)})))),
  v.length>8?h('p',{class:'mini'},'+ '+(v.length-8)+' more in the Excel export'):null,
  h('h2',0,'WHAT A PERSON MUST CONFIRM'),h('div',{class:'note'},D.help[c.domain]||'Review before acting.'),
  h('h2',0,'EVIDENCE'),h('div',{class:'id'},'logic '+c.logic+'  fingerprint '+(v[0]?v[0].fp:'-'))]}
function tagsPanel(){const fs=allVis(),withTags=fs.filter(f=>f.tags!==null);
 const cov=D.tagKeys.map(k=>[k,withTags.filter(f=>f.tags[k]).length]);
 const g=st.group,groups={};withTags.forEach(f=>{const v=f.tags[g]||'(none)';(groups[v]??=[]).push(f)});
 const ge=Object.entries(groups).sort((a,b)=>b[1].length-a[1].length),mx=Math.max(1,ge[0]?ge[0][1].length:1);
 return [h('h2',0,'TAG COVERAGE ON FLAGGED RESOURCES ('+withTags.length+')'),
  ...cov.map(([k,n])=>h('div',{style:'display:grid;grid-template-columns:90px 1fr 50px;gap:8px;align-items:center;padding:2px 0'},h('span',{class:'rn'},k),h('div',{class:'bar',style:'height:10px'},h('i',{style:'width:'+(withTags.length?100*n/withTags.length:0)+'%'})),h('em',{style:'font-style:normal;text-align:right'},withTags.length?Math.round(100*n/withTags.length)+'%':'-'))),
  h('div',{class:'mini',style:'margin-top:6px'},'Mock-up coverage covers only resources that have a finding. A real tag-hygiene check would read tags across the whole inventory, and which tags are required would be set by you in the config.'),
  h('h2',0,'GROUP FINDINGS BY'),h('div',{style:'display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px'},...D.tagKeys.map(k=>h('button',{'aria-pressed':g===k,onclick:()=>{st.group=k;draw()}},k))),
  ...ge.map(([v,l])=>h('div',{class:'abars'},h('div',{class:'r',role:'button',tabindex:0,title:'Filter findings to this tag value',onclick:()=>{st.tag=st.tag&&st.tag.k===g&&st.tag.v===v?null:{k:g,v};draw()}},h('span',{style:(st.tag&&st.tag.k===g&&st.tag.v===v)?'font-weight:700':''},v==='(none)'?'(not tagged)':g+'='+v),h('div',{class:'bar'},h('i',{style:'width:'+Math.max(2,100*l.length/mx)+'%'})),h('em',0,l.length))))]}
function coverageStrip(){return [h('div',{class:'cov'},...D.checks.map(c=>h('div',{class:'sq'+(c.status!=='ran'?' na':''),title:c.id+': '+(c.status==='ran'?c.findings.length+' findings':'not assessed')}))),h('div',{class:'mini',style:'margin-top:6px'},'One square per check. Hatched means not assessed. A count of zero never stands in for that.')]}
function printHead(title){return mount(h('div',{class:'printonly'}),()=>[h('h1',{style:'margin:0 0 2px;font-size:22px'},title),h('div',{class:'mini'},'Prepared '+new Date().toISOString().slice(0,10)+'. '+filterText()+'. Synthetic data.')])}
"""

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>F-CAT</title><style>{css}</style></head><body><div id="app"></div>
<script>const BRAND={{name:'Your Company',tag:'FinOps assessment',accent:'#1f5fbf',logo:null}};const D=/*DATA*/;{js}
{body}
</script></body></html>"""

# -------- A: single-page dashboard (summary on top, workbench below)
A = r"""
const app=$('#app');app.append(topBar(),printHead('Azure FinOps assessment'));
const sum=h('section',{class:'wrap',style:'padding-bottom:0'});
const head=mount(h('div'),()=>[h('p',{class:'headline'},headlineText())]);
const kp=mount(h('div'),kpis);
const mapOpen=store.get('mapopen',true);
const mapBody=mount(h('div'),()=>mapOpen?treemap(260):[]);
const mid=h('div',{class:'row2'},h('div',{class:'pane'},h('h2',0,'WHERE IT CONCENTRATES (click to filter)'),mount(h('div'),areaBars),h('h2',0,'SEVERITY'),mount(h('div'),sevBar)),
 h('div',{class:'pane'},h('h2',0,'MAP OF SUBSCRIPTIONS AND AREAS'),mapBody),
 h('div',{class:'pane'},h('h2',0,'DID EVERY CHECK RUN?'),mount(h('div'),coverageStrip),h('h2',0,'AZURE TAGS ON THE FLAGGED RESOURCES'),mount(h('div'),tagsPanel)));
sum.append(head,kp,mid);
const main=h('main',{class:'wrap'});const g=h('div',{class:'grid3'});
const side=mount(h('aside',{class:'pane side'}),sideFilters),q=mount(h('section',{class:'pane'}),queue),dr=mount(h('aside',{class:'pane',id:'drawer'}),()=>drawer());
g.append(side,q,dr);main.append(g);app.append(sum,main);draw();
"""

# -------- B: tabbed
B = r"""
const app=$('#app');app.append(topBar(),printHead('Azure FinOps assessment'));const base=R.length;
const tabs=[['Overview','ov'],['Findings','fi'],['Map','mp'],['Tags','tg'],['Coverage and gaps','cv']];let tab=store.get('tab','ov');
const bar=h('nav',{class:'tabs',role:'tablist'});const body=h('main',{class:'wrap'});app.append(bar,body);
const paintTabs=()=>bar.replaceChildren(...tabs.map(([l,k])=>h('button',{role:'tab','aria-selected':tab===k,onclick:()=>{tab=k;store.set('tab',k);paintTabs();build()}},l)));
function build(){R.length=base;body.replaceChildren();
 if(tab==='ov'){body.append(h('p',{class:'headline'},headlineText()),mount(h('div'),kpis),
  h('div',{class:'row2'},h('div',{class:'pane'},h('h2',0,'WHERE IT CONCENTRATES'),mount(h('div'),areaBars),h('h2',0,'SEVERITY'),mount(h('div'),sevBar)),
   h('div',{class:'pane'},h('h2',0,'START HERE'),mount(h('div'),()=>rows().sort((a,b)=>score(b)-score(a)).slice(0,4).map(({c,v})=>h('div',{class:'note',style:'cursor:pointer',onclick:()=>{st.sel=c.id;tab='fi';paintTabs();build()}},h('b',0,v.length+' × '+c.title),h('div',{class:'mini'},c.id+' • '+stOf(c.id)))))),
   h('div',{class:'pane'},h('h2',0,'MAP'),mount(h('div'),()=>treemap(240)))))}
 if(tab==='fi'){body.append(h('div',{class:'grid3'},mount(h('aside',{class:'pane side'}),sideFilters),mount(h('section',{class:'pane'}),queue),mount(h('aside',{class:'pane',id:'drawer'}),()=>drawer())))}
 if(tab==='mp'){body.append(h('div',{class:'pane'},h('h2',0,'FINDINGS BY SUBSCRIPTION AND AREA'),mount(h('div'),()=>treemap(420))),h('div',{class:'pane'},mount(h('div'),()=>{const rs=rows().sort((a,b)=>score(b)-score(a));return [h('h2',0,(st.sub==='all'?'ALL SUBSCRIPTIONS':st.sub.toUpperCase())+(st.area?' / '+dn(st.area).toUpperCase():'')),h('table',0,h('tbody',0,...rs.map(({c,v})=>h('tr',0,h('td',0,c.title,h('div',{class:'id'},c.id)),h('td',{class:'num'},v.length)))))]})))}
 if(tab==='tg'){body.append(h('div',{class:'row2'},h('div',{class:'pane'},mount(h('div'),tagsPanel)),h('div',{class:'pane'},mount(h('div'),()=>{const fs=allVis().sort((a,b)=>SEV[b.sev]-SEV[a.sev]).slice(0,14);return [h('h2',0,'FINDINGS IN THIS SELECTION ('+allVis().length+')'),h('ul',{class:'res'},...fs.map(f=>h('li',0,h('span',{class:'rn'},f.name),' ',sevIcon(f.sev),h('div',{class:'mini'},f.c.title),h('div',0,tagChips(f)))))]}))))}
 if(tab==='cv'){body.append(h('div',{class:'row2'},h('div',{class:'pane'},h('h2',0,'DID EVERY CHECK RUN?'),mount(h('div'),coverageStrip)),h('div',{class:'pane'},h('h2',0,'WHAT IS MISSING'),h('ul',{style:'padding-left:18px;margin:0;color:var(--ink2)'},...na.map(c=>h('li',0,c.id+' not assessed: '+c.reason)),h('li',0,'Cost data: not collected, so no money figures and no cost-based checks.'),h('li',0,D.caps.filter(c=>c.kind==='customer').length+' maturity capabilities wait for answers from your team.')))))}
 draw()}
paintTabs();build();
"""

# -------- C: audience toggle and report builder
C = r"""
const app=$('#app');let aud=store.get('aud','exec');const basket=new Set(store.get('basket',[]));
const saveB=()=>store.set('basket',[...basket]);
const audBtn=h('span',{class:'noprint',role:'group','aria-label':'Audience'},h('button',{'aria-pressed':aud==='exec',onclick:()=>set('exec')},'Executive'),' ',h('button',{'aria-pressed':aud==='eng',onclick:()=>set('eng')},'Engineer'));
function set(a){aud=a;store.set('aud',a);$$('button',audBtn).forEach((b,i)=>b.setAttribute('aria-pressed',(i===0)===(a==='exec')));$('#exec').classList.toggle('hide',a!=='exec');$('#eng').classList.toggle('hide',a!=='eng')}
app.append(topBar(audBtn));
const pin=c=>h('label',{class:'opt noprint',style:'margin:8px 0'},h('input',{type:'checkbox',checked:basket.has(c.id),onchange:e=>{e.target.checked?basket.add(c.id):basket.delete(c.id);saveB();draw()}}),'Add this check to the report');
const execV=h('main',{class:'wrap',id:'exec'},h('p',{class:'headline'},headlineText()),mount(h('div'),kpis),
 h('div',{class:'row2'},h('div',{class:'pane'},h('h2',0,'THREE THINGS TO KNOW'),mount(h('div'),()=>{const rs=rows().sort((a,b)=>score(b)-score(a)).slice(0,3);return rs.map(({c,v})=>h('div',{class:'note'},h('b',0,v.length+' × '+c.title),h('div',{class:'mini'},D.help[c.domain]||''),pin(c)))})),
  h('div',{class:'pane'},h('h2',0,'WHERE IT CONCENTRATES'),mount(h('div'),areaBars),h('h2',0,'MAP'),mount(h('div'),()=>treemap(220))),
  h('div',{class:'pane'},h('h2',0,'WHAT WE COULD NOT SEE'),h('ul',{style:'padding-left:18px;margin:0;color:var(--ink2)'},...na.map(c=>h('li',0,c.title+': '+c.reason)),h('li',0,'Cost data was not collected, so no money figures.'),h('li',0,D.caps.filter(c=>c.kind==='customer').length+' maturity topics need answers from your team.')),h('h2',0,'TAGS'),mount(h('div'),tagsPanel))));
const engV=h('main',{class:'wrap hide',id:'eng'},h('div',{class:'grid3'},mount(h('aside',{class:'pane side'}),sideFilters),mount(h('section',{class:'pane'}),queue),mount(h('aside',{class:'pane',id:'drawer'}),()=>drawer(pin))));
/* report basket: what the PDF contains */
const rep=h('section',{class:'wrap'},mount(h('div',{class:'pane'}),()=>[h('div',{class:'noprint'},h('h2',0,'REPORT BASKET'),h('p',{class:'mini',style:'margin:0 0 6px'},basket.size?basket.size+' check'+(basket.size===1?'':'s')+' will appear in the PDF, after the summary. Tick checks in either view.':'Nothing added yet. Tick “Add this check to the report” in either view. The PDF always starts with the summary.'),h('div',{style:'display:flex;gap:8px;flex-wrap:wrap;align-items:center'},h('input',{type:'text','aria-label':'Report title',value:store.get('title','Azure FinOps assessment'),oninput:e=>store.set('title',e.target.value),style:'min-width:240px'}),h('input',{type:'text','aria-label':'Prepared for',placeholder:'Prepared for (customer)',value:store.get('for',''),oninput:e=>store.set('for',e.target.value)}),h('button',{onclick:()=>window.print()},'Export PDF'),h('button',{onclick:()=>{basket.clear();saveB();draw()}},'Empty basket'))),
  h('div',{class:'printonly basket-print'},h('h1',{style:'margin:0;font-size:24px'},store.get('title','Azure FinOps assessment')),h('div',{class:'mini'},(store.get('for','')?'Prepared for '+store.get('for','')+'. ':'')+'Prepared '+new Date().toISOString().slice(0,10)+'. Synthetic data.'),h('p',{class:'headline',style:'margin:10px 0'},headlineText()),
   ...[...basket].map(id=>D.checks.find(c=>c.id===id)).filter(Boolean).map(c=>h('div',{class:'pane',style:'margin:8px 0'},h('h3',0,c.title+' ('+c.id+')'),h('div',{class:'mini'},c.findings.length+' findings. Status: '+stOf(c.id)+(ownOf(c.id)?'. Owner: '+ownOf(c.id):'')),noteOf(c.id)?h('p',0,noteOf(c.id)):null,h('div',{class:'mini'},'Examples: '+c.findings.slice(0,6).map(f=>f.name).join(', ')+(c.findings.length>6?' and '+(c.findings.length-6)+' more':'')),h('div',{class:'note'},D.help[c.domain]||'')))) ]));
app.append(execV,engV,rep);
const st0=document.createElement('style');st0.textContent='@media print{#exec,#eng{display:none!important}}';document.head.append(st0);
set(aud);draw();
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.dumps(build(), separators=(",", ":")).replace("</", "<\\/")
    for name, body in (("A-dashboard", A), ("B-tabs", B), ("C-audience-report", C)):
        (OUT / f"{name}.html").write_text(PAGE.format(css=CSS, js=JS, body=body).replace("/*DATA*/", data))
    (OUT / "index.html").write_text(
        "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>F-CAT front-end round 2</title>"
        "<body style='font:16px/1.5 system-ui;max-width:720px;margin:24px auto;padding:0 16px'><h1>Front-end round 2</h1><ol>"
        "<li><a href=A-dashboard.html>A: one-page dashboard</a>, summary on top, workbench below.</li>"
        "<li><a href=B-tabs.html>B: tabs</a>, Overview, Findings, Map, Tags, Coverage.</li>"
        "<li><a href=C-audience-report.html>C: audience toggle and report basket</a>, Executive or Engineer, pick what goes in the PDF.</li></ol>"
        "<p>Synthetic data and synthetic tags. Notes and branding are kept in your browser only.</p></body>"
    )
    print("wrote", OUT)


if __name__ == "__main__":
    main()
