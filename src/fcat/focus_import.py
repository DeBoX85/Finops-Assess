"""Offline import of a customer-provided FOCUS cost file (CSV or CSV.gz). No Azure access, no permissions needed.
Columns follow the Microsoft Learn FOCUS cost and usage details schema (read 2026-10-18):
https://learn.microsoft.com/en-us/azure/cost-management-billing/dataset-schema/cost-usage-details-focus
Output is aggregated, so the snapshot holds totals per service, subscription and resource, not raw rows."""

from __future__ import annotations

import csv
import gzip
import io
import pathlib

from .errors import FcatError

REQUIRED = ("BilledCost", "BillingCurrency", "ChargePeriodStart", "ServiceName", "SubAccountId")
# Present from FOCUS 1.0 onward; absent in 1.0-preview. 1.0 and 1.2-preview are not told apart here (UNVERIFIED which columns differ at file level).
COST_COLUMNS = ("BilledCost", "EffectiveCost", "ListCost", "ContractedCost")


def _open(path: pathlib.Path):
    raw = path.read_bytes()
    if path.suffix == ".gz":
        raw = gzip.decompress(raw)
    return io.StringIO(raw.decode("utf-8-sig"))


def _num(v):
    try:
        return float(v) if v not in (None, "") else None
    except ValueError:
        return None


def import_files(paths) -> dict:
    files = []
    for p in map(pathlib.Path, paths):
        files.extend(sorted(p.glob("*.csv*")) if p.is_dir() else [p])
    if not files:
        raise FcatError("no FOCUS csv files found")
    totals = {c: 0.0 for c in COST_COLUMNS}
    missing_cols: set[str] = set()
    by = {"service": {}, "subscription": {}, "resource": {}}
    currencies: set[str] = set()
    rows = bad = 0
    first = last = None
    present: set[str] = set()
    for f in files:
        rd = csv.DictReader(_open(f))
        cols = set(rd.fieldnames or [])
        present |= cols
        miss = [c for c in REQUIRED if c not in cols]
        if miss:
            raise FcatError(f"{f.name}: missing required FOCUS columns {miss}; not a FOCUS cost file")
        for r in rd:
            billed = _num(r["BilledCost"])
            if billed is None:
                bad += 1
                continue
            rows += 1
            currencies.add(r["BillingCurrency"])
            day = r["ChargePeriodStart"][:10]
            first = day if first is None or day < first else first
            last = day if last is None or day > last else last
            vals = {c: _num(r.get(c)) for c in COST_COLUMNS}
            for c, v in vals.items():
                if v is not None:
                    totals[c] += v
            for dim, key in (("service", r["ServiceName"]), ("subscription", r["SubAccountId"]), ("resource", r.get("ResourceId") or "")):
                if not key:
                    continue
                agg = by[dim].setdefault(key, {c: 0.0 for c in COST_COLUMNS})
                for c, v in vals.items():
                    if v is not None:
                        agg[c] += v
    for c in COST_COLUMNS:
        if c not in present:
            missing_cols.add(c)
    if len(currencies) > 1:
        raise FcatError(f"mixed billing currencies {sorted(currencies)}; refusing to add them together")
    r2 = lambda d: {k: {c: round(v, 6) for c, v in a.items()} for k, a in sorted(d.items())}  # noqa: E731
    return {
        "rows": rows,
        "unparseable_rows": bad,
        "currency": next(iter(currencies), None),
        "period": {"first_day": first, "last_day": last},
        "totals": {c: round(v, 6) for c, v in totals.items() if c not in missing_cols},
        "columns_missing": sorted(missing_cols),
        "by_service": r2(by["service"]),
        "by_subscription": r2(by["subscription"]),
        "by_resource": r2(by["resource"]),
        "note": "Aggregated from a customer-provided FOCUS file. Open-month rows are estimates. CSP customers: costs may be retail rates (see docs/KB/notes/10).",
    }
