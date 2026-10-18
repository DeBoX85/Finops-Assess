"""Azure Monitor metrics and compute SKU reads for peak-aware rightsizing (docs/RIGHTSIZING.md). Opt-in: [run] rightsizing = true.
Only GET calls on management.azure.com, which the read-only allowlist already permits (no decision record needed).
VERIFIED on Learn 2026-10-18: Metrics - List REST API (GET {resourceUri}/providers/Microsoft.Insights/metrics, api-version 2018-01-01, default ARM throttling,
response value[].timeseries[].data[] with timeStamp, average, maximum, and a per-metric errorCode); Resource Skus - List (GET /subscriptions/{id}/providers/Microsoft.Compute/skus,
$filter=location eq '...', vCPUs capability). UNVERIFIED live: that Maximum at PT1H is the maximum of the one-minute values, throttling in practice, SKU list size and paging."""

from __future__ import annotations

import datetime as dt
import re
from urllib.parse import quote, urlencode

from .rightsize import Point, assess_cpu

METRICS_API = "2018-01-01"
SKUS_API = "2021-07-01"
CPU_METRIC = "Percentage CPU"
WINDOW_DAYS = 30
DEFAULT_MAX_VMS = 50
RUNNING = "powerstate/running"


def window(collected_at: dt.datetime, days: int = WINDOW_DAYS):
    """End is the collection time floored to the hour; start is `days` before. Never the wall clock."""
    end = collected_at.astimezone(dt.UTC).replace(minute=0, second=0, microsecond=0)
    return end - dt.timedelta(days=days), end


def _iso(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def metrics_url(resource_id: str, start: dt.datetime, end: dt.datetime) -> str:
    q = {
        "timespan": f"{_iso(start)}/{_iso(end)}",
        "interval": "PT1H",
        "metricnames": CPU_METRIC,
        "aggregation": "Average,Maximum",
        "api-version": METRICS_API,
    }
    return f"https://management.azure.com{resource_id}/providers/Microsoft.Insights/metrics?{urlencode(q, quote_via=quote)}"


def skus_url(subscription_id: str, location: str) -> str:
    q = {"api-version": SKUS_API, "$filter": f"location eq '{location}'"}
    return f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Compute/skus?{urlencode(q, quote_via=quote)}"


def parse_cpu_response(body, start: dt.datetime):
    """-> (points, error). Points are hourly (max, avg) with the hour counted from `start`; points missing either value are dropped, never zero-filled."""
    if not isinstance(body, dict) or not isinstance(body.get("value"), list):
        return [], "unexpected response shape"
    for m in body["value"]:
        if not isinstance(m, dict) or (m.get("name") or {}).get("value") != CPU_METRIC:
            continue
        code = m.get("errorCode")
        if code not in (None, "Success"):
            return [], f"metric error {code}"
        series = m.get("timeseries")
        if not isinstance(series, list) or not series or not isinstance(series[0], dict):
            return [], "no time series (VM may have been stopped for the whole window)"
        pts = {}
        for d in series[0].get("data") or []:
            if not isinstance(d, dict):
                continue
            mx, av = d.get("maximum"), d.get("average")
            ok = all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in (mx, av))
            try:
                t = dt.datetime.fromisoformat(str(d.get("timeStamp")).replace("Z", "+00:00"))
            except ValueError:
                continue
            if ok:
                pts[int((t - start).total_seconds() // 3600)] = Point(int((t - start).total_seconds() // 3600), float(mx), float(av))
        return [pts[k] for k in sorted(pts)], None
    return [], "CPU metric not present in response"


def parse_skus(pages) -> dict:
    """pages: list of response bodies. -> {sku name: vCPUs} for virtualMachines only."""
    out = {}
    for body in pages:
        for s in (body or {}).get("value", []) if isinstance(body, dict) else []:
            if not isinstance(s, dict) or str(s.get("resourceType") or "").lower() != "virtualmachines":
                continue
            for c in s.get("capabilities") or []:
                if isinstance(c, dict) and c.get("name") == "vCPUs":
                    try:
                        out[str(s.get("name"))] = int(c.get("value"))
                    except (TypeError, ValueError):
                        pass
    return out


_SIZE = re.compile(r"(Standard_[A-Za-z]+?)(\d+)(.*)")


def smaller_size(name: str, vcpus_by_name: dict):
    """Same family and suffix with half the vCPUs, or None when there is not exactly one such size (constrained-core, odd counts, burstable B-series
    are deliberately not handled: unknown is better than a wrong target)."""
    m = _SIZE.fullmatch(name or "")
    cur = vcpus_by_name.get(name)
    if not m or not cur or cur < 2 or cur % 2 or name.startswith("Standard_B"):
        return None
    want = cur // 2
    hits = [
        n
        for n, v in vcpus_by_name.items()
        if v == want and (mm := _SIZE.fullmatch(n)) and mm.group(1) == m.group(1) and mm.group(3) == m.group(3)
    ]
    return hits[0] if len(hits) == 1 else None


def _get_pages(client, url, limit=20):
    pages = []
    while url and len(pages) < limit:
        r = client.request("GET", url)
        if r.status != 200:
            return pages, f"HTTP {r.status}"
        pages.append(r.body)
        url = (r.body or {}).get("nextLink") if isinstance(r.body, dict) else None
    return pages, None


def collect_rightsizing(client, snapshot, config, errors: list, collected_at: dt.datetime):
    """Writes snapshot 'vm_cpu': {'rows': [...], 'skipped': [{'id','reason'}], 'cap': n, 'considered': n, 'window': {...}}.
    Running VMs only (stopped VMs emit no metrics), at most config.rightsizing_max_vms of them, chosen by id order."""
    start, end = window(collected_at)
    vms = [v for v in (snapshot.load("vms") or {}).get("rows", []) if str(v.get("powerState") or "").lower() == RUNNING]
    vms.sort(key=lambda v: str(v.get("id")))
    cap = getattr(config, "rightsizing_max_vms", DEFAULT_MAX_VMS)
    chosen = vms[:cap]
    skus: dict = {}
    rows, skipped = [], []
    for v in chosen:
        vid, size = v["id"], str(v.get("vmSize") or "")
        sub, loc = str(v.get("subscriptionId") or ""), str(v.get("location") or "")
        if (sub, loc) not in skus:
            pages, err = _get_pages(client, skus_url(sub, loc))
            skus[(sub, loc)] = parse_skus(pages) if not err else None
            if err:
                errors.append({"collector": "vm_cpu", "error": f"SKU list for a location failed: {err}"})
        table = skus[(sub, loc)]
        if not table or size not in table:
            skipped.append({"id": vid, "reason": "vCPU count for this size is unknown (SKU list unavailable or size not listed)"})
            continue
        target = smaller_size(size, table)
        if target is None:
            skipped.append({"id": vid, "reason": "no single half-size in the same family (or burstable/odd size); not assessed"})
            continue
        r = client.request("GET", metrics_url(vid, start, end))
        if r.status != 200:
            skipped.append({"id": vid, "reason": f"metrics call failed: HTTP {r.status}"})
            continue
        pts, err = parse_cpu_response(r.body, start)
        if err:
            skipped.append({"id": vid, "reason": err})
            continue
        rows.append(
            {
                "id": vid,
                "vmSize": size,
                "targetSize": target,
                "vcpus": table[size],
                "targetVcpus": table[target],
                "points": [[p.hour_index, p.cpu_max, p.cpu_avg] for p in pts],
            }
        )
    snapshot.save(
        "vm_cpu",
        {
            "rows": rows,
            "skipped": skipped,
            "cap": cap,
            "considered": len(chosen),
            "running_total": len(vms),
            "window": {"start": _iso(start), "end": _iso(end), "hours": WINDOW_DAYS * 24},
        },
    )


def assess_row(row, window_hours, limit_pct: float = 60.0):
    """Returns the assess_cpu result, or None when the stored row is malformed (never raises on bad data)."""
    try:
        v, t = row["vcpus"], row["targetVcpus"]
        if not all(isinstance(x, int) and not isinstance(x, bool) and x > 0 for x in (v, t)) or t >= v or not isinstance(window_hours, int):
            return None
        pts = [Point(int(h), float(mx), float(av)) for h, mx, av in row["points"]]
    except (KeyError, TypeError, ValueError):
        return None
    return assess_cpu(pts, window_hours, v, t, limit_pct=limit_pct)
