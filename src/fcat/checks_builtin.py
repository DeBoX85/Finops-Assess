from . import billing
from .checks import CheckMeta, Finding, check

# ADR 0004 (hybrid): KQL narrows to unmanaged-by-VM disks; the rules below live in Python so they are unit tested.
# Mirrors the finops-toolkit ORPH logic (MIT): skip disks in ActiveSAS state and ASR replica/seed disks.
EXCLUDED_STATES = {"ActiveSAS"}
EXCLUDED_TAG_KEYS = {"asr-replicadisk", "asrseeddisk"}


def _excluded(d) -> str | None:
    if d.get("diskState") in EXCLUDED_STATES:
        return f"diskState {d.get('diskState')}"
    tags = d.get("tags") or {}
    if isinstance(tags, dict) and EXCLUDED_TAG_KEYS & {str(k).lower() for k in tags}:
        return "ASR replica/seed tag"
    return None


@check(
    CheckMeta(
        id="ORPH-DISK-01",
        domain="orphaned",
        title="Unattached managed disks",
        collectors=("unattached_disks",),
        permissions=("Reader",),
        savings_basis="none",
        confidence="high",
        framework="Usage Optimization",
    )
)
def unattached_disks(snap):
    # Phase 1: no savings figure yet. Savings need cost data (actual) and list price; added in Phase 3.
    for d in snap.load("unattached_disks")["rows"]:
        if _excluded(d):
            continue
        yield Finding(
            "ORPH-DISK-01",
            d["id"],
            "medium",
            f"Unattached disk ({d.get('sizeGB')} GB, {d.get('skuName')}) incurs storage cost",
            {k: d.get(k) for k in ("location", "skuName", "sizeGB", "timeCreated", "diskState")},
        )


@check(
    CheckMeta(
        id="BILL-OFFER-01",
        domain="billing",
        title="Cost Management data availability by subscription offer",
        collectors=("subscriptions",),
        permissions=("Reader",),
        savings_basis="none",
        confidence="medium",  # ambiguous quota IDs (shared across agreements) need a live probe
        framework="Data Ingestion",
    )
)
def offer_cost_data(snap):
    """Tells the reader which subscriptions cannot or may not have cost data, so cost checks are never silently empty."""
    for s in snap.load("subscriptions")["rows"]:
        c = billing.classify(s.get("quotaId"))
        if c["cost_management"] == "supported":
            continue
        msg = {
            "unsupported": "Cost Management holds no cost data for this subscription offer; cost-based checks cannot be assessed for it",
            "depends": "Cost data may not be available: this quota ID is shared by supported and unsupported agreement types; confirm the billing account type",
            "unknown": "Offer not recognised; cost data availability not assessed",
        }[c["cost_management"]]
        yield Finding(
            "BILL-OFFER-01",
            s["id"],
            "info",
            msg,
            {"quotaId": c["quota_id"], "offer_note": c["note"], "cost_management": c["cost_management"]},
        )


def _meta(id_, title, collector, conf="medium"):
    return CheckMeta(
        id=id_, domain="orphaned", title=title, collectors=(collector,), permissions=("Reader",),
        savings_basis="none", confidence=conf, framework="Usage Optimization",
    )  # fmt: skip


def _blank(v) -> bool:
    return v is None or v == ""


@check(_meta("ORPH-PIP-01", "Public IP addresses not attached to anything", "public_ips"))
def unattached_public_ips(snap):
    """Not attached to an IP configuration, NAT gateway or linked public IP, or attached only to a NIC that is itself unattached
    (the second case follows the hub query, read 2026-10-18). Cost by SKU/allocation is UNVERIFIED and not estimated here."""
    nic_rows = (snap.load("nics") or {}).get("rows", []) if snap.has("nics") else []
    orphan_nic_pips = {
        str(p).lower()
        for n in nic_rows
        if _blank(n.get("vmId")) and _blank(n.get("privateEndpointId"))
        for p in (n.get("publicIpIds") or [])
        if p
    }
    for r in snap.load("public_ips")["rows"]:
        free = all(_blank(r.get(k)) for k in ("ipConfigId", "natGatewayId", "linkedPublicIpId"))
        via_nic = str(r["id"]).lower() in orphan_nic_pips
        if free or via_nic:
            why = "is not attached to any resource" if free else "is attached only to a network interface that is itself unattached"
            yield Finding(
                "ORPH-PIP-01", r["id"], "medium", f"Public IP ({r.get('skuName')}, {r.get('allocation')}) {why}",
                {"location": r.get("location"), "skuName": r.get("skuName"), "allocation": r.get("allocation"), "via_orphan_nic": via_nic and not free},
            )  # fmt: skip


@check(_meta("ORPH-NIC-01", "Network interfaces not attached to a VM or private endpoint", "nics", "medium"))
def unattached_nics(snap):
    """A NIC itself has no hourly charge (UNVERIFIED); the finding is hygiene and often points to a leftover public IP or NSG association."""
    for r in snap.load("nics")["rows"]:
        if _blank(r.get("vmId")) and _blank(r.get("privateEndpointId")):
            yield Finding(
                "ORPH-NIC-01",
                r["id"],
                "low",
                "Network interface is not attached to a virtual machine or private endpoint",
                {"location": r.get("location")},
            )


@check(_meta("ORPH-NSG-01", "Network security groups with no subnet or NIC", "nsgs", "medium"))
def unused_nsgs(snap):
    """Same semantics as the finops-toolkit hub query (read 2026-10-18): absent or empty association lists mean no association.
    UNVERIFIED live whether ARG omits the properties for an unassociated NSG. No direct cost (UNVERIFIED); clean-up only."""
    for r in snap.load("nsgs")["rows"]:
        if not r.get("nicRefs") and not r.get("subnetRefs"):
            yield Finding(
                "ORPH-NSG-01",
                r["id"],
                "low",
                "Network security group is associated with no subnet or network interface",
                {"location": r.get("location")},
            )


@check(_meta("ORPH-ASP-01", "App Service plans hosting no apps", "app_service_plans", "high"))
def empty_app_service_plans(snap):
    """Free-tier plans cost nothing and are skipped. Paid plans bill whether or not apps run on them (Learn App Service pricing, UNVERIFIED read)."""
    for r in snap.load("app_service_plans")["rows"]:
        if r.get("numberOfSites") != 0:
            continue
        if str(r.get("skuTier") or "").lower() == "free":
            continue
        yield Finding(
            "ORPH-ASP-01", r["id"], "medium", f"App Service plan ({r.get('skuName')}) hosts no apps",
            {k: r.get(k) for k in ("location", "skuName", "skuTier", "skuCapacity")},
        )  # fmt: skip


@check(
    CheckMeta(
        id="IDLE-VMSTOP-01", domain="compute", title="VMs stopped but not deallocated", collectors=("vms",), permissions=("Reader",),
        savings_basis="none", confidence="medium", framework="Usage Optimization",
    )
)  # fmt: skip
def stopped_not_deallocated(snap):
    """PowerState/stopped means the guest is off but compute is still allocated and billed; deallocated is the state that stops compute charges.
    Predicate follows the hub query (read 2026-10-18). UNVERIFIED live: instanceView is only returned when the query asks for it."""
    for r in snap.load("vms")["rows"]:
        if str(r.get("powerState") or "").lower() == "powerstate/stopped":
            yield Finding(
                "IDLE-VMSTOP-01", r["id"], "medium", f"VM ({r.get('vmSize')}) is stopped but not deallocated, so compute is likely still billed",
                {"location": r.get("location"), "vmSize": r.get("vmSize"), "powerState": r.get("powerDisplay")},
            )  # fmt: skip
