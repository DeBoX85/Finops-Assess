"""Round 4 mock-up (A3 refined, 2026-10-21): the A3 dashboard plus the three features added on 2026-10-21 and the multi-tenant flexibility decision.
 - Changes since the last run: the REAL output of fcat.compare between two analyses of the synthetic estate (the older one is the same estate with a few
   rows changed, so every state shown is produced by the tool, not drawn by hand).
 - Maturity with a target level per capability: the REAL output of fcat.maturity on made-up answers and targets.
 - Portfolio view: a design for running several tenants or scopes (backlog 37). The tool has no batch run yet; the two rows are real analyses of two
   synthetic snapshots, and every other part is a layout proposal.
 - New checks (non-production prompts, lifecycle, availability sets) appear in the queue because they are in the golden report.
Rules kept: no money figures, Not assessed separate from no findings, synthetic data labelled in the page, no em dashes.
Output: docs/mockups/frontend4/*.html. Self-contained, system fonts, no network."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "docs" / "mockups" / "frontend4"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v3 = _load("v3", ROOT / "scripts" / "make_frontend_v3.py")
v2 = v3.v2
ms = v3.ms

from fcat import cli, compare, maturity  # noqa: E402

ANSWERS_A = {
    "q1": "B",
    "q2": "B",
    "q3": "A",
    "q4": "B",
    "q5": "A",
    "q6": "C",
    "q7": "A",
    "q8": "B",
    "q9": "D",
    "q10": "B",
    "q11": "A",
    "q12": "D",
    "q13": "B",
}
ANSWERS_B = {
    "q1": "C",
    "q2": "B",
    "q3": "B",
    "q4": "C",
    "q5": "B",
    "q6": "B",
    "q7": "B",
    "q8": "C",
    "q9": "B",
    "q10": "C",
    "q11": "B",
    "q12": "B",
    "q13": "C",
}
TARGETS = {
    "Executive Strategy Alignment": "walk",
    "Budgeting": "run",
    "Forecasting": "walk",
    "Allocation": "walk",
    "Anomaly Management": "walk",
    "Usage Optimization": "walk",
    "Rate Optimization": "walk",
    "Governance, Policy and Risk": "walk",
    "Reporting and Analytics": "walk",
}


def _analyse(snapshot_dir: Path, work: Path):
    """Runs the real offline analysis on a snapshot folder and returns the report document."""
    out = work / "out"
    shutil.copytree(snapshot_dir, out / "snapshot")
    cfg = work / "c.toml"
    cfg.write_text('[run]\nprofile="standard"\n')
    cli.main(["analyze", "--config", str(cfg), "--out", str(out), "--allow-unignored-out"])
    return json.loads((out / "report.json").read_text())


def _older_snapshot(dst: Path):
    """The same synthetic estate a few weeks earlier: two disks not yet orphaned, one since removed, one resized, no availability-set data, one VM then ok."""
    shutil.copytree(ms.SNAP, dst)
    p = dst / "unattached_disks.json"
    d = json.loads(p.read_text())
    rows = d["rows"][2:]  # the two first disks did not exist yet
    gone = dict(d["rows"][0])
    gone["id"] = gone["id"].replace("disk-", "disk-retired-")
    rows.append(gone)  # reported then, removed since
    rows[3]["sizeGB"] = (rows[3].get("sizeGB") or 32) * 2  # resized since
    d["rows"] = rows
    p.write_text(json.dumps(d))
    (dst / "availability_sets.json").unlink()  # collector did not exist then: that check is not comparable
    v = dst / "vms.json"
    d = json.loads(v.read_text())
    d["rows"] = [r for r in d["rows"] if not r["id"].endswith("vm-dev-noshut")]
    v.write_text(json.dumps(d))


def build():
    d = v3.build()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "new").mkdir()
        (tmp / "old").mkdir()
        new = _analyse(ms.SNAP, tmp / "new")
        _older_snapshot(tmp / "older_snapshot")
        old = _analyse(tmp / "older_snapshot", tmp / "old")
        # make the pair look like two runs three weeks apart; analysis timestamps are wall-clock, so set them for the page
        old["manifest"]["started"] = "2026-09-30T09:12:00+00:00"
        new["manifest"]["started"] = "2026-10-21T09:05:00+00:00"
        res = compare.compare(old, new)
    for i in res["items"]:
        i["sub"] = (i["resource_id"].split("/subscriptions/")[-1].split("/")[0]).lower() if "/subscriptions/" in i["resource_id"] else "-"
        i["name"] = i["resource_id"].rstrip("/").rsplit("/", 1)[-1]
        del i["resource_id"]
    d["changes"] = {
        **{k: res[k] for k in ("counts", "warnings", "not_comparable")},
        "older": {"started": res["older"]["started"], "findings": res["older"]["findings"]},
        "newer": {"started": res["newer"]["started"], "findings": res["newer"]["findings"]},
        "items": [i for i in res["items"] if i["state"] != "unchanged"],
    }
    d["maturity"] = maturity.evaluate({"answers": ANSWERS_A, "targets": TARGETS})
    m_b = maturity.evaluate({"answers": ANSWERS_B, "targets": TARGETS})

    def row(name, doc, mat, subs):
        sev = {k: sum(1 for f in doc["findings"] if f["severity"] == k) for k in ("high", "medium", "low", "info")}
        st = [c["status"] for c in doc["manifest"]["checks"]]
        return {
            "name": name,
            "subs": subs,
            "findings": len(doc["findings"]),
            "sev": sev,
            "not_assessed": sum(1 for s in st if s == "not_assessed"),
            "skipped": sum(1 for s in st if s == "skipped"),
            "below": mat["counts"]["below"],
            "needs_input": mat["counts"]["needs_input"],
            "audit": doc["audit"]["status"],
            "ran": doc["manifest"]["started"][:10],
        }

    d["portfolio"] = [
        row(
            "Synthetic tenant A",
            new,
            d["maturity"],
            len({f["resource_id"].split("/")[2] for f in new["findings"] if "/subscriptions/" in f["resource_id"]}),
        ),
        row("Synthetic tenant B (older snapshot, shown as a second tenant)", old, m_b, 4),
    ]
    return d


CSS4 = r"""
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0}.chip{border:1px solid var(--line);border-radius:999px;padding:2px 10px;font-size:12px;background:var(--pane)}
.chip b{font-variant-numeric:tabular-nums}.chip.new{border-color:var(--bad)}.chip.gone{border-color:var(--ok)}
.chg{display:grid;grid-template-columns:96px minmax(0,1fr);gap:2px 10px;padding:5px 0;border-top:1px solid var(--line)}.chg .k{font-size:12px;color:var(--ink2)}
.chg .k::before{content:"";display:inline-block;width:9px;height:9px;margin-right:6px;border:2px solid var(--ink2)}
.chg.new .k::before{background:var(--bad);border-color:var(--bad);border-radius:50%}.chg.no_longer_reported .k::before{border-color:var(--ok);border-radius:50%}
.chg.changed .k::before,.chg.worse .k::before,.chg.better .k::before{transform:rotate(45deg)}
.chg .rule{font-size:11px;color:var(--warn)}
.warns{margin:6px 0;padding-left:18px;color:var(--ink2);font-size:12px}
.seg{flex-wrap:wrap;max-width:100%}.tools{max-width:100%}.mat{display:grid;grid-template-columns:minmax(0,1.4fr) 140px minmax(0,1fr);gap:6px 10px;align-items:center;padding:4px 0;border-top:1px solid var(--line)}
.trk{position:relative;height:22px}.trk::before{content:"";position:absolute;left:8%;right:8%;top:10px;height:2px;background:var(--line)}
.trk span{position:absolute;top:0;width:22px;height:22px;margin-left:-11px;display:grid;place-items:center;font-size:10px;border-radius:50%}
.trk .s{border:2px solid var(--line);background:var(--pane);color:var(--muted)}
.trk .cur{background:var(--ink);color:var(--pane);border-color:var(--ink)}
.trk .tgt{border:2px dashed var(--acc);background:transparent;color:var(--acc)}
.trk .cur.tgt{border-style:solid;box-shadow:0 0 0 3px var(--accbg)}
.mst{font-size:12px}.mst.below{color:var(--bad);font-weight:600}.mst.needs_input{color:var(--warn)}
.tkeys{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--ink2);margin:6px 0}.tkeys i{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:5px;vertical-align:-2px}
.tkeys .a{background:var(--ink)}.tkeys .b{border:2px dashed var(--acc)}.tkeys .c{border:2px solid var(--line)}
table.pf{width:100%;border-collapse:collapse}table.pf th,table.pf td{text-align:left;padding:6px 8px;border-top:1px solid var(--line);vertical-align:top}table.pf td.n,table.pf th.n{text-align:right;font-variant-numeric:tabular-nums}
.pfw{overflow-x:auto}.draft{border:1px dashed var(--ink2);border-radius:6px;padding:8px 10px;color:var(--ink2);font-size:12px;margin-top:8px}
@media (max-width:520px){.mat{grid-template-columns:minmax(0,1fr) 120px}.mat .mst{grid-column:1/-1}}
@media print{.chg,.mat{break-inside:avoid}}
"""

JS4 = r"""
const CH=D.changes,MT=D.maturity;
const LBL={new:'New',no_longer_reported:'No longer reported',worse:'Worse',better:'Better',changed:'Changed'};
function changesPanel(){
 const c=CH.counts;
 const chips=[['new','New',c.new],['worse','Worse',c.worse],['changed','Changed',c.changed],['better','Better',c.better],['no_longer_reported','No longer reported',c.no_longer_reported],['u','Unchanged',c.unchanged]];
 return [
  h('p',{class:'mini'},'Compared with the run of '+CH.older.started.slice(0,10)+' ('+CH.older.findings+' findings). This run: '+CH.newer.started.slice(0,10)+' ('+CH.newer.findings+' findings).'),
  h('div',{class:'chips'},...chips.map(([k,l,n])=>h('span',{class:'chip '+(k==='new'?'new':k==='no_longer_reported'?'gone':'')},l+' ',h('b',0,n)))),
  h('div',{class:'note'},'No longer reported does not prove a fix: the resource may be gone, the rule may have changed, or the scope may differ.'),
  CH.warnings.length?h('ul',{class:'warns'},...CH.warnings.map(w=>h('li',0,w))):null,
  ...['new','worse','changed','better','no_longer_reported'].flatMap(k=>CH.items.filter(i=>i.state===k).map(i=>
   h('div',{class:'chg '+k},h('div',{class:'k'},LBL[k]),h('div',0,h('b',0,i.check_id+' '),i.name,h('div',{class:'mini'},i.severity+' | '+i.message),
    i.changed_detail_keys&&i.changed_detail_keys.length?h('div',{class:'mini'},'Changed: '+i.changed_detail_keys.join(', ')):null,
    i.rule_changed?h('div',{class:'rule'},'Rule text changed since the older run'):null)))),
  CH.not_comparable.length?h('h2',0,'NOT COMPARABLE'):null,
  ...CH.not_comparable.map(n=>h('div',{class:'chg'},h('div',{class:'k'},n.check_id),h('div',{class:'mini'},n.reason)))]}
const LV=['crawl','walk','run'],LX={crawl:16,walk:50,run:84};
const MS={below:'Below target',meets:'Meets target',above:'Above target',no_target:'No target set',needs_input:'Needs input'};
function matRow(r){
 const dots=LV.map(l=>h('span',{class:'s'+(r.current===l?' cur':'')+(r.target===l?' tgt':''),style:'left:'+LX[l]+'%',title:l},l[0].toUpperCase()));
 return h('div',{class:'mat'},
  h('div',0,r.capability,h('div',{class:'mini'},'Q'+r.questions.join(', Q')+(r.partial?' | some mapped answers unsure':''))),
  h('div',{class:'trk',role:'img','aria-label':r.capability+': current '+(r.current||'needs input')+', target '+(r.target||'none')},...dots),
  h('div',{class:'mst '+r.status},MS[r.status],h('div',{class:'mini'},(r.current||'needs input')+(r.target?' vs target '+r.target:''))))}
function maturityPanel(){
 const c=MT.counts,order=['below','needs_input','meets','above','no_target'];
 return [
  h('p',{class:'mini'},MT.disclaimer),
  h('div',{class:'chips'},...order.map(k=>h('span',{class:'chip'},MS[k]+' ',h('b',0,c[k])))),
  h('div',{class:'tkeys'},h('span',0,h('i',{class:'a'}),'Current level (from answers)'),h('span',0,h('i',{class:'b'}),'Target set by the owner'),h('span',0,h('i',{class:'c'}),'Level not reached or not chosen')),
  ...order.flatMap(k=>MT.capabilities.filter(r=>r.status===k).map(matRow)),
  h('div',{class:'note'},'Levels are a screening from 13 questions. Azure scan evidence is not folded in yet. The goal is not Run everywhere: a target of Walk can be the right one.')]}
function portfolio(){
 const rows=D.portfolio;
 return [
  h('div',{class:'pfw'},h('table',{class:'pf'},h('thead',0,h('tr',0,h('th',0,'Tenant or scope'),h('th',{class:'n'},'Subscriptions'),h('th',{class:'n'},'Findings'),h('th',0,'Severity'),h('th',{class:'n'},'Checks not assessed'),h('th',{class:'n'},'Below maturity target'),h('th',{class:'n'},'Needs input'),h('th',0,'Self-audit'),h('th',0,'Last run'))),
   h('tbody',0,...rows.map(r=>h('tr',0,h('td',0,r.name),h('td',{class:'n'},r.subs),h('td',{class:'n'},r.findings),h('td',0,['high','medium','low','info'].map(k=>r.sev[k]+' '+k).join(' | ')),h('td',{class:'n'},r.not_assessed),h('td',{class:'n'},r.below),h('td',{class:'n'},r.needs_input),h('td',0,r.audit),h('td',0,r.ran)))))),
  h('div',{class:'draft'},'Design only. F-CAT runs one tenant per run today. This layout shows what a roll-up could look like if a run could take a list of tenants or scopes (backlog 37, owner chose to keep this option open). Each tenant would keep its own report, snapshot and audit; a roll-up would never merge findings across customers. Both rows here are real analyses of synthetic snapshots.'),
  h('div',{class:'draft'},'Open questions for the owner: does a roll-up ever leave your laptop, is it for one customer with many tenants or for several customers, and should a customer ever see another customer\'s row? The safe default is one customer per roll-up.')]}
function progressSection(){
 return h('section',{class:'wrap',id:'progsec',style:'padding-bottom:0'},h('div',{class:'row2'},
  h('div',{class:'pane'},h('h2',0,'CHANGES SINCE THE LAST RUN'),mount(h('div'),changesPanel)),
  h('div',{class:'pane'},h('h2',0,'MATURITY AGAINST TARGET LEVELS'),mount(h('div'),maturityPanel))))}
function portSection(){return h('section',{class:'wrap',id:'portsec',style:'padding-bottom:0'},h('div',{class:'pane'},h('h2',0,'PORTFOLIO OF TENANTS AND SCOPES (DESIGN)'),mount(h('div'),portfolio)))}
function viewSwitch4(){return h('div',{class:'seg noprint',role:'group','aria-label':'View'},...[['all','Everything'],['find','Findings'],['gov','Governance and tags'],['prog','Progress'],['port','Portfolio']].map(([k,l])=>h('button',{'aria-pressed':st.view===k,onclick:()=>{st.view=k;store.set('view',k);applyView4();draw()}},l)))}
function applyView4(){
 const g=$('#govsec'),m=$('#mainsec'),s=$('#sumsec'),p=$('#progsec'),o=$('#portsec');if(!g)return;const v=st.view;
 g.classList.toggle('hide',!(v==='all'||v==='gov'));m.classList.toggle('hide',!(v==='all'||v==='find'));s.classList.toggle('hide',!(v==='all'||v==='find'));
 p.classList.toggle('hide',!(v==='all'||v==='prog'));o.classList.toggle('hide',v!=='port')}
"""

A4 = r"""
const app=$('#app');app.append(topBar(viewSwitch4()),printHead('Azure FinOps assessment'));
if(!['all','find','gov','prog','port'].includes(st.view))st.view='all';
const sum=h('section',{class:'wrap',id:'sumsec',style:'padding-bottom:0'});
sum.append(mount(h('div'),()=>[h('p',{class:'headline'},headlineText())]),mount(h('div'),kpis),
 h('div',{class:'row2'},h('div',{class:'pane'},h('h2',0,'WHERE IT CONCENTRATES (click to filter)'),mount(h('div'),areaBars),h('h2',0,'SEVERITY'),mount(h('div'),sevBar)),
  h('div',{class:'pane'},h('h2',0,'MAP OF SUBSCRIPTIONS AND AREAS'),mount(h('div'),()=>treemap(260))),
  h('div',{class:'pane'},h('h2',0,'DID EVERY CHECK RUN?'),mount(h('div'),coverageStrip))));
const gov=govSection(false);gov.id='govsec';
const prog=progressSection(),port=portSection();
const main=h('main',{class:'wrap',id:'mainsec'});const g=h('div',{class:'grid3'});
g.append(mount(h('aside',{class:'pane side'}),sideFilters),mount(h('section',{class:'pane'}),queue),mount(h('aside',{class:'pane',id:'drawer'}),()=>drawer()));main.append(g);
app.append(sum,prog,gov,main,port);applyView4();draw();
"""

PAGE_NOTE = "Synthetic estate. Findings, run comparison and maturity levels are the real output of the tool on it; the portfolio view and the governance posture states are designs."


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.dumps(build(), separators=(",", ":")).replace("</", "<\\/")
    page = v2.PAGE.format(css=v2.CSS + v3.CSS3 + CSS4, js=v2.JS + v3.JS3 + JS4, body=A4).replace("/*DATA*/", data)
    page = page.replace("fcat2:", "fcat4:")
    page = page.replace(
        "label=s.replace('sub-synth-','Subscription ')",
        "label=s==='-'?'Tenant-wide (no single subscription)':s.replace('sub-synth-','Subscription ')",
    )
    page = page.replace("[s,s,subN(s)]", "[s,s==='-'?'Tenant-wide':s,subN(s)]")
    (OUT / "A4-dashboard.html").write_text(page)
    (OUT / "index.html").write_text(
        "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>F-CAT front-end round 4</title>"
        "<body style='font:16px/1.5 system-ui;max-width:720px;margin:24px auto;padding:0 16px'><h1>Front-end round 4</h1>"
        "<p><a href=A4-dashboard.html>A4: A3 plus changes since the last run, maturity against target levels, and a portfolio design</a>. "
        "Use the switch top right: Everything, Findings, Governance and tags, Progress, Portfolio.</p>"
        f"<p>{PAGE_NOTE}</p></body>"
    )
    print("wrote", OUT)


if __name__ == "__main__":
    main()
