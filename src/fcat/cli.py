from __future__ import annotations

import argparse
import pathlib
import sys

from . import checks, collectors, focus_import, manifest, render_html, render_json, render_xlsx
from . import config as cfgmod
from .auth import AzCliTokenProvider
from .errors import FcatError
from .http import Client
from .snapshot import Snapshot


def _finish(cfg, snap, out, identity, calls, cerrors, started):
    findings, status = checks.run_all(cfg, snap)
    m = manifest.build(cfg, identity, calls, status, cerrors, started, manifest.now(), manifest.scope_summary(snap))
    doc = render_json.render(pathlib.Path(out) / "report.json", m, findings)
    render_html.render(pathlib.Path(out) / "report.html", doc)
    try:
        render_xlsx.render(pathlib.Path(out) / "report.xlsx", doc)
    except ImportError:
        print("note: openpyxl not installed, Excel report skipped (pip install 'fcat[excel]')")
    print(f"{len(findings)} findings; checks: " + ", ".join(f"{s['id']}={s['status']}" for s in status))
    print(f"self-audit: {doc['audit']['status']} (report fingerprint {doc['audit']['report_hash']})")
    return doc["audit"]["status"] == "pass"


def main(argv=None):
    p = argparse.ArgumentParser(prog="fcat")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="collect from Azure (read-only) and analyse")
    r.add_argument("--config", required=True)
    r.add_argument("--out", default="output")
    a = sub.add_parser("analyze", help="re-analyse an existing snapshot offline")
    a.add_argument("--config", required=True)
    a.add_argument("--out", default="output")
    f = sub.add_parser("import-focus", help="aggregate a customer-provided FOCUS cost file into the snapshot (offline)")
    f.add_argument("paths", nargs="+")
    f.add_argument("--out", default="output")
    for sp in (r, a, f):
        sp.add_argument(
            "--allow-unignored-out", action="store_true", help="write into a git work tree even if git would not ignore the folder"
        )
    args = p.parse_args(argv)
    problem = None if args.allow_unignored_out else manifest.out_dir_problem(args.out)
    if problem:
        print(f"error: {problem}. Use a different --out, or add it to .gitignore, or pass --allow-unignored-out.", file=sys.stderr)
        return 2
    if args.cmd == "import-focus":
        try:
            data = focus_import.import_files(args.paths)
        except FcatError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        Snapshot(pathlib.Path(args.out) / "snapshot").save("cost_focus", data)
        print(f"imported {data['rows']} rows, {data['currency']}, {data['period']['first_day']} to {data['period']['last_day']}")
        return 0
    cfg = cfgmod.load(args.config)
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    snap = Snapshot(out / "snapshot")
    started = manifest.now()
    try:
        if args.cmd == "run":
            tp = AzCliTokenProvider()
            client = Client(tp)
            cerrors = []
            collectors.collect(client, snap, cfg, cerrors)
            ok = _finish(cfg, snap, out, tp.identity(), client.calls, cerrors, started)
        else:
            ok = _finish(cfg, snap, out, {}, [], [], started)
        if not ok:
            print("warning: self-audit FAILED, do not use this report; see the Audit section", file=sys.stderr)
            return 3
    except FcatError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
