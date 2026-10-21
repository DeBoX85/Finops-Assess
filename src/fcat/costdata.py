"""Cost data collector (ADR 0006 stage 1, opt-in `[run] cost_apis = true`). Design: docs/COST-DATA.md.

One Cost Management Query per enabled subscription: ActualCost, last full calendar month, grouped by ResourceId. Nothing is written to Azure.
Learn facts (REST reference Query - Usage, api-version 2026-06-01, read 2026-10-21):
- POST {scope}/providers/Microsoft.CostManagement/query?api-version=...; body type (Usage | ActualCost | AmortizedCost ...), timeframe (TheLastMonth
  ...), dataset.aggregation (alias -> {name, function: Sum}, at most 2), dataset.granularity, dataset.grouping [{name, type: Dimension}].
- 200 result: properties.columns [{name, type}], properties.rows, properties.nextLink. 204 means no content. 429 carries
  x-ms-ratelimit-microsoft.consumption-retry-after.
UNVERIFIED live: the name of the cost column (the samples show PreTaxCost on legacy scopes; MCA may say Cost), the case of ResourceId values,
whether nextLink must be followed with POST and the same body, throttling at scale, and the value 'ActualCost' being accepted on every offer type.
So the parser reads columns BY NAME and refuses to guess; an unexpected shape is an error, never a zero."""

from __future__ import annotations

from urllib.parse import quote

API = "2026-06-01"
BASE = "https://management.azure.com"
PAGE_LIMIT = 20
COST_COLUMNS = ("Cost", "PreTaxCost")  # first one present wins
RESOURCE_COLUMN = "ResourceId"
CURRENCY_COLUMN = "Currency"


def query_url(sub):
    return f"{BASE}/subscriptions/{quote(sub)}/providers/Microsoft.CostManagement/query?api-version={API}"


def query_body(timeframe="TheLastMonth"):
    return {
        "type": "ActualCost",
        "timeframe": timeframe,
        "dataset": {
            "granularity": "None",
            "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
            "grouping": [{"type": "Dimension", "name": RESOURCE_COLUMN}],
        },
    }


def project_rows(sub, props):
    """Turns one result page into rows. Returns (rows, error). Columns are located by name; a missing cost or resource column is an error."""
    cols = props.get("columns") if isinstance(props, dict) else None
    rows = props.get("rows") if isinstance(props, dict) else None
    if not isinstance(cols, list) or not isinstance(rows, list):
        return [], "response has no columns/rows"
    names = [c.get("name") if isinstance(c, dict) else None for c in cols]
    cost_at = next((names.index(n) for n in COST_COLUMNS if n in names), None)
    if cost_at is None or RESOURCE_COLUMN not in names:
        return [], f"unexpected columns {[n for n in names if isinstance(n, str)][:8]}"
    res_at = names.index(RESOURCE_COLUMN)
    cur_at = names.index(CURRENCY_COLUMN) if CURRENCY_COLUMN in names else None
    out, bad = [], 0
    for r in rows:
        if not isinstance(r, list) or len(r) <= max(cost_at, res_at):
            bad += 1
            continue
        cost = r[cost_at]
        if isinstance(cost, bool) or not isinstance(cost, (int, float)):
            bad += 1
            continue
        rid = r[res_at]
        cur = r[cur_at] if cur_at is not None and len(r) > cur_at else None
        out.append(
            {
                "subscriptionId": sub,
                "resourceId": rid.strip().lower() if isinstance(rid, str) else "",
                "cost": float(cost),
                "currency": cur if isinstance(cur, str) else None,
            }
        )
    if bad:  # dropping rows would understate the subscription total and skew every share built on it
        return [], f"{bad} of {len(rows)} rows had an unexpected shape or a non-numeric cost, so the subscription total cannot be trusted"
    return out, None


def _query_sub(client, sub, timeframe):
    """Follows nextLink up to PAGE_LIMIT pages. Returns (rows, truncated, error)."""
    rows: list = []
    url = query_url(sub)
    for _ in range(PAGE_LIMIT):
        r = client.request("POST", url, query_body(timeframe))
        if r.status == 204:
            return rows, False, None
        if r.status != 200 or not isinstance(r.body, dict):
            return rows, False, f"HTTP {r.status}"
        props = r.body.get("properties")
        got, err = project_rows(sub, props)
        if err:
            return rows, False, err
        rows += got
        url = props.get("nextLink") if isinstance(props, dict) else None
        if not url:
            return rows, False, None
    return rows, True, None


def collect_cost(client, snapshot, config, errors: list, timeframe="TheLastMonth"):
    """Writes snapshot 'cost_by_resource': {'rows', 'scopes': [{'subscriptionId', 'status', 'truncated'}], 'timeframe', 'api_version'}.
    Zero successful scopes writes nothing and records an error, so checks say 'not assessed' (lesson M-008)."""
    if not snapshot.has("subscriptions"):
        errors.append(
            {"collector": "cost_by_resource", "error": "subscription inventory (subscriptions) is missing, so no scope could be selected"}
        )
        return
    subs = sorted(
        {
            r["subscriptionId"]
            for r in (snapshot.load("subscriptions") or {}).get("rows", [])
            if isinstance(r, dict)
            and isinstance(r.get("subscriptionId"), str)
            and r["subscriptionId"]
            and str(r.get("state") or "Enabled").lower() == "enabled"
        }
    )
    if not subs:
        errors.append({"collector": "cost_by_resource", "error": "no enabled subscription found in the inventory"})
        return
    rows, scopes = [], []
    for sub in subs:
        got, truncated, err = _query_sub(client, sub, timeframe)
        scopes.append({"subscriptionId": sub, "status": "ok" if not err else err, "truncated": bool(truncated)})
        if err:
            errors.append({"collector": "cost_by_resource", "error": f"subscription {sub}: {err}"})
            continue
        rows += got
    if not any(s["status"] == "ok" for s in scopes):
        return
    rows.sort(key=lambda r: (r["subscriptionId"], r["resourceId"]))
    snapshot.save("cost_by_resource", {"rows": rows, "scopes": scopes, "timeframe": timeframe, "api_version": API})
