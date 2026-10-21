"""Backlog 35 (gap analysis KB 14): non-production and housekeeping checks. Ideas come from the public ACORT README (GPL, ideas only, no code
read or copied) and Microsoft Learn pages cited per check. Every check is offline-only until gate G2 passes on a real tenant."""

from .checks import Finding, NotAssessed, check, collected_at
from .checks_builtin import _cm, _devtest_subs, _parse_ts, _rows

NONPROD_WORDS = {"dev", "development", "test", "testing", "uat", "qa", "nonprod", "sandbox", "staging", "stg", "preprod"}
REDUNDANT_SKU_PARTS = ("_grs", "_gzrs", "_ragrs", "_ragzrs", "_zrs")


def _nonprod_name(name) -> bool:
    """Whole-word match on the subscription name ('contest' and 'attestation' do not count). 'non-prod' is read as one word."""
    import re  # noqa: PLC0415

    text = re.sub(r"non[\s_-]+prod", "nonprod", str(name or "").lower())
    return bool(set(re.split(r"[^a-z0-9]+", text)) & NONPROD_WORDS)


@check(
    _cm(
        "OPT-DEVOFF-01",
        "billing",
        "Rate Optimization",
        "Subscriptions that look non-production but are not on a Dev/Test offer",
        "subscriptions",
        conf="low",
    )
)
def devtest_offer_not_used(snap):
    """Heuristic on the subscription NAME only. Learn (read 2026-10-21): Pay-As-You-Go Dev/Test (0023P) and Enterprise Dev/Test (0148P) both
    require a Visual Studio subscription for the users, and the Enterprise offer needs an EA with the Dev/Test option enabled. So this is a
    prompt to check eligibility, never a saving. Offers whose quota ID already contains 'devtest' are skipped."""
    dev = _devtest_subs(snap)
    for s in _rows(snap, "subscriptions"):
        sid = str(s.get("subscriptionId") or str(s.get("id")).split("/")[-1]).lower()
        if sid in dev or not _nonprod_name(s.get("name")):
            continue
        yield Finding(
            "OPT-DEVOFF-01",
            s["id"],
            "info",
            "Subscription name suggests non-production use but the offer is not a Dev/Test offer: check whether Dev/Test pricing is available and allowed",
            {"quotaId": s.get("quotaId"), "basis": "subscription name words only"},
        )


@check(
    _cm(
        "IDLE-VMSHUT-01",
        "compute",
        "Usage Optimization",
        "Running VMs in Dev/Test-looking subscriptions with no auto-shutdown schedule",
        "vms",
        "subscriptions",
        "devtest_schedules",
        conf="low",
    )
)
def no_autoshutdown_in_devtest(snap):
    """A schedule counts when a Microsoft.DevTestLab/schedules resource targets the VM id and is Enabled (Learn template reference, read 2026-10-21).
    UNVERIFIED live: that Resource Graph returns this type, and the property names taskType, status, targetResourceId. Because absence of the type in
    Resource Graph looks identical to 'no schedules anywhere', an empty schedule list makes the check refuse to decide rather than flag every VM."""
    dev = _devtest_subs(snap)
    if not dev:
        return
    rows = _rows(snap, "devtest_schedules")
    if not rows:
        raise NotAssessed(
            "no auto-shutdown schedule resources were returned for the estate; cannot tell 'none exist' from 'Resource Graph does not return this type' (UNVERIFIED)"
        )
    shut = {str(r.get("targetResourceId") or "").lower() for r in rows if str(r.get("status") or "").lower() == "enabled"}
    for v in _rows(snap, "vms"):
        if str(v.get("subscriptionId") or "").lower() not in dev:
            continue
        if str(v.get("powerState") or "").lower() != "powerstate/running":
            continue
        if str(v.get("id") or "").lower() in shut:
            continue
        yield Finding(
            "IDLE-VMSHUT-01",
            v["id"],
            "low",
            f"Running VM ({v.get('vmSize')}) in a Dev/Test-looking subscription has no enabled auto-shutdown schedule: review whether it needs to run around the clock",
            {"location": v.get("location"), "vmSize": v.get("vmSize")},
        )


@check(
    _cm(
        "OPT-DTSTOR-01",
        "storage",
        "Usage Optimization",
        "Premium disks and zone or geo redundant storage in Dev/Test-looking subscriptions",
        "all_disks",
        "storage_accounts",
        "subscriptions",
        conf="low",
    )
)
def premium_or_redundant_in_devtest(snap):
    """Prompt, not a saving: test workloads sometimes need production-like storage. Disks: any SKU name starting with Premium. Storage accounts: SKU
    name starting Premium_ or containing ZRS/GRS/GZRS variants. Dev/Test is judged from the quota ID only (see _devtest_subs)."""
    dev = _devtest_subs(snap)
    for d in _rows(snap, "all_disks"):
        if str(d.get("subscriptionId") or "").lower() in dev and str(d.get("skuName") or "").lower().startswith("premium"):
            yield Finding(
                "OPT-DTSTOR-01",
                d["id"],
                "info",
                f"Premium disk ({d.get('skuName')}, {d.get('sizeGB')} GB) in a Dev/Test-looking subscription: check whether a cheaper SKU meets the test need",
                {"kind": "disk", "skuName": d.get("skuName"), "sizeGB": d.get("sizeGB")},
            )
    for a in _rows(snap, "storage_accounts"):
        sku = str(a.get("skuName") or "").lower()
        if str(a.get("subscriptionId") or "").lower() in dev and (sku.startswith("premium") or any(p in sku for p in REDUNDANT_SKU_PARTS)):
            yield Finding(
                "OPT-DTSTOR-01",
                a["id"],
                "info",
                f"Storage account SKU {a.get('skuName')} in a Dev/Test-looking subscription: check whether locally redundant standard storage meets the test need",
                {"kind": "storage_account", "skuName": a.get("skuName"), "accountKind": a.get("kind")},
            )


@check(
    _cm(
        "OPT-STORLC-01",
        "storage",
        "Usage Optimization",
        "Storage accounts with no blob lifecycle management policy",
        "storage_accounts",
        "storage_lifecycle",
        conf="low",
    )
)
def storage_without_lifecycle(snap):
    """Learn (read 2026-10-21): lifecycle policies are supported for block and append blobs in general-purpose v2 and premium block blob accounts;
    the legacy BlobStorage kind is left out because Learn pages disagree on it. A policy is the child resource 'default'. UNVERIFIED live: that
    Resource Graph returns managementpolicies; an empty result makes the check refuse to decide. Whether an account holds blobs at all is not known."""
    pols = _rows(snap, "storage_lifecycle")
    accts = [a for a in _rows(snap, "storage_accounts") if str(a.get("kind") or "").lower() in ("storagev2", "blockblobstorage")]
    if accts and not pols:
        raise NotAssessed(
            "no lifecycle policy resources were returned for the estate; cannot tell 'none exist' from 'Resource Graph does not return this type' (UNVERIFIED)"
        )
    have = {
        str(p.get("id") or "").lower().rsplit("/managementpolicies/", 1)[0]
        for p in pols
        if isinstance(p.get("ruleCount"), int) and not isinstance(p.get("ruleCount"), bool) and p["ruleCount"] > 0
    }
    for a in accts:
        if str(a.get("id") or "").lower() not in have:
            yield Finding(
                "OPT-STORLC-01",
                a["id"],
                "low",
                f"Storage account ({a.get('kind')}, {a.get('skuName')}) has no lifecycle policy with rules: old blobs stay on their original tier until someone moves or deletes them",
                {"location": a.get("location"), "kind": a.get("kind"), "skuName": a.get("skuName"), "accessTier": a.get("accessTier")},
            )


@check(
    _cm("ORPH-AVSET-01", "orphaned", "Usage Optimization", "Availability sets with no virtual machines", "availability_sets", conf="medium")
)
def empty_availability_sets(snap):
    """Learn: properties.virtualMachines lists the VMs in the set (SubResource array). An empty set has no direct charge that I know of (UNVERIFIED), so this is
    hygiene, severity low. A missing or null list is not reported."""
    for r in _rows(snap, "availability_sets"):
        if r.get("vmCount") == 0:
            yield Finding("ORPH-AVSET-01", r["id"], "low", "Availability set contains no virtual machines", {"location": r.get("location")})


DEALLOC_DAYS = 90


@check(
    _cm(
        "IDLE-VMDEAL-01",
        "compute",
        "Usage Optimization",
        "VMs deallocated for more than 90 days (disks and IPs still billed)",
        "vms",
        conf="low",
    )
)
def long_deallocated_vms(snap):
    """Compute is not billed while deallocated, but disks, snapshots and public IPs are (Learn, States and billing status of Azure Virtual Machines,
    read 2026-10-21). Age comes ONLY from a timestamp on the power state (powerTime). We never infer 'over 90 days' from a missing Activity Log entry:
    the Activity Log keeps 90 days (Learn, Activity log in Azure Monitor, read 2026-10-21), so absence proves nothing. UNVERIFIED live: whether
    Resource Graph returns a time on the power state at all. If deallocated VMs exist but none carries a time, the check refuses to decide."""
    dealloc = [v for v in _rows(snap, "vms") if str(v.get("powerState") or "").lower() == "powerstate/deallocated"]
    if not dealloc:
        return
    ref = collected_at(snap)
    dated = [(v, _parse_ts(v.get("powerTime"))) for v in dealloc]
    if not any(t for _, t in dated):
        raise NotAssessed(
            f"{len(dealloc)} deallocated VM(s) found but none has a power-state timestamp, so their age is unknown "
            "(the Activity Log only reaches back 90 days and cannot prove a longer period) (UNVERIFIED)"
        )
    for v, t in dated:
        if t is not None and (ref - t).days > DEALLOC_DAYS:
            yield Finding(
                "IDLE-VMDEAL-01",
                v["id"],
                "low",
                f"VM ({v.get('vmSize')}) has been deallocated for {(ref - t).days} days: review whether it, its disks and its public IPs are still needed",
                {"location": v.get("location"), "vmSize": v.get("vmSize"), "deallocated_days": (ref - t).days},
            )
