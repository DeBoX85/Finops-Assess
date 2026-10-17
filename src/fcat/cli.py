from __future__ import annotations
import argparse, pathlib, sys
from . import config as cfgmod, checks, checks_builtin, collectors, manifest, render_json
from .snapshot import Snapshot
from .http import Client
from .auth import AzCliTokenProvider
from .errors import FcatError

def _finish(cfg, snap, out, identity, calls, cerrors, started):
    findings, status = checks.run_all(cfg, snap)
    m = manifest.build(cfg, identity, calls, status, cerrors, started, manifest.now())
    render_json.render(pathlib.Path(out) / "report.json", m, findings)
    print(f"{len(findings)} findings; checks: " + ", ".join(f"{s['id']}={s['status']}" for s in status))

def main(argv=None):
    p = argparse.ArgumentParser(prog="fcat")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="collect from Azure (read-only) and analyse")
    r.add_argument("--config", required=True); r.add_argument("--out", default="output")
    a = sub.add_parser("analyze", help="re-analyse an existing snapshot offline")
    a.add_argument("--config", required=True); a.add_argument("--out", default="output")
    args = p.parse_args(argv)
    cfg = cfgmod.load(args.config)
    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    snap = Snapshot(out / "snapshot")
    started = manifest.now()
    try:
        if args.cmd == "run":
            tp = AzCliTokenProvider()
            client = Client(tp)
            cerrors = []
            collectors.collect(client, snap, cfg, cerrors)
            _finish(cfg, snap, out, tp.identity(), client.calls, cerrors, started)
        else:
            _finish(cfg, snap, out, {}, [], [], started)
    except FcatError as e:
        print(f"error: {e}", file=sys.stderr); return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
