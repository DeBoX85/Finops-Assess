"""Cost governance checks, phase 1 (tags and tag policy) and phase 2 (budgets, anomaly alert rules, cost exports; bottom of file). Design: docs/COST-GOVERNANCE.md. Evidence: docs/KB/notes/11-cost-governance-azure.md.
Everything here is offline-only (UNVERIFIED live): ARG property names for policy assignments, null versus empty tags, and compliance
data timing. Thresholds are our proposals and are echoed in the finding details. Tag values appear only under the details keys named in
redact.TAG_VALUE_KEYS so that --redact can mask them."""

from __future__ import annotations

import datetime as dt
from collections import Counter

from . import tags as T
from .checks import CheckMeta, Finding, NotAssessed, check, collected_at


def _g(id_, framework, title, *collectors, conf="medium"):
    return CheckMeta(
        id=id_, domain="governance", title=title, collectors=collectors, permissions=("Reader",),
        savings_basis="none", confidence=conf, framework=framework,
    )  # fmt: skip


def _rows(snap, name):
    return (snap.load(name) or {}).get("rows", [])


def _policies(snap):
    return T.tag_policies(_rows(snap, "policy_assignments")) if snap.has("policy_assignments") else None


def _scheme(snap):
    inv = T.inventory(_rows(snap, "tag_inventory"))
    return inv, T.scheme(inv, _policies(snap) or [])


@check(_g("TAG-DISC-01", "Allocation", "Tagging scheme found in the environment", "tag_inventory"))
def tag_scheme(snap):
    """Reports what the customer actually does: keys, coverage, where the scheme came from. Nothing is judged against a built-in list.
    No tags at all, or no key shared widely enough to call a scheme, is the finding ('if at all')."""
    inv, sch = _scheme(snap)
    if not inv["total"]:
        raise NotAssessed("no resources were returned by the inventory query")
    cov = {
        k: {"resources": e["resources"], "percent": round(100.0 * e["resources"] / inv["total"], 1), "casings": sorted(e["casings"])}
        for k, e in inv["keys"].items()
    }
    top = dict(sorted(cov.items(), key=lambda kv: (-kv[1]["resources"], kv[0]))[:25])
    d = {
        "scheme_source": sch["source"],
        "scheme_keys": sch["keys"],
        "declared_by_policy": sch["declared"],
        "inferred_keys": sch["inferred"],
        "resources": inv["total"],
        "resources_with_any_tag": inv["tagged"],
        "distinct_keys": len(inv["keys"]),
        "top_keys": top,
        "inference_rule": f"a key is in the inferred scheme when at least {T.SCHEME_SHARE_PCT}% of resources carry it (our proposal)",
        "policy_data": "collected" if snap.has("policy_assignments") else "not collected, so a declared standard could not be looked for",
    }
    if inv["tagged"] == 0:
        yield Finding("TAG-DISC-01", "tags:scheme", "medium", f"No tags found on any of {inv['total']} resources", d)
    elif sch["source"] == "none":
        yield Finding(
            "TAG-DISC-01", "tags:scheme", "medium",
            f"Tags exist ({len(inv['keys'])} distinct keys) but no key is shared widely enough to call a tagging scheme", d,
        )  # fmt: skip
    else:
        yield Finding(
            "TAG-DISC-01", "tags:scheme", "info",
            f"Tagging scheme found ({sch['source']}): {', '.join(sch['keys'])}", d,
        )  # fmt: skip


@check(_g("TAG-COV-01", "Allocation", "Subscriptions where many resources lack the tagging scheme keys", "tag_inventory"))
def tag_coverage(snap):
    """Measured against the customer's own scheme (see TAG-DISC-01). Types that never carry a tag (some resource types do not support tags;
    Learn tag-support list not parsed yet) are NOT excluded; the top untagged types are shown so a reader can judge."""
    inv, sch = _scheme(snap)
    if not inv["total"]:
        raise NotAssessed("no resources were returned by the inventory query")
    if sch["source"] == "none":
        return  # TAG-DISC-01 already reports that no scheme is evident
    by_sub: dict = {}
    for row in _rows(snap, "tag_inventory"):
        if isinstance(row, dict):
            by_sub.setdefault(T.sub_of(row), []).append(row)
    for sub, rows in sorted(by_sub.items()):
        total = len(rows)
        if total < T.MIN_RESOURCES:
            continue
        missing = 0
        per_key = Counter()
        untagged_types = Counter()
        for row in rows:
            have = {k.lower() for k in T.tags_of(row)}
            if any(k not in have for k in sch["keys"]):
                missing += 1
                untagged_types[str(row.get("type") or "").lower()] += 1
            per_key.update(k for k in sch["keys"] if k in have)
        pct = 100.0 * missing / total
        if pct < T.GAP_PCT:
            continue
        yield Finding(
            "TAG-COV-01", f"/subscriptions/{sub}", "medium" if pct >= 50 else "low",
            f"{missing} of {total} resources lack at least one scheme tag ({pct:.0f}%)",
            {
                "scheme_source": sch["source"],
                "scheme_keys": sch["keys"],
                "resources": total,
                "missing_any_scheme_key": missing,
                "percent_missing": round(pct, 1),
                "per_key_coverage_percent": {k: round(100.0 * per_key[k] / total, 1) for k in sch["keys"]},
                "top_types_lacking": dict(untagged_types.most_common(5)),
                "rule": f"reported when at least {T.GAP_PCT}% of resources lack a scheme key and the subscription has at least {T.MIN_RESOURCES} resources (our proposal)",
                "caveat": "some resource types do not support tags; the type list is not applied yet",
            },
        )  # fmt: skip


@check(_g("TAG-CASE-01", "Allocation", "Same tag name written with different capitalisation", "tag_inventory"))
def tag_name_casing(snap):
    """Learn: tag names are case-insensitive for operations, but the provider keeps the casing it was given and that casing shows in cost reports.
    Whether Cost Management merges the variants is UNVERIFIED, so the message says 'may split'."""
    inv = T.inventory(_rows(snap, "tag_inventory"))
    for k, e in sorted(inv["keys"].items()):
        if len(e["casings"]) > 1:
            yield Finding(
                "TAG-CASE-01", f"tag:{k}", "low",
                f"Tag name '{k}' is written {len(e['casings'])} ways, which may split cost reports",
                {"casings": dict(sorted(e["casings"].items())), "resources": e["resources"]},
            )  # fmt: skip


@check(_g("TAG-VAL-01", "Allocation", "Same tag value written in different ways", "tag_inventory"))
def tag_value_variants(snap):
    """Values are case-sensitive and show as separate rows in cost reports (Learn). Variants are only values that fold together after lower-casing,
    trimming, and treating runs of space, underscore, hyphen and dot as equal. Synonyms such as prod and production are NOT inferred."""
    inv = T.inventory(_rows(snap, "tag_inventory"))
    for k, e in sorted(inv["keys"].items()):
        groups = T.value_variants(e["values"])
        if groups:
            yield Finding(
                "TAG-VAL-01", f"tag:{k}", "low",
                f"Tag '{k}' has {len(groups)} value(s) written more than one way",
                {"variants": groups, "distinct_values": len(e["values"]), "folding_rule": "lower case, trimmed, runs of space/underscore/hyphen/dot equal"},
            )  # fmt: skip


@check(
    _g(
        "TAG-RG-01",
        "Allocation",
        "Resource groups whose tags are missing on most resources inside",
        "tag_inventory",
        "container_tags",
        conf="low",
    )
)
def rg_tags_not_inherited(snap):
    """Resources do not inherit tags from their resource group (Learn). Tags on the group help cost allocation only if something copies them:
    an Azure Policy inherit or modify definition (readable here when policy data was collected) or the Cost Management tag inheritance setting
    (NOT readable yet, so it is never assumed absent: the details say so)."""
    pol = _policies(snap)
    inherit_seen = None if pol is None else any(p["kind"] in {"inherit", "modify"} for p in pol)
    by_rg: dict = {}
    for r in _rows(snap, "tag_inventory"):
        if not isinstance(r, dict):
            continue
        rid = str(r.get("id") or "").lower()
        parts = rid.split("/")
        if "resourcegroups" in parts and parts.index("resourcegroups") + 1 < len(parts):
            key = (T.sub_of(r), parts[parts.index("resourcegroups") + 1])
            by_rg.setdefault(key, []).append({k.lower() for k in T.tags_of(r)})
    for c in _rows(snap, "container_tags"):
        if not isinstance(c, dict) or "resourcegroups" not in str(c.get("type") or "").lower():
            continue
        cid = str(c.get("id") or "").lower().split("/")
        if "resourcegroups" not in cid or cid.index("resourcegroups") + 1 >= len(cid):
            continue
        key = (T.sub_of(c), cid[cid.index("resourcegroups") + 1])
        kids = by_rg.get(key, [])
        rg_keys = {k.lower() for k in T.tags_of(c)}
        if not rg_keys or len(kids) < T.RG_MIN_RESOURCES:
            continue
        lacking = {k: sum(1 for have in kids if k not in have) for k in sorted(rg_keys)}
        worst = {k: n for k, n in lacking.items() if 100.0 * n / len(kids) >= T.RG_GAP_PCT}
        if not worst:
            continue
        yield Finding(
            "TAG-RG-01", str(c.get("id")), "low",
            f"Resource group carries tag(s) {', '.join(sorted(worst))} that many of its {len(kids)} resources do not",
            {
                "resources_in_group": len(kids),
                "group_tags": sorted(rg_keys),
                "resources_lacking_each": worst,
                "inheritance_policy_seen": inherit_seen,
                "cost_management_inheritance": "not assessed, because the setting is not yet readable by this tool",
                "rule": f"reported when at least {T.RG_GAP_PCT}% of at least {T.RG_MIN_RESOURCES} resources lack a group tag (our proposal)",
            },
        )  # fmt: skip


@check(_g("POL-TAG-01", "Policy and governance", "No enforced tag policy found", "policy_assignments"))
def tag_policy_presence(snap):
    """Looks only for the built-in tag definitions listed on Learn. Custom definitions and initiatives are counted but not inspected, so 'none found' says
    exactly that. Policy assigned above the scanned scope is only seen when the query used AuthorizationScopeFilter (collector does)."""
    rows = _rows(snap, "policy_assignments")
    pol = T.tag_policies(rows)
    unclassified = sum(1 for r in rows if isinstance(r, dict) and not T.classify_assignment(r))
    d = {"assignments_total": len(rows), "assignments_not_inspected": unclassified, "tag_policies_found": len(pol)}
    if not pol:
        yield Finding(
            "POL-TAG-01", "policy:tags", "low",
            f"No built-in tag policy found among {len(rows)} policy assignments ({unclassified} custom or initiative assignments were not inspected)", d,
        )  # fmt: skip
    elif not any(p["enforced"] for p in pol):
        yield Finding(
            "POL-TAG-01", "policy:tags", "info",
            "Tag policies are assigned but none is enforced (enforcementMode DoNotEnforce)",
            {**d, "note": "Microsoft's FinOps guidance suggests starting with audit and expanding, so this can be a deliberate first step"},
        )  # fmt: skip


@check(
    _g("POL-TAGMOD-01", "Policy and governance", "Tag policies only block, nothing fills in missing tags", "policy_assignments", conf="low")
)
def tag_policy_mode(snap):
    """Deny-type tag policies stop new untagged resources only. Learn: existing resources are unchanged; modify and inherit definitions can add tags and need a
    remediation task for existing resources. Suggestion level, because blocking can be a deliberate choice."""
    pol = [p for p in T.tag_policies(_rows(snap, "policy_assignments")) if p["enforced"]]
    if pol and all(p["kind"] == "require" for p in pol):
        yield Finding(
            "POL-TAGMOD-01", "policy:tags", "info",
            "Only deny-type tag policies are enforced; no policy adds or inherits tags on existing resources",
            {"tag_policies": len(pol), "kinds": sorted({p["kind"] for p in pol})},
        )  # fmt: skip


@check(_g("POL-COMPL-01", "Policy and governance", "Tag policy non-compliance", "policy_assignments", "policy_states"))
def tag_policy_compliance(snap):
    """Non-compliant share per tag policy assignment from Policy Insights state counts. Compliance data is evaluated by Azure Policy on its own schedule,
    so recent changes may not be reflected (timing UNVERIFIED here)."""
    pol = {p["id"].lower(): p for p in T.tag_policies(_rows(snap, "policy_assignments"))}
    counts: dict = {}
    for r in _rows(snap, "policy_states"):
        if isinstance(r, dict) and isinstance(r.get("n"), int) and not isinstance(r.get("n"), bool):
            counts.setdefault(str(r.get("assignmentId") or "").lower(), Counter())[str(r.get("state") or "").lower()] += r["n"]
    for aid, p in sorted(pol.items()):
        cnt = counts.get(aid)
        if not cnt:
            continue
        total = sum(cnt.values())
        bad = cnt["noncompliant"]
        if not total or not bad:
            continue
        pct = 100.0 * bad / total
        yield Finding(
            "POL-COMPL-01", p["id"], "medium" if pct >= 50 else "low",
            f"Tag policy has {bad} of {total} evaluated resources non-compliant ({pct:.0f}%)",
            {"kind": p["kind"], "tag": p["tag"], "enforced": p["enforced"], "states": dict(cnt), "percent_noncompliant": round(pct, 1)},
        )  # fmt: skip


# ---------------------------------------------------------------------------------------------------------------------------------
# Phase 2: budgets, anomaly alert rules, cost exports. Collector: govcost.py (opt-in [run] governance_apis). All offline-only, UNVERIFIED live.
# Scope covered: subscriptions only. Management group and billing account budgets or exports are NOT collected, so every message says
# "visible at subscription scope" and never claims there is no control anywhere.

SUB_ONLY = "subscription scope only; management group and billing account scopes were not collected"


def _rest(snap, name):
    """Rows plus the sets of subscriptions whose call worked or failed. Raises NotAssessed when the collector did not run or all calls failed."""
    if not snap.has(name):
        raise NotAssessed(
            f"the {name} collector produced no data (it needs [run] governance_apis = true, and at least one successful call)"
        )
    data = snap.load(name) or {}
    scopes = [x for x in data.get("scopes") or [] if isinstance(x, dict)] if isinstance(data.get("scopes"), list) else []
    ok = {str(x.get("subscriptionId")) for x in scopes if x.get("status") == "ok"}
    if not ok:
        raise NotAssessed(f"no subscription could be read for {name}")
    failed = sorted({str(x.get("subscriptionId")) for x in scopes if x.get("status") != "ok"})
    rows = [x for x in data.get("rows") or [] if isinstance(x, dict)] if isinstance(data.get("rows"), list) else []
    return rows, ok, failed


def _date(v):
    try:
        d = dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=dt.UTC)


def _notes(bud):
    return [x for x in bud.get("notifications") or [] if isinstance(x, dict)] if isinstance(bud.get("notifications"), list) else []


def _by_sub(rows):
    out: dict = {}
    for item in rows:
        out.setdefault(str(item.get("subscriptionId")), []).append(item)
    return out


@check(_g("BUD-COVER-01", "Budgeting", "Subscriptions with no budget visible at subscription scope", "budgets"))
def budget_coverage(snap):
    """CAF: apply a budget and alerts to each subscription. A management group budget may cover a subscription too; whether it does is UNVERIFIED
    and the management group scope is not collected, so the message says what was and was not looked at."""
    rows, ok, failed = _rest(snap, "budgets")
    have = _by_sub(rows)
    for sub in sorted(ok):
        if not have.get(sub):
            yield Finding(
                "BUD-COVER-01", f"/subscriptions/{sub}", "medium", "No budget is visible at subscription scope",
                {"scope_collected": SUB_ONLY, "subscriptions_not_readable": len(failed)},
            )  # fmt: skip


@check(_g("BUD-ALERT-01", "Budgeting", "Budgets that cannot alert anyone", "budgets"))
def budget_alerts(snap):
    """A budget without an enabled notification, or whose enabled notifications name no e-mail address, role or group, raises no alert a person sees.
    Addresses are never stored, only whether any exist. Confidence is capped at medium until a live response confirms the notification shape."""
    rows, _ok, _failed = _rest(snap, "budgets")
    for bud in rows:
        notes = _notes(bud)
        enabled = [x for x in notes if x.get("enabled") is True]
        reach = [x for x in enabled if x.get("hasEmail") or x.get("hasRole") or x.get("hasGroup")]
        if reach:
            continue
        why = (
            "has no enabled notification"
            if not enabled
            else "has enabled notifications but none names a recipient (e-mail, role or action group)"
        )
        yield Finding(
            "BUD-ALERT-01", str(bud.get("id")), "medium", f"Budget {why}",
            {"name": bud.get("name"), "amount": bud.get("amount"), "timeGrain": bud.get("timeGrain"), "notifications_configured": len(notes), "enabled": len(enabled)},
        )  # fmt: skip


@check(_g("BUD-FCST-01", "Forecasting", "Subscriptions whose budgets alert on actual spend only", "budgets", conf="low"))
def budget_forecast_alerts(snap):
    """FinOps budgeting guidance: alert on actual and forecasted cost. Only subscriptions that already have a budget are judged
    (BUD-COVER-01 covers the rest). A forecast alert counts when an enabled notification has thresholdType Forecasted."""
    rows, ok, _failed = _rest(snap, "budgets")
    for sub, buds in sorted(_by_sub(rows).items()):
        if sub not in ok:
            continue
        has = any(x.get("enabled") is True and x.get("thresholdType") == "Forecasted" for b in buds for x in _notes(b))
        if not has:
            yield Finding(
                "BUD-FCST-01", f"/subscriptions/{sub}", "low", "No budget has an enabled forecast alert, so overspend is only flagged after it happens",
                {"budgets": len(buds), "scope_collected": SUB_ONLY},
            )  # fmt: skip


@check(_g("BUD-EXP-01", "Budgeting", "Budgets whose end date has passed", "budgets"))
def budget_expired(snap):
    """Learn: a budget monitors and alerts only while its time period is valid. Judged against the snapshot collection time, never the wall clock."""
    rows, _ok, _failed = _rest(snap, "budgets")
    now = collected_at(snap)
    for bud in rows:
        end = _date(bud.get("endDate"))
        if end is not None and end < now:
            yield Finding(
                "BUD-EXP-01", str(bud.get("id")), "medium", f"Budget ended on {end.date().isoformat()}, so it no longer monitors spend",
                {"name": bud.get("name"), "endDate": bud.get("endDate"), "collected_at": now.isoformat()},
            )  # fmt: skip


@check(_g("ALR-ANOM-01", "Anomaly Management", "Subscriptions with no anomaly alert rule visible", "anomaly_rules", conf="low"))
def anomaly_alert_rules(snap):
    """Anomaly alert rules are scheduled actions of kind InsightAlert at subscription scope (Learn). The API lists SHARED scheduled actions; whether a
    rule created in the portal is shared or private is UNVERIFIED, so a missing rule is worded 'not visible to this identity', never 'absent'."""
    rows, ok, _failed = _rest(snap, "anomaly_rules")
    for sub in sorted(ok):
        rules = [r for r in _by_sub(rows).get(sub, []) if r.get("kind") == "InsightAlert"]
        live = [r for r in rules if r.get("status") == "Enabled"]
        if live:
            continue
        msg = (
            "An anomaly alert rule exists but is not enabled (" + ", ".join(sorted({str(r.get("status")) for r in rules})) + ")"
            if rules
            else "No anomaly alert rule is visible to this identity (shared rules only; private rules cannot be seen)"
        )
        yield Finding(
            "ALR-ANOM-01", f"/subscriptions/{sub}", "low", msg,
            {"rules_visible": len(rules), "caveat": "public cloud only; Learn limits a subscription to five rules"},
        )  # fmt: skip


BAD_RUNS = {"Failed", "Timeout", "DataNotAvailable"}


@check(_g("EXP-CFG-01", "Data Ingestion", "Cost data exports missing, paused or failing", "cost_exports", conf="low"))
def export_config(snap):
    """FinOps data ingestion: scheduled exports to storage. Reports (1) no export visible at any subscription scope, (2) an export whose schedule
    is Inactive, (3) an export whose last run failed. Run history is requested with $expand=runHistory (last run of each export)."""
    rows, ok, _failed = _rest(snap, "cost_exports")
    if not rows:
        yield Finding(
            "EXP-CFG-01", "exports:estate", "low", "No cost export is visible at any subscription scope that was read",
            {"subscriptions_read": len(ok), "scope_collected": SUB_ONLY},
        )  # fmt: skip
        return
    for exp in rows:
        if exp.get("hasSchedule") and exp.get("scheduleStatus") == "Inactive":
            yield Finding(
                "EXP-CFG-01", str(exp.get("id")), "low", "Cost export schedule is Inactive, so no new data is delivered",
                {"name": exp.get("name"), "exportType": exp.get("exportType"), "recurrence": exp.get("recurrence")},
            )  # fmt: skip
        elif isinstance(exp.get("lastRunStatus"), str) and exp["lastRunStatus"] in BAD_RUNS:
            yield Finding(
                "EXP-CFG-01", str(exp.get("id")), "medium", f"Last cost export run ended with status {exp.get('lastRunStatus')}",
                {"name": exp.get("name"), "lastRunEnd": exp.get("lastRunEnd"), "errorCode": exp.get("lastRunErrorCode")},
            )  # fmt: skip
