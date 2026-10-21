from __future__ import annotations

import argparse
import json
import pathlib
import sys

from . import checks, collectors, compare, doctor, focus_import, manifest, maturity, redact, render_html, render_json, render_xlsx
from . import config as cfgmod
from .auth import AzCliTokenProvider
from .errors import FcatError
from .http import Client
from .snapshot import Snapshot


def _finish(cfg, snap, out, identity, calls, cerrors, started, redacted=False):
    findings, status = checks.run_all(cfg, snap)
    if redacted:
        salt = redact.new_salt()
        findings, identity = redact.findings(findings, salt), redact.identity(identity, salt)
    m = manifest.build(cfg, identity, calls, status, cerrors, started, manifest.now(), manifest.scope_summary(snap))
    m["redacted"] = redacted
    m["report_options"] = cfg.report.manifest_view()
    doc = render_json.render(pathlib.Path(out) / "report.json", m, findings)
    render_html.render(pathlib.Path(out) / "report.html", doc, cfg.report)
    try:
        render_xlsx.render(pathlib.Path(out) / "report.xlsx", doc, cfg.report)
    except ImportError:
        print("note: openpyxl not installed, Excel report skipped (pip install 'fcat[excel]')")
    print(f"{len(findings)} findings; checks: " + ", ".join(f"{s['id']}={s['status']}" for s in status))
    print(f"self-audit: {doc['audit']['status']} (report fingerprint {doc['audit']['report_hash']})")
    return doc["audit"]["status"] == "pass"


def _doctor(args) -> int:
    if args.needs:
        print(doctor.needs_markdown())
        return 0
    problem = manifest.out_dir_problem(args.out)
    if problem:
        print(f"error: {problem}. Use a different --out or add it to .gitignore.", file=sys.stderr)
        return 2
    try:
        cfg = cfgmod.load(args.config) if args.config else None
        tp = AzCliTokenProvider()
        client = Client(tp)
        results = doctor.probe(client, tp, cfg.subscriptions if cfg else None, cfg.management_groups if cfg else None)
    except (FcatError, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(doctor.render_probe_table(results))
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "doctor.json").write_text(json.dumps({"probes": results, "calls": len(client.calls)}, indent=1))
    return 0 if all(r["status"] == "pass" for r in results) else 1


def _maturity(args) -> int:
    try:
        res = maturity.evaluate(maturity.load(args.input))
    except FcatError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "maturity.json").write_text(json.dumps(res, indent=1))
    (out / "maturity.md").write_text(maturity.markdown(res))
    c = res["counts"]
    print(f"below target {c['below']}, meets {c['meets']}, above {c['above']}, no target {c['no_target']}, needs input {c['needs_input']}")
    return 0


def _compare(args) -> int:
    try:
        result = compare.compare(compare.load(args.older), compare.load(args.newer))
    except FcatError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "compare.json").write_text(json.dumps(result, indent=1))
    (out / "compare.md").write_text(compare.markdown(result))
    c = result["counts"]
    print(
        f"new {c['new']}, no longer reported {c['no_longer_reported']}, worse {c['worse']}, better {c['better']}, changed {c['changed']}, unchanged {c['unchanged']}"
    )
    for w in result["warnings"]:
        print(f"note: {w}")
    return 0


PURGE_FILES = ("report.json", "report.html", "report.xlsx", "compare.json", "compare.md", "maturity.json", "maturity.md")


def _purge(out: pathlib.Path, yes: bool) -> int:
    """Deletes only files fcat itself writes (reports, snapshot/*.json) in the local output folder. Never touches Azure. Dry run by default."""
    if not out.is_dir():
        print(f"nothing to purge: {out} does not exist")
        return 0
    todo = [out / n for n in PURGE_FILES if (out / n).is_file()] + sorted((out / "snapshot").glob("*.json"))
    for p in todo:
        print(("delete " if yes else "would delete ") + str(p))
    if yes:
        for p in todo:
            p.unlink()
        for d in (out / "snapshot", out):
            try:
                d.rmdir()  # only if now empty; foreign files keep the folder
            except OSError:
                pass
    elif todo:
        print("dry run: pass --yes to delete")
    return 0


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
    for sp in (r, a):
        sp.add_argument(
            "--branding", help="TOML file with only a [report] table; replaces the [report] settings of the main config for this run"
        )
        sp.add_argument(
            "--redact",
            action="store_true",
            help="pseudonymise tenant, subscription, resource group and resource names in the reports (snapshot is not redacted)",
        )
    d = sub.add_parser("doctor", help="list the access the checks need (offline) or probe what the current login can read")
    d.add_argument("--needs", action="store_true", help="print the access-need list from the check catalogue; no login, no network")
    d.add_argument("--config", help="optional config: probes are limited to its subscriptions or management groups")
    d.add_argument("--out", default="output")
    cp = sub.add_parser(
        "compare", help="compare two report.json files (older first) and list new, worse, better and no longer reported findings (offline)"
    )
    cp.add_argument("older")
    cp.add_argument("newer")
    cp.add_argument("--out", default="output")
    mt = sub.add_parser(
        "maturity", help="screen FinOps maturity from questionnaire answers and compare with a target level per capability (offline)"
    )
    mt.add_argument("input", help="TOML file with [answers] q1..q13 (A,B,C,D) and optional [targets]")
    mt.add_argument("--out", default="output")
    pg = sub.add_parser("purge", help="delete files fcat created in an output folder (dry run unless --yes)")
    pg.add_argument("--out", default="output")
    pg.add_argument("--yes", action="store_true")
    for sp in (r, a, f, cp, mt):
        sp.add_argument(
            "--allow-unignored-out", action="store_true", help="write into a git work tree even if git would not ignore the folder"
        )
    args = p.parse_args(argv)
    if args.cmd == "doctor":
        return _doctor(args)
    problem = None if args.cmd == "purge" or args.allow_unignored_out else manifest.out_dir_problem(args.out)
    if problem:
        print(f"error: {problem}. Use a different --out, or add it to .gitignore, or pass --allow-unignored-out.", file=sys.stderr)
        return 2
    if args.cmd == "compare":
        return _compare(args)
    if args.cmd == "maturity":
        return _maturity(args)
    if args.cmd == "purge":
        return _purge(pathlib.Path(args.out), args.yes)
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
    if getattr(args, "branding", None):
        try:
            cfg.report = cfgmod.load_report_options(args.branding)
        except (cfgmod.ReportOptionsError, OSError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
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
            ok = _finish(cfg, snap, out, tp.identity(), client.calls, cerrors, started, args.redact)
        else:
            ok = _finish(cfg, snap, out, {}, [], [], started, args.redact)
        if not ok:
            print("warning: self-audit FAILED, do not use this report; see the Audit section", file=sys.stderr)
            return 3
    except FcatError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
