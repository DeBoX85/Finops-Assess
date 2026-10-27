"""Generic accuracy tests that apply to EVERY registered check (docs/AUDIT.md, backlog 22). New checks are covered automatically.

1. Robustness: seeded type-mutation fuzzing of the fixture rows. A check may report nothing, or NotAssessed, but must not crash.
2. Metamorphic: shuffling rows, or adding unknown columns, must not change the findings.
3. Locality: removing rows from a check's primary collector must not change findings for the rows that remain.
4. Contract: every column used by a fixture or the synthetic estate is projected by that collector's KQL (schema-drift guard).
"""

import copy
import json
import pathlib
import random
import re
import sys

import pytest

from fcat import checks, collectors
from fcat.snapshot import Snapshot

checks.load_builtin()
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import make_synthetic as ms  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "checks"


def _cases(meta):
    return json.loads((FIX / f"{meta.id}.json").read_text())["cases"]


def _load(tmp_path, snapshot, tag):
    s = Snapshot(tmp_path / tag)
    for k, v in snapshot.items():
        s.save(k, v)
    return s


def _run(fn, snap):
    try:
        return sorted((f.resource_id, f.fingerprint or "", f.message) for f in fn(snap))
    except checks.NotAssessed:
        return "not_assessed"


PARAMS = [pytest.param(m, fn, id=m.id) for m, fn in checks.REGISTRY]


# ---- 1. robustness ----
JUNK = [None, "", "x", 0, -1, 3.5, True, [], {}, [None], {"a": None}, "2026-13-45T99:99:99Z", "ÿ" * 50, 10**12]


@pytest.mark.parametrize(("meta", "fn"), PARAMS)
def test_fuzzed_rows_never_crash_a_check(meta, fn, tmp_path):
    rnd = random.Random(f"fcat-{meta.id}")
    for c in _cases(meta):
        base = c["snapshot"]
        for i in range(60):
            snap = copy.deepcopy(base)
            for data in snap.values():
                for row in data.get("rows", []) if isinstance(data, dict) else []:
                    for key in list(row):
                        if key != "id" and rnd.random() < 0.35:
                            row[key] = rnd.choice(JUNK)
            s = _load(tmp_path, snap, f"fz{i}")
            try:
                list(fn(s))
            except checks.NotAssessed:
                pass


# ---- 2. metamorphic ----
@pytest.mark.parametrize(("meta", "fn"), PARAMS)
def test_row_order_and_extra_columns_do_not_change_findings(meta, fn, tmp_path):
    rnd = random.Random(f"mm-{meta.id}")
    for ci, c in enumerate(_cases(meta)):
        ref = _run(fn, _load(tmp_path, c["snapshot"], f"ref{ci}"))
        for k in range(5):
            snap = copy.deepcopy(c["snapshot"])
            for data in snap.values():
                if isinstance(data, dict) and "rows" in data:
                    rnd.shuffle(data["rows"])
                    for row in data["rows"]:
                        row["x_unknown_column"] = {"anything": [1, 2, 3]}
            assert _run(fn, _load(tmp_path, snap, f"mm{ci}_{k}")) == ref, c["name"]


# ---- 3. locality ----
# Estate-level checks judge shares and totals, so removing one row legitimately changes their message or numbers. They are covered by
# tests/test_tags.py (order independence, casing relabel, scale) instead.
AGGREGATE = {
    "TAG-DISC-01",
    "TAG-COV-01",
    "TAG-CASE-01",
    "TAG-VAL-01",
    "TAG-RG-01",
    "POL-TAG-01",
    "POL-TAGMOD-01",
    "BUD-COVER-01",
    "BUD-FCST-01",
    "ALR-ANOM-01",
    "EXP-CFG-01",
}


@pytest.mark.parametrize(("meta", "fn"), PARAMS)
def test_removing_primary_rows_does_not_change_other_findings(meta, fn, tmp_path):
    if meta.id in AGGREGATE:
        pytest.skip("estate-level check, see tests/test_tags.py")
    primary = meta.collectors[0]
    for ci, c in enumerate(_cases(meta)):
        rows = (c["snapshot"].get(primary) or {}).get("rows", [])
        full = _run(fn, _load(tmp_path, c["snapshot"], f"full{ci}"))
        if full == "not_assessed" or len(rows) < 2:
            continue
        ids = [r.get("id") for r in rows]
        for drop in range(len(rows)):
            if ids.count(ids[drop]) > 1:
                continue  # expanded rows (one row per AKS pool) share an id; dropping one changes that resource's own findings by design
            snap = copy.deepcopy(c["snapshot"])
            gone = snap[primary]["rows"].pop(drop)["id"]
            part = _run(fn, _load(tmp_path, snap, f"p{ci}_{drop}"))
            assert part == [t for t in full if t[0] != gone], (c["name"], gone)


# ---- 4. contract: fixtures and synthetic estate only use projected columns ----
def projected_columns(kql: str) -> set[str]:
    m = re.search(r"\|\s*project\s+(.*?)(?:\|\s*order by|$)", kql, re.S | re.I)
    if m is None:  # summarize form: names are the aggregate aliases and the by-columns
        m = re.search(r"\|\s*summarize\s+(.*?)(?:\|\s*order by|$)", kql, re.S | re.I)
        clause = re.sub(r"\s+by\s+", ", ", m.group(1))
    else:
        clause = m.group(1)
    parts, depth, cur = [], 0, ""
    for ch in clause:
        depth += ch in "(["
        depth -= ch in ")]"
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    names = set()
    for p in parts:
        p = p.strip()
        if p:
            names.add(p.split("=")[0].strip() if re.match(r"^\w+\s*=", p) else p.split(".")[-1].strip())
    return names


def test_projected_columns_parser_on_known_query():
    cols = projected_columns(collectors.KQL_NSGS)
    assert {"id", "nicRefs", "subnetRefs", "tags"} <= cols and "nicCount" not in cols


def _used_columns():
    used: dict[str, set] = {}
    for m, _ in checks.REGISTRY:
        for c in _cases(m):
            for name, data in c["snapshot"].items():
                for row in data.get("rows", []) if isinstance(data, dict) else []:
                    used.setdefault(name, set()).update(row)
    for name, rows in ms.estate().items():
        for row in rows:
            used.setdefault(name, set()).update(row)
    return used


@pytest.mark.parametrize("name", sorted(n for n in _used_columns() if n in collectors.COLLECTORS))
def test_columns_in_fixtures_are_projected_by_the_collector(name):
    extra = _used_columns()[name] - projected_columns(collectors.COLLECTORS[name])
    assert not extra, f"{name}: fixture/synthetic columns not projected by its KQL: {sorted(extra)}"


def test_every_column_a_check_reads_exists_in_its_kql():
    """Static: r.get('x') / r['x'] literals in checks_builtin.py must be projected by at least one collector the check declares."""
    src = (ROOT / "src" / "fcat" / "checks_builtin.py").read_text() + (ROOT / "src" / "fcat" / "checks_governance.py").read_text()
    cols_all = set()
    for kql in collectors.COLLECTORS.values():
        cols_all |= projected_columns(kql)
    cols_all |= {
        "cost_management",
        "properties",
        "managedDisk",
        "vhd",
        "rows",
        "skipped",
        "window",
        "hours",
        "targetSize",
        "targetVcpus",
        "vcpus",
        "size",
    }  # keys of the REST-collected vm_cpu snapshot, not ARG columns  # not row columns: result key and nested ARM keys read inside dynamic columns
    read = set(re.findall(r'\b(?:r|d|s|n|v|p|c)\.get\("(\w+)"', src)) | set(re.findall(r'\b(?:r|d|s|n|v)\["(\w+)"\]', src))
    assert read, "parser found nothing; test is broken"
    assert not (read - cols_all), f"checks read columns no collector projects: {sorted(read - cols_all)}"
