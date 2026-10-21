"""Cost-to-inventory reconciliation (backlog 33, KB 14 gap G1). Needs the opt-in `[run] cost_apis = true` collectors (costdata.py, resource_ids).
Offline-only until gate G2 passes. Design and limits: docs/COST-DATA.md."""

import dataclasses

from .checks import Finding, NotAssessed, check
from .checks_builtin import _cm

SHARE_THRESHOLD = 0.05  # report when at least 5 percent of a subscription's cost is unmapped. My judgement, not a Microsoft figure.
TOP_N = 5


# Cost Management Reader (KB 11: its actions include Microsoft.CostManagement/*/read) for the Query, Reader for the Resource Graph id list. On EA and MCA
# billing the view-charges settings can also block cost reads even with the role: UNVERIFIED, first G2 item for this check.
_META = dataclasses.replace(
    _cm(
        "COST-UNMAP-01",
        "billing",
        "Allocation",
        "Cost on resources missing from the inventory, or with no resource id",
        "cost_by_resource",
        "resource_ids",
        conf="low",
    ),
    permissions=("Cost Management Reader", "Reader"),
)


@check(_META)
def unmapped_cost(snap):
    """Per subscription, for the last full month: cost whose ResourceId is not in the Resource Graph id list (deleted since, or a type or scope we did
    not list) and cost with an empty ResourceId (support, marketplace, reservations and similar lines may have none: UNVERIFIED which). Neither is
    waste on its own, so this is a prompt to explain the money, never a saving. Refuses to decide when the id list is truncated, a subscription's
    call failed, or one subscription reports more than one currency."""
    if not snap.has("cost_by_resource") or not snap.has("resource_ids"):
        raise NotAssessed("needs [run] cost_apis = true; the cost query or the resource id list did not produce data")
    cost = snap.load("cost_by_resource") or {}
    ids = snap.load("resource_ids") or {}
    rows = [r for r in ids.get("rows") or [] if isinstance(r, dict)] if isinstance(ids.get("rows"), list) else []
    total = ids.get("total_records")
    if isinstance(total, int) and total > len(rows):
        raise NotAssessed(f"the resource id list is incomplete ({len(rows)} of {total} rows), so absence from it proves nothing")
    known = {r["id"].lower() for r in rows if isinstance(r.get("id"), str)}
    scopes = [s for s in cost.get("scopes") or [] if isinstance(s, dict)]
    ok = {
        s["subscriptionId"]
        for s in scopes
        if s.get("status") == "ok" and not s.get("truncated") and isinstance(s.get("subscriptionId"), str)
    }
    if not ok:
        raise NotAssessed("no subscription cost query completed (all failed or were cut off at the page limit)")
    by_sub: dict = {}
    for r in cost.get("rows") or []:  # a malformed row is skipped, never guessed at
        if (
            isinstance(r, dict)
            and isinstance(r.get("subscriptionId"), str)
            and r["subscriptionId"] in ok
            and isinstance(r.get("resourceId"), str)
            and isinstance(r.get("cost"), (int, float))
            and not isinstance(r.get("cost"), bool)
            and (r.get("currency") is None or isinstance(r.get("currency"), str))
        ):
            by_sub.setdefault(r["subscriptionId"], []).append(r)
    mixed = sorted(sid for sid, rs in by_sub.items() if len({x.get("currency") for x in rs}) > 1)
    if mixed:
        raise NotAssessed(f"{len(mixed)} subscription(s) report more than one currency, and amounts are never added across currencies")
    for sid in sorted(by_sub):
        rs = by_sub[sid]
        sub_total = sum(x["cost"] for x in rs)
        if sub_total <= 0:
            continue
        noid = [x for x in rs if not x["resourceId"]]
        gone = sorted((x for x in rs if x["resourceId"] and x["resourceId"] not in known), key=lambda x: -x["cost"])
        gone_cost, noid_cost = sum(x["cost"] for x in gone), sum(x["cost"] for x in noid)
        share = (gone_cost + noid_cost) / sub_total
        if share < SHARE_THRESHOLD:
            continue
        cur = rs[0].get("currency")
        yield Finding(
            "COST-UNMAP-01",
            f"/subscriptions/{sid}",
            "info",
            f"{share:.0%} of last month's cost ({cur}) sits on resources missing from the inventory or on lines without a resource id: explain it before using cost-per-resource views",
            {
                "currency": cur,
                "subscription_cost": round(sub_total, 2),
                "missing_from_inventory_cost": round(gone_cost, 2),
                "missing_from_inventory_resources": len(gone),
                "no_resource_id_cost": round(noid_cost, 2),
                "top_missing": [{"id": x["resourceId"], "cost": round(x["cost"], 2)} for x in gone[:TOP_N]],
                "threshold_share": SHARE_THRESHOLD,
                "period": cost.get("timeframe"),
            },
        )
