"""Cost governance collectors, phase 2: budgets, anomaly alert rules, cost exports (GET only, Reader). Design: docs/COST-GOVERNANCE.md.

Learn facts (read 2026-10-20), all api-version 2026-06-01:
- Budgets: GET {scope}/providers/Microsoft.Consumption/budgets. properties: amount, category, timeGrain, timePeriod.startDate/endDate,
  currentSpend, forecastSpend, notifications (a dictionary keyed by name; each has enabled, operator, threshold, thresholdType,
  contactEmails, contactRoles, contactGroups).
- Scheduled actions: GET {scope}/providers/Microsoft.CostManagement/scheduledActions (shared actions only). kind Email | InsightAlert,
  properties.status Enabled | Expired | Disabled. Anomaly alert rules are kind InsightAlert, subscription scope only.
- Exports: GET {scope}/providers/Microsoft.CostManagement/exports?$expand=runHistory. properties.schedule.status Active | Inactive,
  properties.runHistory.value[].properties.status (Queued, InProgress, Completed, Failed, Timeout, NewDataNotAvailable, DataNotAvailable).
UNVERIFIED live: whether a Reader sees anomaly rules created as private actions, whether the budget list at subscription scope also returns
resource group budgets, throttling at scale, and the exact shape of notifications on a real response.

Privacy (docs/COST-GOVERNANCE.md section 6): e-mail addresses, contact groups, storage account ids, containers and folders are NEVER copied
into the snapshot. Only booleans and counts. Projection functions below are the single place that decides what is kept."""

from __future__ import annotations

from urllib.parse import quote

API = "2026-06-01"
BASE = "https://management.azure.com"
PAGE_LIMIT = 20


def _get_pages(client, url, limit=PAGE_LIMIT):
    pages = []
    while url and len(pages) < limit:
        r = client.request("GET", url)
        if r.status != 200:
            return pages, f"HTTP {r.status}"
        pages.append(r.body)
        url = r.body.get("nextLink") if isinstance(r.body, dict) else None
    return pages, None


def _items(pages):
    for p in pages:
        for it in (p or {}).get("value") or [] if isinstance(p, dict) else []:
            if isinstance(it, dict):
                yield it


def budgets_url(sub):
    return f"{BASE}/subscriptions/{quote(sub)}/providers/Microsoft.Consumption/budgets?api-version={API}"


def scheduled_actions_url(sub):
    return f"{BASE}/subscriptions/{quote(sub)}/providers/Microsoft.CostManagement/scheduledActions?api-version={API}"


def exports_url(sub):
    return f"{BASE}/subscriptions/{quote(sub)}/providers/Microsoft.CostManagement/exports?api-version={API}&$expand=runHistory"


def _props(item):
    p = item.get("properties")
    return p if isinstance(p, dict) else {}


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _nonempty(v):
    return isinstance(v, list) and any(isinstance(x, str) and x.strip() for x in v)


def project_budget(sub, item):
    p = _props(item)
    n = p.get("notifications")
    notes = list(n.values()) if isinstance(n, dict) else (n if isinstance(n, list) else [])
    out = []
    for x in notes:
        if not isinstance(x, dict):
            continue
        out.append(
            {
                "enabled": x.get("enabled") is True,
                "operator": x.get("operator") if isinstance(x.get("operator"), str) else None,
                "threshold": _num(x.get("threshold")),
                "thresholdType": x.get("thresholdType") if isinstance(x.get("thresholdType"), str) else "Actual",
                "hasEmail": _nonempty(x.get("contactEmails")),
                "hasRole": _nonempty(x.get("contactRoles")),
                "hasGroup": _nonempty(x.get("contactGroups")),
            }
        )
    tp = p.get("timePeriod") if isinstance(p.get("timePeriod"), dict) else {}
    bid = str(item.get("id") or "")
    return {
        "id": bid,
        "subscriptionId": sub,
        "name": item.get("name"),
        "level": "resourceGroup" if "/resourcegroups/" in bid.lower() else "subscription",
        "amount": _num(p.get("amount")),
        "category": p.get("category"),
        "timeGrain": p.get("timeGrain"),
        "startDate": tp.get("startDate"),
        "endDate": tp.get("endDate"),
        "currentSpend": _num((p.get("currentSpend") or {}).get("amount")) if isinstance(p.get("currentSpend"), dict) else None,
        "notifications": out,
    }


def project_scheduled_action(sub, item):
    p = _props(item)
    return {
        "id": str(item.get("id") or ""),
        "subscriptionId": sub,
        "name": item.get("name"),
        "kind": item.get("kind"),
        "status": p.get("status"),
        "viewId": p.get("viewId"),
        "frequency": (p.get("schedule") or {}).get("frequency") if isinstance(p.get("schedule"), dict) else None,
        "endDate": (p.get("schedule") or {}).get("endDate") if isinstance(p.get("schedule"), dict) else None,
        "hasRecipient": _nonempty((p.get("notification") or {}).get("to")) if isinstance(p.get("notification"), dict) else False,
    }


def project_export(sub, item):
    p = _props(item)
    d = p.get("definition") if isinstance(p.get("definition"), dict) else {}
    s = p.get("schedule") if isinstance(p.get("schedule"), dict) else None
    runs = (
        [r for r in ((p.get("runHistory") or {}).get("value") or []) if isinstance(r, dict)]
        if isinstance(p.get("runHistory"), dict)
        else []
    )
    last = None
    if runs:
        last = max(runs, key=lambda r: str(_props(r).get("processingEndTime") or _props(r).get("submittedTime") or ""))
    lp = _props(last) if last else {}
    return {
        "id": str(item.get("id") or ""),
        "subscriptionId": sub,
        "name": item.get("name"),
        "exportType": d.get("type"),
        "format": p.get("format"),
        "hasSchedule": s is not None,
        "scheduleStatus": s.get("status") if s else None,
        "recurrence": s.get("recurrence") if s else None,
        "runHistoryReturned": isinstance(p.get("runHistory"), dict),
        "lastRunStatus": lp.get("status") if last else None,
        "lastRunEnd": lp.get("processingEndTime") if last else None,
        "lastRunErrorCode": (lp.get("error") or {}).get("code") if isinstance(lp.get("error"), dict) else None,
    }


_PROJECT = {"budgets": project_budget, "anomaly_rules": project_scheduled_action, "cost_exports": project_export}
_URL = {"budgets": budgets_url, "anomaly_rules": scheduled_actions_url, "cost_exports": exports_url}
GOVERNANCE_REST = tuple(_PROJECT)


def collect_governance(client, snapshot, config, errors: list):
    """Writes snapshots 'budgets', 'anomaly_rules', 'cost_exports': {'rows': [...], 'scopes': [{'subscriptionId', 'status'}], 'api_version'}.
    'scopes' says for every subscription whether the call worked. A collector with zero successful scopes writes nothing and records an error,
    so the checks report 'not assessed' and never an empty pass (lesson M-008)."""
    if not snapshot.has("subscriptions"):
        for name in GOVERNANCE_REST:
            errors.append({"collector": name, "error": "subscription inventory (subscriptions) is missing, so no scope could be selected"})
        return
    subs = []
    for r in (snapshot.load("subscriptions") or {}).get("rows", []):
        sid = r.get("subscriptionId") if isinstance(r, dict) else None
        if isinstance(sid, str) and sid and str(r.get("state") or "Enabled").lower() == "enabled":
            subs.append(sid)
    subs = sorted(set(subs))
    if not subs:
        for name in GOVERNANCE_REST:
            errors.append({"collector": name, "error": "no enabled subscription found in the inventory"})
        return
    for name in GOVERNANCE_REST:
        rows, scopes = [], []
        for sub in subs:
            pages, err = _get_pages(client, _URL[name](sub))
            scopes.append({"subscriptionId": sub, "status": "ok" if not err else err})
            if err:
                errors.append({"collector": name, "error": f"subscription {sub}: {err}"})
                continue
            rows += [_PROJECT[name](sub, it) for it in _items(pages)]
        if not any(s["status"] == "ok" for s in scopes):
            continue  # nothing usable: no snapshot, so the checks say 'not assessed' instead of passing on empty data
        rows.sort(key=lambda r: r["id"])
        snapshot.save(name, {"rows": rows, "scopes": scopes, "api_version": API})
