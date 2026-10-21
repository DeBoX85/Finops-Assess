"""CSS and JavaScript of the interactive dashboard (backlog 39). Kept as strings so the report stays one self-contained file.
Every value from the report reaches the page through textContent (the h() helper builds text nodes), never through innerHTML."""

CSS = r"""
:root{--bg:#eef1f5;--pane:#fff;--ink:#14202e;--ink2:#46556a;--muted:#5d6b7e;--line:#d6dde6;--acc:#1f5fbf;--ok:#0b6b2e;--warn:#8a5700;--bad:#a12626;--r:8px}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0e141c;--pane:#16202c;--ink:#e6edf6;--ink2:#b3c0d1;--muted:#8e9db1;--line:#2a3a4d;--acc:#7fb0f5;--ok:#4cc27a;--warn:#f2b84b;--bad:#f08a8a}}
:root[data-theme=dark]{--bg:#0e141c;--pane:#16202c;--ink:#e6edf6;--ink2:#b3c0d1;--muted:#8e9db1;--line:#2a3a4d;--acc:#7fb0f5;--ok:#4cc27a;--warn:#f2b84b;--bad:#f08a8a}
:root{--accbg:color-mix(in srgb,var(--acc) 13%,var(--pane))}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
button,input,select,textarea{font:inherit;color:var(--ink);background:var(--pane);border:1px solid var(--line);border-radius:var(--r);padding:5px 10px}
button{cursor:pointer}button:hover{border-color:var(--acc)}button[aria-pressed=true],button[aria-current=page]{background:var(--accbg);border-color:var(--acc)}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
header.top{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:10px 16px;background:var(--pane);border-bottom:1px solid var(--line)}
.brand{display:flex;gap:12px;align-items:center;min-width:0;margin-right:auto}.brand img{max-height:40px;max-width:140px}
h1.bn{font-size:16px;font-weight:700;line-height:1.2;margin:0}.bt{color:var(--muted);font-size:13px}
nav{display:flex;gap:6px;flex-wrap:wrap}.tools{display:flex;gap:6px;flex-wrap:wrap}
.chip{border:1px solid var(--line);border-radius:999px;padding:1px 10px;font-size:12px;color:var(--ink2);white-space:nowrap}.chip.ok{color:var(--ok);border-color:currentColor}.chip.bad{color:var(--bad);border-color:currentColor;font-weight:600}
main{max-width:1240px;margin:0 auto;padding:14px 16px 40px}.view{display:none}.view.on{display:block}
.pane{background:var(--pane);border:1px solid var(--line);border-radius:var(--r);padding:14px;margin-bottom:12px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:13px;letter-spacing:.04em;color:var(--muted);margin:0 0 8px;font-weight:600;text-transform:none}h3{font-size:15px;margin:10px 0 4px}
.headline{font-size:19px;line-height:1.35;margin:0 0 10px}.mini{font-size:12px;color:var(--muted)}.note{background:var(--accbg);border-radius:var(--r);padding:8px 10px;margin:8px 0;color:var(--ink2)}
.grid{display:grid;gap:12px}.g3{grid-template-columns:repeat(3,minmax(0,1fr))}.g2{grid-template-columns:repeat(2,minmax(0,1fr))}.find{grid-template-columns:210px minmax(0,1fr) minmax(0,360px);align-items:start}
.stat{display:flex;gap:18px;flex-wrap:wrap}.stat div b{display:block;font-size:26px;line-height:1.1;font-variant-numeric:tabular-nums}.stat span{font-size:12px;color:var(--muted)}
.sev{display:inline-flex;gap:5px;align-items:center;font-size:12px}.sev i{width:10px;height:10px;display:inline-block}.sev.high i{background:var(--bad);transform:rotate(45deg)}.sev.medium i{background:var(--warn);border-radius:50%}.sev.low i{border:2px solid var(--ink2);border-radius:50%}.sev.info i{border:1.5px dashed var(--muted);border-radius:2px}
.pill{font-size:11px;border:1px solid var(--line);border-radius:4px;padding:0 6px;color:var(--ink2);white-space:nowrap}
ul.plain{margin:0;padding-left:18px}ul.plain li{margin:3px 0}
table{border-collapse:collapse;width:100%}th{text-align:left;font-size:12px;color:var(--muted);padding:6px 8px;border-bottom:1px solid var(--line)}td{padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top;overflow-wrap:anywhere}
.tw{overflow-x:auto}.id{font:12px ui-monospace,Menlo,Consolas,monospace;color:var(--muted);overflow-wrap:anywhere}
label.opt{display:flex;gap:8px;align-items:center;padding:3px 0;cursor:pointer}label.opt .n{margin-left:auto;color:var(--muted);font-variant-numeric:tabular-nums}
.chk{display:block;width:100%;text-align:left;border:1px solid var(--line);border-radius:var(--r);padding:8px 10px;margin:0 0 6px;background:var(--pane)}.chk[aria-expanded=true]{border-color:var(--acc)}
.chk .t{font-weight:600}.fl{display:block;width:100%;text-align:left;border:0;border-top:1px solid var(--line);border-radius:0;padding:6px 4px 6px 14px}.fl[aria-current=true]{background:var(--accbg)}
.kv{display:grid;grid-template-columns:minmax(80px,130px) minmax(0,1fr);gap:3px 10px;margin:6px 0}.kv dt{color:var(--muted);font-size:12px}.kv dd{margin:0;overflow-wrap:anywhere}
.st{display:inline-flex;gap:6px;align-items:center;font-size:12px}.st i{width:11px;height:11px;display:inline-block;border-radius:50%;flex:none}.st.ran i{background:var(--ok)}.st.not_assessed i,.st.skipped i{border:2px solid var(--warn)}.st.failed i{background:var(--bad);transform:rotate(45deg);border-radius:0}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0}
.chg{display:grid;grid-template-columns:110px minmax(0,1fr);gap:2px 10px;padding:6px 0;border-top:1px solid var(--line)}.chg .k{font-size:12px;color:var(--ink2)}
.mat{display:grid;grid-template-columns:minmax(0,1.4fr) 140px minmax(0,1fr);gap:6px 10px;align-items:center;padding:5px 0;border-top:1px solid var(--line)}
.trk{position:relative;height:24px}.trk::before{content:"";position:absolute;left:8%;right:8%;top:11px;height:2px;background:var(--line)}
.trk span{position:absolute;top:0;width:24px;height:24px;margin-left:-12px;display:grid;place-items:center;font-size:11px;border-radius:50%;border:2px solid var(--line);background:var(--pane);color:var(--muted)}
.trk .cur{background:var(--ink);color:var(--pane);border-color:var(--ink)}.trk .tgt{border:2px dashed var(--acc);color:var(--acc)}.trk .cur.tgt{border-style:solid;box-shadow:0 0 0 3px var(--accbg)}
.mst{font-size:13px}.mst.below{color:var(--bad);font-weight:600}.mst.needs_input{color:var(--warn)}
details.dom{border:1px solid var(--line);border-radius:var(--r);padding:6px 12px;margin-bottom:8px}details.dom>summary{cursor:pointer;font-weight:600}
.keys{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--ink2);margin:6px 0}.keys i{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:5px;vertical-align:-2px}.keys .a{background:var(--ink)}.keys .b{border:2px dashed var(--acc)}.keys .c{border:2px solid var(--line)}
textarea{width:100%;min-height:56px;resize:vertical}
.stat .k{border:0;background:none;text-align:left;padding:6px 10px;margin:-6px -10px;border-radius:var(--r)}.stat .k:hover,.stat .k:focus-visible{background:var(--accbg)}
.stat .k b{display:block;font-size:26px;line-height:1.1;font-variant-numeric:tabular-nums}.stat .k span{font-size:12px;color:var(--muted)}
.abars{display:grid;gap:2px}.abars .r{display:grid;grid-template-columns:minmax(110px,210px) minmax(0,1fr) 36px;gap:10px;align-items:center;width:100%;border:0;background:none;text-align:left;padding:5px 6px}
.abars .r:hover,.abars .r:focus-visible{background:var(--accbg)}.abars .bar{height:10px;background:var(--line);border-radius:5px;overflow:hidden;display:block}.abars .bar i{display:block;height:100%;background:var(--acc)}.abars b{text-align:right;font-variant-numeric:tabular-nums}
.tm{display:flex;gap:10px;flex-wrap:wrap}.sp{flex:1 1 230px;min-width:0;border:1px solid var(--line);border-radius:var(--r);padding:6px}
.sph{display:flex;justify-content:space-between;gap:8px;width:100%;border:0;background:none;font-weight:600;padding:4px 6px;text-align:left;overflow-wrap:anywhere}.sph em{font-style:normal;font-weight:400;color:var(--muted);font-size:12px;white-space:nowrap}.sph:hover{background:var(--accbg)}
.spb{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}
.tile{flex:1 1 96px;min-width:0;display:flex;flex-direction:column;gap:2px;text-align:left;padding:7px 9px;background:var(--accbg);border:1px solid transparent;position:relative;overflow:hidden;min-height:64px}.tile:hover,.tile:focus-visible{border-color:var(--acc)}
.tile span{font-size:12px;color:var(--ink2);overflow-wrap:anywhere}.tile b{font-size:18px;font-variant-numeric:tabular-nums}.tile i{position:absolute;left:0;bottom:0;height:4px;background:var(--acc)}
.covrow{display:grid;grid-template-columns:minmax(80px,150px) minmax(0,1fr) 54px;gap:10px;align-items:center;padding:3px 0}.covrow .bar{height:10px;background:var(--line);border-radius:5px;overflow:hidden}.covrow .bar i{display:block;height:100%;background:var(--acc)}.covrow em{font-style:normal;text-align:right;font-variant-numeric:tabular-nums}
.tag{display:inline-block;border:1px solid var(--line);border-radius:4px;padding:0 6px;margin:2px 4px 2px 0;font:12px ui-monospace,Menlo,Consolas,monospace}.src{display:inline-block;border-left:4px solid var(--acc);padding:2px 8px;background:var(--accbg);border-radius:0 4px 4px 0;margin-right:6px}
.var{display:inline-flex;gap:5px;margin:2px 6px 2px 0;border:1px solid var(--line);border-radius:4px;padding:0 6px;font:12px ui-monospace,Menlo,Consolas,monospace}.var em{font-style:normal;color:var(--muted)}
.tagrow{padding:6px 0;border-top:1px solid var(--line)}
.crumb{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin:0 0 10px;font-size:13px}.crumb .sep{color:var(--muted)}.crumb button{padding:2px 10px;border-radius:999px;font-size:13px}.crumb .x{color:var(--muted)}
@media print{.tile,.sp{break-inside:avoid}.crumb{display:none}}
.cover{display:none}
@media (max-width:900px){.g3,.g2,.find{grid-template-columns:minmax(0,1fr)}.mat{grid-template-columns:minmax(0,1fr) 120px}.mat .mst{grid-column:1/-1}}
@page{margin:16mm 14mm;@bottom-center{content:"Page " counter(page) " of " counter(pages)}}
@media print{body{background:#fff;color:#000;font-size:11pt}header.top,.noprint{display:none!important}.view{display:block!important;break-before:page}.view:first-of-type{break-before:auto}
.cover{display:block;break-after:page;padding-top:30mm}.cover h1{font-size:30pt}.pane{border-color:#999;break-inside:avoid}.chg,.mat,tr{break-inside:avoid}main{padding:0;max-width:none}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}.chk{break-inside:avoid}}
"""

JS = r"""
const $=(s,r=document)=>r.querySelector(s);
function h(t,a,...k){const e=document.createElement(t);for(const[x,v]of Object.entries(a||{})){if(x==='class')e.className=v;else if(x.startsWith('on'))e.addEventListener(x.slice(2),v);else if(v!==false&&v!=null)e.setAttribute(x,v===true?'':v)}for(const c of k.flat(3))if(c!=null&&c!==false)e.append(c.nodeType?c:document.createTextNode(String(c)));return e}
const OP=D.audience==='operator';
const store={get(k,d){try{const v=localStorage.getItem('fcat-dash:'+D.run.fingerprint+':'+k);return v===null?d:JSON.parse(v)}catch(e){return d}},set(k,v){try{localStorage.setItem('fcat-dash:'+D.run.fingerprint+':'+k,JSON.stringify(v))}catch(e){}}};
const SEV={high:3,medium:2,low:1,info:0},SEVL=['high','medium','low','info'];
const dn=d=>D.domains[d]||d;
const sevIcon=s=>h('span',{class:'sev '+s},h('i'),s);
const stat=(s,t)=>h('span',{class:'st '+s},h('i'),t||s.replace('_',' '));
const st={view:store.get('view','summary'),sev:new Set(SEVL),area:null,sub:'all',q:'',open:null,sel:null};
const byCheck=id=>D.checks.find(c=>c.id===id);
const visible=()=>D.findings.filter(f=>st.sev.has(f.sev)&&(!st.area||byCheck(f.check).domain===st.area)&&(st.sub==='all'||f.sub===st.sub)&&(!st.q||(f.msg+' '+f.res+' '+f.check).toLowerCase().includes(st.q.toLowerCase())));
const ranN=D.checks.filter(c=>c.status==='ran').length,naN=D.checks.filter(c=>c.status==='not_assessed').length,skN=D.checks.filter(c=>c.status==='skipped').length,faN=D.checks.filter(c=>c.status==='failed').length;
const TAGIDS=['TAG-DISC-01','TAG-COV-01','TAG-CASE-01','TAG-VAL-01','TAG-RG-01'],HASTAG=D.checks.some(c=>TAGIDS.includes(c.id)),fnd=id=>D.findings.filter(f=>f.check===id);
const VIEWS=[['summary','Summary'],['findings','Findings'],['coverage','Coverage'],...(HASTAG?[['tags','Tags']]:[]),...(D.changes||D.maturity?[['progress','Progress']]:[]),['audit','Self-audit']];
let rerender=()=>{};
function go(v,after){st.view=v;store.set('view',v);if(after)after();rerender()}
function topBar(){
 return h('header',{class:'top'},h('div',{class:'brand'},D.logo?h('img',{alt:'',src:D.logo}):null,h('div',0,h('h1',{class:'bn'},D.title),D.subtitle?h('div',{class:'bt'},D.subtitle):null)),
  h('nav',{'aria-label':'Sections'},...VIEWS.map(([k,l])=>h('button',{'aria-current':st.view===k?'page':null,onclick:()=>go(k)},l))),
  h('div',{class:'tools'},OP?/*OP*/h('span',{class:'chip'},'Operator view')/*ENDOP*/:null,h('span',{class:'chip '+(D.audit.status==='pass'?'ok':'bad')},'Self-audit: '+D.audit.status),
   h('button',{onclick:()=>{const r=document.documentElement,d=r.dataset.theme==='dark'||(!r.dataset.theme&&matchMedia('(prefers-color-scheme:dark)').matches);r.dataset.theme=d?'light':'dark'}},'Light / dark'),
   h('button',{onclick:()=>print()},'Print or save as PDF')))}
function topFive(){
 const m={};D.findings.forEach(f=>{const x=m[f.check]||(m[f.check]={n:0,s:0});x.n++;x.s=Math.max(x.s,SEV[f.sev])});
 return Object.entries(m).sort((a,b)=>b[1].s-a[1].s||b[1].n-a[1].n).slice(0,5)}
const subL=s=>s==='-'?'Tenant-wide':s;
function drill(o){go('findings',()=>{st.sev=new Set(o.sev||SEVL);st.area=o.area||null;st.sub=o.sub||'all';st.q='';st.open=o.open||null;st.sel=null})}
function areaBars(){const m={};D.findings.forEach(f=>{const d=byCheck(f.check).domain;m[d]=(m[d]||0)+1});const es=Object.entries(m).sort((a,b)=>b[1]-a[1]);if(!es.length)return h('p',{class:'mini'},'No items to show.');const mx=es[0][1];
 return h('div',{class:'abars'},...es.map(([d,n])=>h('button',{class:'r',title:'Show these items',onclick:()=>drill({area:d})},h('span',0,dn(d)),h('span',{class:'bar'},h('i',{style:'width:'+Math.max(3,100*n/mx)+'%'})),h('b',0,n))))}
function treemap(){const cell={};D.findings.forEach(f=>{const d=byCheck(f.check).domain;cell[f.sub]=cell[f.sub]||{};cell[f.sub][d]=(cell[f.sub][d]||0)+1});
 const subs=Object.keys(cell).sort(),tot=s=>Object.values(cell[s]).reduce((a,b)=>a+b,0),mx=Math.max(1,...subs.flatMap(s=>Object.values(cell[s])));
 return h('div',{class:'tm'},...subs.map(s=>h('div',{class:'sp'},h('button',{class:'sph',title:'Show everything in this subscription',onclick:()=>drill({sub:s})},h('span',0,subL(s)),h('em',0,tot(s)+(tot(s)===1?' item':' items'))),
  h('div',{class:'spb'},...Object.entries(cell[s]).sort((a,b)=>b[1]-a[1]).map(([d,n])=>h('button',{class:'tile',title:dn(d)+' in '+subL(s)+': '+n,onclick:()=>drill({sub:s,area:d})},h('span',0,dn(d)),h('b',0,n),h('i',{style:'width:'+Math.max(6,100*n/mx)+'%'})))))))}
function mapPane(){return D.findings.length?h('div',{class:'pane'},h('h2',0,'MAP OF SUBSCRIPTIONS AND AREAS'),treemap(),h('p',{class:'mini'},'One panel per subscription; the bar on each tile shows how many items, compared with the busiest tile. Click a tile to see those items, or a panel title to see the whole subscription. On the Findings page you can step back.')):null}
function crumbs(){const parts=[];
 if(st.sub!=='all')parts.push(['Subscription: '+subL(st.sub),()=>{st.sub='all'}]);
 if(st.area)parts.push(['Area: '+dn(st.area),()=>{st.area=null}]);
 if(st.sev.size<SEVL.length)parts.push(['Severity: '+SEVL.filter(x=>st.sev.has(x)).join(', '),()=>{st.sev=new Set(SEVL)}]);
 if(st.q)parts.push(['Search: '+st.q,()=>{st.q=''}]);
 const sel=D.findings.find(x=>x.fp+x.res===st.sel),ck=st.open&&byCheck(st.open);
 return h('nav',{class:'crumb noprint','aria-label':'Where you are'},h('button',{onclick:()=>go('summary')},'Summary'),h('span',{class:'sep'},'>'),h('span',0,'Findings'),
  ...parts.flatMap(([l,fn])=>[h('span',{class:'sep'},'>'),h('button',{title:'Remove this filter',onclick:()=>{fn();st.open=null;st.sel=null;rerender()}},l+'  \u00d7')]),
  ck?[h('span',{class:'sep'},'>'),h('span',0,ck.title)]:null,sel?[h('span',{class:'sep'},'>'),h('span',0,sel.name)]:null,
  parts.length?h('button',{class:'x',onclick:()=>{st.sub='all';st.area=null;st.sev=new Set(SEVL);st.q='';st.open=null;st.sel=null;rerender()}},'Clear all'):null)}
function summary(){
 const n=D.findings.length,sv=SEVL.map(s=>[s,D.findings.filter(f=>f.sev===s).length]);
 return h('div',0,
  h('div',{class:'pane'},h('p',{class:'headline'},n===0?'The checks that ran found nothing to review. '+(naN+skN?naN+skN+' checks did not run, so that is not a clean bill of health.':''):n+' items to review from '+ranN+' checks that ran. '+(naN+skN+faN?(naN+skN+faN)+((naN+skN+faN)===1?' check could not run and is':' checks could not run and are')+' listed as not assessed.':'Every check ran.')),
   h('div',{class:'stat'},...sv.map(([s,k])=>h('button',{class:'k',title:'Show these items',onclick:()=>drill({sev:[s]})},h('b',0,k),h('span',0,sevIcon(s)))),h('button',{class:'k',title:'See which checks ran',onclick:()=>go('coverage')},h('b',0,ranN),h('span',0,'checks ran')),h('button',{class:'k',title:'See what was not assessed',onclick:()=>go('coverage')},h('b',0,naN+skN+faN),h('span',0,'not assessed'))),
   h('div',{class:'note'},'F-CAT only reads. It recommends and never changes anything in Azure. Each item is a prompt to check with the owner, not an instruction.')),
  h('div',{class:'grid g2'},
   h('div',{class:'pane'},h('h2',0,'WHERE TO LOOK FIRST'),topFive().length?h('ul',{class:'plain'},...topFive().map(([id,x])=>h('li',0,h('button',{onclick:()=>go('findings',()=>{st.open=id;st.area=null;st.sev=new Set(SEVL)})},byCheck(id).title),' ',h('span',{class:'mini'},x.n+' item'+(x.n>1?'s':'')+', highest '+SEVL[3-Math.max(...D.findings.filter(f=>f.check===id).map(f=>SEV[f.sev]))])))):h('p',{class:'mini'},'Nothing to list.')),
   h('div',{class:'pane'},h('h2',0,'WHERE THE ITEMS CONCENTRATE'),areaBars())),mapPane(),h('div',{class:'pane'},h('h2',0,'WHAT WE COULD NOT ASSESS'),naN+skN+faN?h('ul',{class:'plain'},...D.checks.filter(c=>c.status!=='ran').map(c=>h('li',0,h('b',0,c.title),': ',c.plain))):h('p',{class:'mini'},'Every check ran.')),
  h('div',{class:'pane'},h('h2',0,'WHAT THIS RUN LOOKED AT'),h('p',{class:'mini'},D.scopeText+' Run '+D.run.started.slice(0,10)+'. Report fingerprint '+D.run.fingerprint+'.')))}
function side(){
 const dom=[...new Set(D.checks.map(c=>c.domain))],subs=[...new Set(D.findings.map(f=>f.sub))].sort();
 return h('aside',{class:'pane','aria-label':'Filters'},h('h2',0,'SEARCH'),h('input',{type:'search',id:'q','aria-label':'Search findings',value:st.q,oninput:e=>{st.q=e.target.value;rerender(true)}}),
  h('h2',{style:'margin-top:12px'},'AREA'),...dom.map(d=>h('label',{class:'opt'},h('input',{type:'radio',name:'ar',checked:st.area===d,onclick:e=>{st.area=st.area===d?null:d;rerender()}}),dn(d),h('span',{class:'n'},D.findings.filter(f=>byCheck(f.check).domain===d).length))),
  h('h2',{style:'margin-top:12px'},'SEVERITY'),...SEVL.map(s=>h('label',{class:'opt'},h('input',{type:'checkbox',checked:st.sev.has(s),onchange:e=>{e.target.checked?st.sev.add(s):st.sev.delete(s);rerender()}}),sevIcon(s))),
  subs.length>1?[h('h2',{style:'margin-top:12px'},'SUBSCRIPTION'),h('select',{'aria-label':'Subscription',onchange:e=>{st.sub=e.target.value;rerender()}},h('option',{value:'all'},'All'),...subs.map(s=>h('option',{value:s,selected:st.sub===s},subL(s))))]:null)}
function queue(){
 const vf=visible(),ids=[...new Set(vf.map(f=>f.check))].sort((a,b)=>Math.max(...vf.filter(f=>f.check===b).map(f=>SEV[f.sev]))-Math.max(...vf.filter(f=>f.check===a).map(f=>SEV[f.sev]))||vf.filter(f=>f.check===b).length-vf.filter(f=>f.check===a).length);
 return h('section',{'aria-label':'Findings by check'},ids.length?ids.map(id=>{const c=byCheck(id),fl=vf.filter(f=>f.check===id),open=st.open===id;
  return h('div',0,h('button',{class:'chk','aria-expanded':open,onclick:()=>{st.open=open?null:id;rerender(true)}},h('span',{class:'t'},c.title),' ',h('span',{class:'pill'},fl.length+' item'+(fl.length>1?'s':'')),' ',h('span',{class:'pill'},c.conf+' confidence')),
   open?fl.map(f=>h('button',{class:'fl','aria-current':st.sel===f.fp+f.res,onclick:()=>{st.sel=f.fp+f.res;rerender(true)}},sevIcon(f.sev),' ',f.name)):null)}):h('div',{class:'pane'},'No findings match these filters.'))}
const kv=o=>Object.entries(o||{}).filter(([k,v])=>v!==null&&v!==undefined&&typeof v!=='object');
function drawer(){
 const f=D.findings.find(x=>x.fp+x.res===st.sel);
 if(!f)return h('aside',{class:'pane'},h('h2',0,'DETAIL'),h('p',{class:'mini'},'Pick an item to see what was found and what to check first.'));
 const c=byCheck(f.check),hp=D.help[c.domain]||D.help._;
 return h('aside',{class:'pane','aria-live':'polite'},h('h2',0,'DETAIL'),h('div',0,sevIcon(f.sev),' ',h('b',0,c.title)),h('p',0,f.msg),h('div',{class:'id'},f.res),
  h('h3',0,'Why it matters'),h('p',0,hp.why),h('h3',0,'What to check first'),h('p',0,hp.check),
  kv(f.details).length?[h('h3',0,'What we saw'),h('dl',{class:'kv'},...kv(f.details).flatMap(([k,v])=>[h('dt',0,k),h('dd',0,v)]))]:null,
  h('h3',0,'How sure we are'),h('p',{class:'mini'},c.conf+' confidence. '+c.validationText),
  OP?/*OP*/[h('h3',0,'Evidence (operator only)'),h('dl',{class:'kv'},h('dt',0,'Rule version'),h('dd',0,f.evidence.logic_hash||'n/a'),h('dt',0,'Fingerprint'),h('dd',0,f.fp),h('dt',0,'Data digests'),h('dd',0,Object.entries(f.evidence.snapshot_digests||{}).map(([k,v])=>k+' '+v).join(', ')||'n/a')),
   h('h3',0,'Your notes (kept in this browser only)'),h('textarea',{'aria-label':'Notes',oninput:e=>store.set('note:'+f.fp+f.res,e.target.value)},store.get('note:'+f.fp+f.res,'')),
   h('select',{'aria-label':'Review status',onchange:e=>store.set('status:'+f.fp+f.res,e.target.value)},...['To review','Confirmed','Ask owner',"Won't fix"].map(s=>h('option',{selected:store.get('status:'+f.fp+f.res,'To review')===s},s)))]/*ENDOP*/:null)}
function findings(){return h('div',0,crumbs(),h('div',{class:'grid find'},side(),queue(),drawer()))}
function coverage(){
 return h('div',{class:'pane'},h('h2',0,'DID EVERY CHECK RUN?'),h('p',{class:'mini'},'A check that did not run is not a pass. It is listed here with the reason.'),
  h('div',{class:'tw'},h('table',0,h('thead',0,h('tr',0,h('th',0,'Check'),h('th',0,'Status'),h('th',0,'What happened'),h('th',0,'Verified on a live tenant?'))),
   h('tbody',0,...D.checks.map(c=>h('tr',0,h('td',0,c.title,OP?/*OP*/h('div',{class:'id'},c.id)/*ENDOP*/:null),h('td',0,stat(c.status)),h('td',0,c.status==='ran'?c.count+' item'+(c.count===1?'':'s'):c.plain,OP&&c.reason?/*OP*/h('div',{class:'id'},c.reason)/*ENDOP*/:null),h('td',{class:'mini'},c.validationText)))))),
  OP&&D.collectorErrors.length?/*OP*/[h('h3',0,'Collector errors (operator only)'),h('ul',{class:'plain'},...D.collectorErrors.map(e=>h('li',0,e.collector+': '+e.error)))]/*ENDOP*/:null)}
const LV=['crawl','walk','run'],LX={crawl:16,walk:50,run:84},MS={below:'Below target',meets:'Meets target',above:'Above target',no_target:'No target set',needs_input:'Needs input'};
const LAB={new:'New',worse:'Worse',better:'Better',changed:'Changed',no_longer_reported:'No longer reported'};
const day=x=>typeof x==='string'&&x?x.slice(0,10):'not recorded';
function changes(){const CH=D.changes,c=CH.counts;
 return h('div',{class:'pane'},h('h2',0,'CHANGES SINCE THE PREVIOUS RUN'),h('p',{class:'mini'},'Previous run '+day(CH.older.started)+' ('+CH.older.findings+' findings). This run '+day(CH.newer.started)+' ('+CH.newer.findings+' findings).'),
  h('div',{class:'chips'},...[['New',c.new],['Worse',c.worse],['Changed',c.changed],['Better',c.better],['No longer reported',c.no_longer_reported],['Unchanged',c.unchanged]].map(([l,n])=>h('span',{class:'chip'},l+' '+n))),
  h('div',{class:'note'},'No longer reported does not prove a fix: the resource may be gone, the rule may have changed, or the scope may differ.'),
  CH.warnings.length?h('ul',{class:'plain mini'},...CH.warnings.map(w=>h('li',0,w))):null,
  ...Object.keys(LAB).flatMap(k=>CH.items.filter(i=>i.state===k).map(i=>h('div',{class:'chg'},h('div',{class:'k'},LAB[k]),h('div',0,h('b',0,i.check_id+' '),i.name,h('div',{class:'mini'},i.severity+' | '+i.message),i.changed_detail_keys&&i.changed_detail_keys.length?h('div',{class:'mini'},'Changed: '+i.changed_detail_keys.join(', ')):null,i.rule_changed?h('div',{class:'mini'},'The rule changed since the previous run.'):null)))),
  CH.not_comparable.length?[h('h3',0,'Not comparable'),...CH.not_comparable.map(n=>h('div',{class:'chg'},h('div',{class:'k'},n.check_id),h('div',{class:'mini'},n.reason)))]:null)}
function matRow(r){
 return h('div',{class:'mat'},h('div',0,r.capability,h('div',{class:'mini'},'From question'+(r.questions.length>1?'s ':' ')+r.questions.join(', ')+(r.partial?' (some answers unsure)':''))),
  h('div',{class:'trk',role:'img','aria-label':r.capability+': current '+(r.current||'needs input')+', target '+(r.target||'none')},...LV.map(l=>h('span',{class:(r.current===l?'cur ':'')+(r.target===l?'tgt':''),title:l},l[0].toUpperCase()))),
  h('div',{class:'mst '+r.status},MS[r.status],h('div',{class:'mini'},(r.current||'needs input')+(r.target?' vs target '+r.target:''))))}
function maturity(){const M=D.maturity,c=M.counts,doms=[...new Set(M.capabilities.map(r=>r.domain))];
 return h('div',{class:'pane'},h('h2',0,'MATURITY AGAINST TARGET LEVELS'),h('p',{class:'mini'},M.disclaimer),
  h('div',{class:'chips'},...['below','needs_input','meets','above','no_target'].map(k=>h('span',{class:'chip'},MS[k]+' '+c[k]))),
  h('div',{class:'keys'},h('span',0,h('i',{class:'a'}),'Current level (filled, letter C, W or R)'),h('span',0,h('i',{class:'b'}),'Target (dashed ring)'),h('span',0,h('i',{class:'c'}),'Not reached or not chosen')),
  ...doms.map(d=>{const rs=M.capabilities.filter(r=>r.domain===d),main=rs.filter(r=>r.status!=='no_target'),rest=rs.filter(r=>r.status==='no_target');
   return h('details',{class:'dom',open:main.length>0},h('summary',0,d+' ('+main.length+' with a target or open question, '+rest.length+' without)'),...main.map(matRow),rest.length?h('details',0,h('summary',{class:'mini'},rest.length+' without a target'),...rest.map(matRow)):null)}),
  h('div',{class:'note'},'Levels are a screening from 13 questions; Azure scan evidence is not part of them. The goal is not Run everywhere: Walk can be the right target.'))}
function progress(){return h('div',0,D.changes?changes():null,D.maturity?maturity():null)}
function audit(){const A=D.audit;
 return h('div',{class:'pane'},h('h2',0,'SELF-AUDIT'),h('p',0,'Result: '+A.status.toUpperCase()+'. Report fingerprint '+D.run.fingerprint+'.'),h('p',{class:'mini'},A.limits),
  A.invariants.length?h('div',{class:'tw'},h('table',0,h('thead',0,h('tr',0,h('th',0,'Test'),h('th',0,'Result'),h('th',0,'What it verifies'))),h('tbody',0,...A.invariants.map(i=>h('tr',0,h('td',{class:'id'},i.id),h('td',0,i.passed?'pass':'FAIL'),h('td',0,i.description+(i.passed?'':' ('+i.violation_count+' violations)'))))))):h('p',{class:'mini'},'Test detail was left out of this copy. The result line above is the full result.'),
  OP?/*OP*/h('p',{class:'mini'},'Operator copy. Tool '+D.run.tool+' ran '+D.run.apiCalls+' read calls.')/*ENDOP*/:null)}
const maskVal=v=>{let x=2166136261;for(const c of String(v)){x^=c.charCodeAt(0);x=Math.imul(x,16777619)}return 'val-'+(x>>>0).toString(16).padStart(8,'0')};
st.mask=false;const shown=v=>OP&&st.mask?maskVal(v):v;
const toChecks=(id,label)=>h('button',{class:'noprint',onclick:()=>drill({open:id})},label||'See these items');
function tags(){
 const disc=fnd('TAG-DISC-01')[0],dd=disc&&disc.details,num=(x,d)=>typeof x==='number'?x:d;
 const off=TAGIDS.map(byCheck).filter(c=>c&&c.status!=='ran');
 const SRC={policy:'Declared by a tag policy',inferred:'Inferred from what most resources already use',none:'No standard evident'};
 const keys=dd&&dd.top_keys&&typeof dd.top_keys==='object'?Object.entries(dd.top_keys):[];
 return h('div',0,
  h('div',{class:'pane'},h('h2',0,'TAG STANDARD'),
   dd?[h('dl',{class:'kv'},h('dt',0,'Standard found'),h('dd',0,h('span',{class:'src'},SRC[dd.scheme_source]||'Not recorded'),...(Array.isArray(dd.scheme_keys)?dd.scheme_keys.map(k=>h('span',{class:'tag'},k)):[])),
    h('dt',0,'How we know'),h('dd',{class:'mini'},dd.scheme_source==='policy'?'A tag policy names these tags. Nothing is judged against a list built into F-CAT.':(dd.inference_rule||'Not recorded')),
    h('dt',0,'Coverage'),h('dd',0,num(dd.resources_with_any_tag,'?')+' of '+num(dd.resources,'?')+' resources carry at least one tag; '+num(dd.distinct_keys,'?')+' distinct tag names.')),toChecks('TAG-DISC-01')]
   :h('p',{class:'mini'},'No tag discovery result in this run.'),
   OP?/*OP*/h('label',{class:'opt noprint'},h('input',{type:'checkbox',checked:st.mask,onchange:e=>{st.mask=e.target.checked;rerender(true)}}),'Mask tag values (for screenshots)')/*ENDOP*/:null),
  keys.length?h('div',{class:'pane'},h('h2',0,'TAG NAMES IN USE'),...keys.map(([k,v])=>h('div',{class:'covrow'},h('span',{class:'id'},k),h('div',{class:'bar'},h('i',{style:'width:'+Math.max(0,Math.min(100,num(v&&v.percent,0)))+'%'})),h('em',0,num(v&&v.percent,0)+'%')))):null,
  h('div',{class:'pane'},h('h2',0,'SUBSCRIPTIONS BELOW THE BAR'),
   fnd('TAG-COV-01').length?[...fnd('TAG-COV-01').map(f=>{const d=f.details||{};return h('div',{class:'tagrow'},h('b',0,f.name),h('div',0,num(d.missing_any_scheme_key,'?')+' of '+num(d.resources,'?')+' resources lack a tag from the standard ('+num(d.percent_missing,'?')+'%).'),
     d.top_types_lacking&&typeof d.top_types_lacking==='object'?h('div',{class:'mini'},'Most often missing on: '+Object.entries(d.top_types_lacking).map(([t,n])=>t+' ('+n+')').join(', ')):null)}),
    h('p',{class:'mini'},'Only subscriptions with at least 10 resources and 25% or more lacking the standard are listed. Others were not flagged; this is a proposed bar, not a verified rule.'),toChecks('TAG-COV-01')]
   :h('p',{class:'mini'},'No subscription was flagged by this rule.')),
  h('div',{class:'pane'},h('h2',0,'INCONSISTENT SPELLING (MAY SPLIT COST REPORTS)'),
   fnd('TAG-CASE-01').length||fnd('TAG-VAL-01').length?[
    ...fnd('TAG-CASE-01').map(f=>h('div',{class:'tagrow'},h('span',{class:'tag'},'name '+f.name.replace('tag:','')),...Object.entries((f.details&&f.details.casings)||{}).map(([k,n])=>h('span',{class:'var'},k,h('em',0,n))))),
    ...fnd('TAG-VAL-01').map(f=>h('div',{class:'tagrow'},h('span',{class:'tag'},'values of '+f.name.replace('tag:','')),...((f.details&&Array.isArray(f.details.variants))?f.details.variants.flatMap(g=>Array.isArray(g)?g.map(x=>h('span',{class:'var'},shown(x.value),h('em',0,x.count))):[]):[]))),
    h('p',{class:'mini'},'Names are case-insensitive to Azure but the casing shows in cost reports; values are case-sensitive and appear as separate rows. Whether Cost Management merges them is not verified.'),toChecks('TAG-CASE-01','See name variants'),' ',toChecks('TAG-VAL-01','See value variants')]
   :h('p',{class:'mini'},'No spelling variants were flagged.')),
  fnd('TAG-RG-01').length?h('div',{class:'pane'},h('h2',0,'RESOURCE GROUP TAGS NOT CARRIED BY THEIR RESOURCES'),...fnd('TAG-RG-01').map(f=>h('div',{class:'tagrow'},h('b',0,subL(f.sub)+' / '+f.name),h('div',{class:'mini'},f.msg))),
   h('div',{class:'note'},'Azure does not copy resource group tags to resources. Cost Management has an optional inheritance setting that F-CAT cannot read yet, so whether it is on is not assessed.'),toChecks('TAG-RG-01')):null,
  off.length?h('div',{class:'pane'},h('h2',0,'TAG CHECKS THAT DID NOT RUN'),h('ul',{class:'plain'},...off.map(c=>h('li',0,h('b',0,c.title),': ',c.plain)))):null)}
const RENDER={summary,findings,coverage,tags,progress,audit};
const root=$('#app');
function mountAll(keep){const sc=window.scrollY,ae=document.activeElement&&document.activeElement.id;root.replaceChildren(h('div',{class:'cover'},h('h1',0,D.title),D.subtitle?h('p',0,D.subtitle):null,D.preparedFor?h('p',0,'Prepared for '+D.preparedFor):null,D.preparedBy?h('p',0,'Prepared by '+D.preparedBy):null,h('p',{class:'mini'},'Run '+D.run.started.slice(0,10)+'. Report fingerprint '+D.run.fingerprint+'. Self-audit: '+D.audit.status+'.')),topBar(),
 h('main',0,...VIEWS.map(([k])=>h('div',{class:'view'+(st.view===k?' on':''),id:'v-'+k},RENDER[k]())),D.footer?h('p',{class:'mini'},D.footer):null));if(keep)window.scrollTo(0,sc);if(ae==='q'){const q=$('#q');if(q){q.focus();q.setSelectionRange(q.value.length,q.value.length)}}}
rerender=mountAll;if(!VIEWS.some(v=>v[0]===st.view))st.view='summary';mountAll();
"""

import re as _re  # noqa: E402

_OPSEG = _re.compile(r"/\*OP\*/.*?/\*ENDOP\*/", _re.S)


def js_for(audience: str) -> str:
    """The customer file carries no operator code at all, not just a switch that turns it off."""
    if audience == "operator":
        return JS.replace("/*OP*/", "").replace("/*ENDOP*/", "")
    return _OPSEG.sub("null", JS).replace("const OP=D.audience==='operator';", "const OP=false;")
