from . import billing, metrics
from .checks import CheckMeta, Finding, NotAssessed, check, collected_at

# ADR 0004 (hybrid): KQL narrows to unmanaged-by-VM disks; the rules below live in Python so they are unit tested.
# Mirrors the finops-toolkit ORPH logic (MIT): skip disks in ActiveSAS state and ASR replica/seed disks.
EXCLUDED_STATES = {"ActiveSAS"}
EXCLUDED_TAG_KEYS = {"asr-replicadisk", "asrseeddisk"}


def _text(v) -> str:
    """Scalar text or empty. Lists, dicts and None become '' so a malformed row is 'unknown', never a crash."""
    return v if isinstance(v, str) else (str(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else "")


def _excluded(d) -> str | None:
    if _text(d.get("diskState")) in EXCLUDED_STATES:
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


def _m(id_, title, *collectors, conf="medium"):
    return CheckMeta(
        id=id_, domain="orphaned", title=title, collectors=collectors, permissions=("Reader",),
        savings_basis="none", confidence=conf, framework="Usage Optimization",
    )  # fmt: skip


def _rows(snap, name):
    return (snap.load(name) or {}).get("rows", [])


@check(_m("ORPH-LB-01", "Standard load balancers with no backend pool", "load_balancers"))
def backendless_load_balancers(snap):
    """Zero backend pools on a non-Basic SKU (Basic is retired and covered elsewhere). Like the hub query, a pool that exists but is empty
    is NOT detected here; an unknown pool count (null) is not reported."""
    for r in _rows(snap, "load_balancers"):
        if r.get("backendPoolCount") == 0 and str(r.get("skuName") or "").lower() != "basic":
            yield Finding(
                "ORPH-LB-01", r["id"], "medium", f"Load balancer ({r.get('skuName')}) has no backend pool", {"location": r.get("location")}
            )


@check(_m("ORPH-AGW-01", "Application gateways whose backend pools hold no targets", "app_gateways"))
def backendless_app_gateways(snap):
    """Sum of backend IP configurations and backend addresses over all pools is zero (hub query logic). FQDN-only pools are counted via backendAddresses (UNVERIFIED)."""
    for r in _rows(snap, "app_gateways"):
        pools = r.get("backendPools") if isinstance(r.get("backendPools"), list) else []
        targets = 0
        for p in pools:
            props = p.get("properties") if isinstance(p, dict) else None
            if not isinstance(props, dict):
                props = {}
            for k in ("backendIPConfigurations", "backendAddresses"):
                targets += len(props[k]) if isinstance(props.get(k), list) else 0
        if targets == 0:
            yield Finding(
                "ORPH-AGW-01", r["id"], "medium", f"Application gateway ({r.get('skuName')}) has no backend targets in {len(pools)} pool(s)",
                {"location": r.get("location"), "skuName": r.get("skuName"), "skuCapacity": r.get("skuCapacity"), "pools": len(pools)},
            )  # fmt: skip


@check(_m("ORPH-EPOOL-01", "SQL elastic pools with no databases", "elastic_pools", "sql_databases"))
def empty_elastic_pools(snap):
    """Joined in Python on the lower-cased pool id. If the database list is missing the check yields nothing rather than calling every pool empty."""
    if not snap.has("sql_databases"):
        return
    used = {str(d.get("elasticPoolId") or "").lower() for d in _rows(snap, "sql_databases")}
    for r in _rows(snap, "elastic_pools"):
        if str(r["id"]).lower() not in used:
            yield Finding(
                "ORPH-EPOOL-01",
                r["id"],
                "medium",
                f"SQL elastic pool ({r.get('skuName')}) contains no databases",
                {"location": r.get("location"), "skuName": r.get("skuName")},
            )


@check(_m("ORPH-VGW-01", "VPN/ExpressRoute gateways with no connection", "vnet_gateways", "vnet_connections", conf="low"))
def idle_vnet_gateways(snap):
    """Differs from the hub query on purpose: a VPN gateway with point-to-site configured is skipped, because P2S clients do not use a connection resource.
    Confidence low until verified live (UNVERIFIED how connection resources appear for every gateway type)."""
    if not snap.has("vnet_connections"):
        return
    used = set()
    for c in _rows(snap, "vnet_connections"):
        used |= {str(c.get(k) or "").lower() for k in ("gateway1", "gateway2")}
    for r in _rows(snap, "vnet_gateways"):
        if r.get("gatewayType") not in ("Vpn", "ExpressRoute") or r.get("p2sConfigured"):
            continue
        if str(r["id"]).lower() not in used:
            yield Finding(
                "ORPH-VGW-01",
                r["id"],
                "medium",
                f"{r.get('gatewayType')} gateway ({r.get('skuName')}) has no connection",
                {"location": r.get("location"), "skuName": r.get("skuName")},
            )


@check(_m("ORPH-NAT-01", "NAT gateways not associated with a subnet", "nat_gateways"))
def orphan_nat_gateways(snap):
    """Absent or empty subnet list means orphaned (hub query semantics, UNVERIFIED live)."""
    for r in _rows(snap, "nat_gateways"):
        if not r.get("subnetCount"):
            yield Finding(
                "ORPH-NAT-01",
                r["id"],
                "medium",
                "NAT gateway is not associated with any subnet",
                {"location": r.get("location"), "skuName": r.get("skuName")},
            )


@check(_m("ORPH-DDOS-01", "DDoS protection plans with no virtual network", "ddos_plans"))
def unassociated_ddos_plans(snap):
    """A DDoS plan is a high fixed monthly cost (Learn pricing page, not re-read today: UNVERIFIED), so an unused one matters. Absent or empty list means unassociated."""
    for r in _rows(snap, "ddos_plans"):
        if not r.get("vnetCount"):
            yield Finding(
                "ORPH-DDOS-01",
                r["id"],
                "medium",
                "DDoS protection plan is not associated with any virtual network",
                {"location": r.get("location")},
            )


@check(_m("ORPH-ERC-01", "ExpressRoute circuits not provisioned by the provider", "er_circuits", conf="low"))
def unprovisioned_er_circuits(snap):
    """Provider state other than Provisioned. ExpressRoute Direct circuits (port-based) and unknown state are skipped. Billing starts at circuit creation
    per Learn (UNVERIFIED, not re-read today), hence low confidence on the cost angle."""
    for r in _rows(snap, "er_circuits"):
        state = r.get("providerState")
        if not state or r.get("portId"):
            continue
        if state != "Provisioned":
            yield Finding(
                "ORPH-ERC-01",
                r["id"],
                "medium",
                f"ExpressRoute circuit provider state is {state}",
                {"location": r.get("location"), "providerState": state, "circuitState": r.get("circuitState")},
            )


@check(
    CheckMeta(
        id="MON-LAWCAP-01", domain="monitoring", title="Log Analytics workspaces without a daily cap", collectors=("la_workspaces",),
        permissions=("Reader",), savings_basis="none", confidence="low", framework="Planning and Estimating",
    )
)  # fmt: skip
def workspaces_without_daily_cap(snap):
    """Informational. Learn calls the daily cap a preventative control, not a cost-reduction method, so absence is a governance observation.
    Free-tier workspaces are skipped. UNVERIFIED how ARG reports 'no cap' (null or negative), both are treated as no cap."""
    for r in _rows(snap, "la_workspaces"):
        if str(r.get("skuName") or "").lower() == "free":
            continue
        q = r.get("dailyQuotaGb")
        if q is not None and (isinstance(q, bool) or not isinstance(q, (int, float))):
            continue  # not a number: unknown, not 'no cap'
        if q is None or q < 0:
            yield Finding(
                "MON-LAWCAP-01",
                r["id"],
                "info",
                "Log Analytics workspace has no daily ingestion cap",
                {"location": r.get("location"), "skuName": r.get("skuName")},
            )


@check(
    CheckMeta(
        id="MON-AICLS-01", domain="monitoring", title="Application Insights resources not linked to a workspace",
        collectors=("app_insights",), permissions=("Reader",), savings_basis="none", confidence="low", framework="Data Ingestion",
    )
)  # fmt: skip
def appinsights_without_workspace(snap):
    """Learn: workspaceResourceId is required when creating a component with the current API version; older components lack it.
    Absence therefore means an older resource, reported as informational (migration candidate), not as a defect."""
    for r in _rows(snap, "app_insights"):
        if _blank(r.get("workspaceResourceId")):
            yield Finding(
                "MON-AICLS-01",
                r["id"],
                "info",
                "Application Insights resource has no linked Log Analytics workspace (older resource type)",
                {"location": r.get("location"), "ingestionMode": r.get("ingestionMode")},
            )


@check(
    CheckMeta(
        id="SEC-DEFDEV-01", domain="security", title="Defender for Cloud paid plans on Dev/Test-looking subscriptions",
        collectors=("defender_pricings", "subscriptions"), permissions=("Reader",), savings_basis="none", confidence="low",
        framework="Usage Optimization",
    )
)  # fmt: skip
def defender_plans_on_devtest(snap):
    """Heuristic: quota ID contains 'devtest' (e.g. MSDNDevTest, CSPDevTest) AND a plan is at pricing tier Standard. Whether the plan is wanted is a business
    decision; wording is 'review'. Subscriptions are matched on subscription id, case-insensitive."""
    dev = {}
    for s in _rows(snap, "subscriptions"):
        if "devtest" in str(s.get("quotaId") or "").lower():
            dev[str(s["id"]).split("/")[-1].lower()] = s["id"]
    for r in _rows(snap, "defender_pricings"):
        sub = str(r.get("subscriptionId") or "").lower()
        if sub in dev and str(r.get("pricingTier") or "").lower() == "standard":
            yield Finding(
                "SEC-DEFDEV-01", r["id"], "info", f"Defender plan {r.get('name')} is on a paid tier in a subscription that looks like Dev/Test: review whether it is needed",
                {"plan": r.get("name"), "subPlan": r.get("subPlan"), "subscription": dev[sub]},
            )  # fmt: skip


OLD_SNAPSHOT_DAYS = 30  # same threshold as the Storage workbook ("Disk Snapshots with + 30 Days")


def _parse_ts(v):
    import datetime as dt  # noqa: PLC0415

    try:
        return dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None


@check(_m("ORPH-SNAP-01", "Managed disk snapshots older than 30 days", "snapshots"))
def old_snapshots(snap):
    """Age is measured from the snapshot's collection time. Old does not mean unneeded (backups, legal hold): informational, medium confidence."""
    ref = collected_at(snap)
    for r in _rows(snap, "snapshots"):
        t = _parse_ts(r.get("timeCreated"))
        if t is not None and (ref - t).days > OLD_SNAPSHOT_DAYS:
            yield Finding(
                "ORPH-SNAP-01", r["id"], "low", f"Snapshot ({r.get('sizeGB')} GB, {r.get('skuName')}) is {(ref - t).days} days old",
                {"location": r.get("location"), "sizeGB": r.get("sizeGB"), "skuName": r.get("skuName"), "age_days": (ref - t).days},
            )  # fmt: skip


@check(_m("ORPH-SNAP-02", "Snapshots stored on Premium SSD", "snapshots"))
def premium_snapshots(snap):
    """Hub query tests sku.name Premium_LRS, the workbook tests sku.tier Premium; either counts. Whether Standard is acceptable for the use is a human call."""
    for r in _rows(snap, "snapshots"):
        if str(r.get("skuName") or "").lower() == "premium_lrs" or str(r.get("skuTier") or "").lower() == "premium":
            yield Finding(
                "ORPH-SNAP-02",
                r["id"],
                "low",
                f"Snapshot ({r.get('sizeGB')} GB) uses Premium storage",
                {"location": r.get("location"), "skuName": r.get("skuName"), "sizeGB": r.get("sizeGB")},
            )


@check(_m("ORPH-SNAP-03", "Snapshots whose source disk no longer exists", "snapshots", "all_disks", "subscriptions", conf="low"))
def snapshots_without_source(snap):
    """Only judged when the source disk lives in a subscription we scanned; a source in a subscription we cannot see is not reported (unknown, not deleted)."""
    disks = {str(d["id"]).lower() for d in _rows(snap, "all_disks")}
    scanned = {str(s["id"]).split("/")[-1].lower() for s in _rows(snap, "subscriptions")}
    for r in _rows(snap, "snapshots"):
        src = str(r.get("sourceResourceId") or "").lower()
        parts = src.split("/")
        if len(parts) > 2 and parts[1] == "subscriptions" and parts[2] in scanned and "/disks/" in src and src not in disks:
            yield Finding(
                "ORPH-SNAP-03",
                r["id"],
                "low",
                "Snapshot source disk was not found in the scanned subscriptions",
                {"location": r.get("location"), "sizeGB": r.get("sizeGB")},
            )


@check(_m("MOD-STORV1-01", "Legacy storage account kinds (Storage, BlobStorage)", "storage_accounts"))
def legacy_storage_accounts(snap):
    """Hub query: kind Storage or BlobStorage on a Standard_* SKU. Upgrade to general purpose v2 is the usual path; effect on cost is not computed."""
    for r in _rows(snap, "storage_accounts"):
        if str(r.get("kind") or "").lower() in ("storage", "blobstorage") and str(r.get("skuName") or "").lower().startswith("standard_"):
            yield Finding(
                "MOD-STORV1-01",
                r["id"],
                "low",
                f"Storage account kind {r.get('kind')} is a legacy kind",
                {"location": r.get("location"), "kind": r.get("kind"), "skuName": r.get("skuName")},
            )


@check(_m("IDLE-VMDISK-01", "Premium disks on VMs that are stopped or deallocated", "vms", "all_disks"))
def premium_disks_on_stopped_vms(snap):
    """Workbook looks at the OS disk only; this also covers data disks. A deallocated VM still pays for its disks. Matching is case-insensitive on disk id."""
    prem = {
        str(d["id"]).lower(): d for d in _rows(snap, "all_disks") if str(d.get("skuName") or "").lower() in ("premium_lrs", "premium_zrs")
    }
    for v in _rows(snap, "vms"):
        if str(v.get("powerState") or "").lower() not in ("powerstate/stopped", "powerstate/deallocated"):
            continue
        dd = v.get("dataDisks") if isinstance(v.get("dataDisks"), list) else []
        ids = [v.get("osDiskId")] + [
            (d.get("managedDisk") or {}).get("id") if isinstance(d, dict) and isinstance(d.get("managedDisk"), dict) else None for d in dd
        ]
        hit = sorted({str(i).lower() for i in ids if i and str(i).lower() in prem})
        if hit:
            yield Finding(
                "IDLE-VMDISK-01", v["id"], "medium", f"VM is {str(v.get('powerState')).split('/')[-1]} but {len(hit)} Premium disk(s) are still billed",
                {"power_state": v.get("powerState"), "premium_disks": hit},
            )  # fmt: skip


@check(_m("ORPH-PDNS-01", "Private DNS zones linked to no virtual network", "private_dns_zones"))
def idle_private_dns_zones(snap):
    """Workbook predicate: numberOfVirtualNetworkLinks == 0. An unknown count (null) is not reported."""
    for r in _rows(snap, "private_dns_zones"):
        if r.get("linkCount") == 0:
            yield Finding(
                "ORPH-PDNS-01", r["id"], "low", "Private DNS zone has no virtual network link", {"recordSets": r.get("recordSets")}
            )


@check(_m("ORPH-PE-01", "Private endpoints in Disconnected state", "private_endpoints"))
def disconnected_private_endpoints(snap):
    """Workbook predicate: first (manual, else automatic) connection has status Disconnected. Rejected or Pending states are deliberately not reported."""
    for r in _rows(snap, "private_endpoints"):
        if str(r.get("connState") or "").lower() == "disconnected":
            yield Finding("ORPH-PE-01", r["id"], "low", "Private endpoint connection is Disconnected", {"location": r.get("location")})


# ---- Batch 5 (2026-10-18). Predicates from finops-toolkit hub queries (MIT, f12c29e, read 2026-10-18); retirement dates from Learn (read 2026-10-18).
# All UNVERIFIED live. Retirement checks use positive evidence only (a retired SKU or an explicit VHD URI), never the absence of a property.
def _cm(id_, domain, framework, title, *collectors, conf="medium", basis="none"):
    return CheckMeta(
        id=id_, domain=domain, title=title, collectors=collectors, permissions=("Reader",),
        savings_basis=basis, confidence=conf, framework=framework,
    )  # fmt: skip


def _devtest_subs(snap) -> set:
    return {
        str(s.get("subscriptionId") or str(s.get("id")).split("/")[-1]).lower()
        for s in _rows(snap, "subscriptions")
        if "devtest" in str(s.get("quotaId") or "").lower()
    }


@check(
    _cm(
        "MOD-LBBAS-01",
        "modernization",
        "Architecting and Workload Placement",
        "Load balancers on the retired Basic SKU",
        "load_balancers",
        conf="high",
    )
)
def basic_load_balancers(snap):
    """Learn (read 2026-10-18): Basic Load Balancer was retired on 2025-09-30. Existing ones keep running but are unsupported and have no SLA. Cloud Services
    (extended support) is exempt per Learn; this check cannot tell (UNVERIFIED), so the message says so."""
    for r in _rows(snap, "load_balancers"):
        if str(r.get("skuName") or "").lower() == "basic":
            yield Finding(
                "MOD-LBBAS-01", r["id"], "medium", "Load balancer uses the Basic SKU, retired 2025-09-30 (no SLA); plan the upgrade to Standard",
                {"location": r.get("location"), "note": "Cloud Services (extended support) is exempt per Learn; not detectable here"},
            )  # fmt: skip


@check(
    _cm(
        "MOD-PIPBAS-01",
        "modernization",
        "Architecting and Workload Placement",
        "Public IP addresses on the retired Basic SKU",
        "public_ips",
        conf="high",
    )
)
def basic_public_ips(snap):
    """Learn (read 2026-10-18): Basic SKU public IPs were retired on 2025-09-30. A Microsoft Q&A answer says IPs on Application Gateway v1 and on Basic VPN gateways
    followed other dates (UNVERIFIED, Q&A is not official documentation), so the message does not state an urgency for those."""
    for r in _rows(snap, "public_ips"):
        if str(r.get("skuName") or "").lower() == "basic":
            yield Finding(
                "MOD-PIPBAS-01", r["id"], "medium", "Public IP uses the Basic SKU, retired 2025-09-30; plan the upgrade to Standard",
                {"location": r.get("location"), "allocation": r.get("allocation")},
            )  # fmt: skip


@check(
    _cm(
        "MOD-AGWV1-01",
        "modernization",
        "Architecting and Workload Placement",
        "Application gateways on the retired v1 SKU",
        "app_gateways",
        conf="high",
    )
)
def app_gateways_v1(snap):
    """Learn (read 2026-10-18): Application Gateway V1 retired on 2026-04-28; remaining V1 gateways can be blocked and deleted by Microsoft. Hub query rule: tier Standard or WAF
    (v2 tiers are Standard_v2 and WAF_v2)."""
    for r in _rows(snap, "app_gateways"):
        if str(r.get("skuTier") or "").lower() in ("standard", "waf"):
            yield Finding(
                "MOD-AGWV1-01", r["id"], "medium", f"Application gateway uses the retired v1 SKU ({r.get('skuTier')}); migrate to v2",
                {"location": r.get("location"), "skuName": r.get("skuName"), "skuTier": r.get("skuTier"), "skuCapacity": r.get("skuCapacity")},
            )  # fmt: skip


@check(_cm("MOD-VMUNMG-01", "modernization", "Architecting and Workload Placement", "VMs using unmanaged disks", "vms", conf="medium"))
def vms_with_unmanaged_disks(snap):
    """Learn (read 2026-10-18): unmanaged disks fully retired 2026-03-31 (extended from 2025-09-30); VMs that use them cannot be started. The hub query tests for a
    null managed disk; this check requires a positive VHD URI on the OS disk or a data disk instead, so a missing property is 'unknown', not a finding."""
    for v in _rows(snap, "vms"):
        dd = v.get("dataDisks") if isinstance(v.get("dataDisks"), list) else []
        data_vhd = any(isinstance(d, dict) and isinstance(d.get("vhd"), dict) and not _blank(d["vhd"].get("uri")) for d in dd)
        if not _blank(v.get("osDiskVhdUri")) or data_vhd:
            yield Finding(
                "MOD-VMUNMG-01", v["id"], "medium", "VM uses unmanaged (VHD blob) disks, retired 2026-03-31; migrate to managed disks",
                {"vmSize": v.get("vmSize"), "os_disk_unmanaged": not _blank(v.get("osDiskVhdUri")), "data_disk_unmanaged": data_vhd},
            )  # fmt: skip


@check(
    _cm(
        "LIC-AHBWIN-01",
        "licensing",
        "Licensing and SaaS",
        "Windows VMs and scale sets without Azure Hybrid Benefit",
        "vm_licensing",
        "subscriptions",
        conf="low",
    )
)
def windows_without_ahb(snap):
    """Hub query rule: OS type Windows, image publisher not microsoftwindowsdesktop or microsoftvisualstudio, license type not starting with 'Windows'
    (Windows_Server is Azure Hybrid Benefit, Windows_Client is multi-tenant hosting; Learn read 2026-10-18). Dev/Test subscriptions are skipped (quota id contains 'devtest';
    broader than the hub query, which excludes only MSDNDevTest, to avoid false positives). Whether the customer holds eligible licences with Software Assurance
    cannot be read from Azure, so confidence is low and the wording is 'review'. No cost figure: Learn says at least 8 core licences per VM apply; vCPU needs another call."""
    dev = _devtest_subs(snap)
    for r in _rows(snap, "vm_licensing"):
        if str(r.get("osType") or "").lower() != "windows" or str(r.get("subscriptionId") or "").lower() in dev:
            continue
        if str(r.get("publisher") or "").lower() in ("microsoftwindowsdesktop", "microsoftvisualstudio"):
            continue
        if str(r.get("licenseType") or "").lower().startswith("windows"):
            continue
        yield Finding(
            "LIC-AHBWIN-01", r["id"], "low", "Windows workload is not using Azure Hybrid Benefit: review whether eligible licences with Software Assurance exist",
            {"resType": r.get("resType"), "vmSize": r.get("vmSize"), "licenseType": r.get("licenseType")},
        )  # fmt: skip


@check(
    _cm(
        "LIC-AHBSQL-01",
        "licensing",
        "Licensing and SaaS",
        "SQL Server VMs on pay-as-you-go licensing",
        "sql_vms",
        "subscriptions",
        conf="low",
    )
)
def sql_vms_without_ahb(snap):
    """Hub query rule: sqlServerLicenseType other than AHUB and edition not Developer or Express. Here only an explicit PAYG counts: DR (free DR replica licence, Learn read
    2026-10-18) and unknown values are not reported, and an unknown edition is skipped. Dev/Test subscriptions skipped. Eligibility cannot be read from Azure, so wording is 'review'."""
    dev = _devtest_subs(snap)
    for r in _rows(snap, "sql_vms"):
        sku = str(r.get("sqlImageSku") or "").lower()
        if str(r.get("sqlLicenseType") or "").upper() != "PAYG" or not sku or sku in ("developer", "express"):
            continue
        if str(r.get("subscriptionId") or "").lower() in dev:
            continue
        yield Finding(
            "LIC-AHBSQL-01", r["id"], "low", f"SQL Server VM ({r.get('sqlImageSku')}) pays per use: review Azure Hybrid Benefit eligibility",
            {"sqlImageSku": r.get("sqlImageSku"), "sqlImageOffer": r.get("sqlImageOffer"), "licenseType": r.get("sqlLicenseType")},
        )  # fmt: skip


@check(_cm("OPT-AKSSPT-01", "optimization", "Rate Optimization", "AKS autoscaling user pools not using Spot", "aks_pools", conf="low"))
def aks_pools_not_spot(snap):
    """Hub query idea: autoscaling pool without Spot. Learn (read 2026-10-18): Spot pools must be user pools (never system), have no SLA and are evicted, and suit only
    interruptible work. So this is a prompt to ask the owner, severity info, confidence low; only User-mode autoscaling pools are listed. No saving is claimed."""
    for r in _rows(snap, "aks_pools"):
        if (
            r.get("autoScale") is True
            and str(r.get("poolMode") or "").lower() == "user"
            and str(r.get("priority") or "").lower() in ("", "regular")
        ):
            yield Finding(
                "OPT-AKSSPT-01", f"{r['id']}/agentPools/{r.get('poolName')}", "info",
                "Autoscaling user node pool uses regular VMs: ask whether any of its workloads can tolerate Spot evictions",
                {"vmSize": r.get("vmSize"), "minCount": r.get("minCount"), "maxCount": r.get("maxCount"), "nodeCount": r.get("nodeCount")},
            )  # fmt: skip


ADVISOR_SEVERITY = {"high": "medium", "medium": "low", "low": "info"}
ADVISOR_OPEN_STATES = ("", "new", "inprogress")


@check(
    _cm(
        "ADV-COST-01",
        "advisor",
        "Usage Optimization",
        "Azure Advisor cost recommendations (pass-through)",
        "advisor_cost",
        conf="medium",
        basis="estimate",
    )
)
def advisor_cost(snap):
    """Pass-through of Microsoft's own recommendations, labelled as such. Advisor's savings figure is reported as 'advisor_reported_savings' with its currency and is NOT
    verified by this tool; Learn (read 2026-10-18) does not state its period, and says it uses retail rates and overlapping data sets, so figures must not be summed.
    Completed, Postponed and Dismissed recommendations are skipped (field recommendationStatus; an absent field counts as open)."""
    for r in _rows(snap, "advisor_cost"):
        if str(r.get("status") or "").lower() not in ADVISOR_OPEN_STATES:
            continue
        sav = r.get("savingsAmount")
        yield Finding(
            "ADV-COST-01", r["id"], ADVISOR_SEVERITY.get(str(r.get("impact") or "").lower(), "info"),
            f"Advisor: {_text(r.get('problem')) or 'cost recommendation'}",
            {
                "source": "Azure Advisor",
                "solution": r.get("solution"),
                "typeId": r.get("typeId"),
                "target": r.get("targetResourceId") or r.get("impactedValue"),
                "advisor_reported_savings": sav if isinstance(sav, (int, float)) and not isinstance(sav, bool) else None,
                "advisor_savings_currency": r.get("savingsCurrency"),
                "advisor_savings_period": "not stated by Advisor docs (UNVERIFIED)",
                "lastUpdated": r.get("lastUpdated"),
            },
        )  # fmt: skip


# ---- Batch 6 (2026-10-18). Workbook predicates (MIT, f12c29e); Learn facts read 2026-10-18; all UNVERIFIED live.
IDLE_BACKUP_DAYS = 90  # same threshold as the workbook "Idle backups" query


@check(_cm("IDLE-BKP-01", "orphaned", "Usage Optimization", "Backup items with no backup in 90 days", "backup_items", conf="low"))
def idle_backups(snap):
    """Workbook rule: lastBackupTime older than 90 days at the snapshot's collection time. Items with no timestamp are skipped (never backed up is a different question).
    A stale item may mean failing backups (a reliability problem) or a source that no longer needs protection; the message does not choose. Stopped protection with retained
    data is common and is shown in the details."""
    ref = collected_at(snap)
    for r in _rows(snap, "backup_items"):
        t = _parse_ts(r.get("lastBackupTime"))
        if t is not None and (ref - t).days > IDLE_BACKUP_DAYS:
            yield Finding(
                "IDLE-BKP-01", r["id"], "low", f"No backup for {(ref - t).days} days: check whether backups are failing or the item is no longer needed",
                {"protectionState": r.get("protectionState"), "workloadType": r.get("workloadType"), "source": r.get("sourceResourceId"), "age_days": (ref - t).days},
            )  # fmt: skip


@check(
    _cm(
        "OPT-VAULT-01",
        "optimization",
        "Usage Optimization",
        "Geo-redundant backup vaults in Dev/Test-looking subscriptions",
        "recovery_vaults",
        "subscriptions",
        conf="low",
    )
)
def grs_vaults_in_devtest(snap):
    """Judgement prompt, severity info. Heuristic as SEC-DEFDEV-01: quota id contains 'devtest'. Redundancy value GeoRedundant (workbook property
    standardTierStorageRedundancy). Whether a dev copy needs geo-redundancy is a business decision; no saving is claimed."""
    dev = _devtest_subs(snap)
    for r in _rows(snap, "recovery_vaults"):
        if str(r.get("subscriptionId") or "").lower() in dev and str(r.get("redundancy") or "").lower() == "georedundant":
            yield Finding(
                "OPT-VAULT-01", r["id"], "info", "Recovery Services vault is geo-redundant in a subscription that looks like Dev/Test: review whether that is needed",
                {"redundancy": r.get("redundancy"), "location": r.get("location")},
            )  # fmt: skip


COSMOS_FREE_COPIES = 2  # Learn: two periodic backups are free, extra copies are charged


@check(
    _cm(
        "OPT-COSBKP-01",
        "optimization",
        "Usage Optimization",
        "Cosmos DB accounts paying for extra periodic backup copies",
        "cosmos_accounts",
        conf="low",
    )
)
def cosmos_periodic_extra_copies(snap):
    """Workbook rule: Periodic policy, single-write account, copies = retention hours / interval hours, and copies >= 10 or (copies > 2 and retention <= 168 h).
    Learn (read 2026-10-18): 2 copies are free, extra copies are charged; the Continuous 7-day tier has no backup storage charge, but continuous mode changes the
    restore model, migration is one-way, and some accounts cannot migrate. So this is a prompt to evaluate, not a saving. Missing numbers mean the account is skipped."""
    for r in _rows(snap, "cosmos_accounts"):
        ret, interval = r.get("retentionHours"), r.get("intervalMinutes")
        nums = all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in (ret, interval))
        if str(r.get("backupType") or "").lower() != "periodic" or r.get("multiWrite") is not False or not nums or interval <= 0:
            continue
        copies = ret / (interval / 60)
        if copies >= 10 or (copies > COSMOS_FREE_COPIES and ret <= 168):
            yield Finding(
                "OPT-COSBKP-01", r["id"], "info", f"Periodic backup keeps about {copies:g} copies ({COSMOS_FREE_COPIES} are free): evaluate Continuous 7-day backup",
                {"backup_copies": round(copies, 2), "free_copies": COSMOS_FREE_COPIES, "retentionHours": ret, "intervalMinutes": interval},
            )  # fmt: skip


@check(
    _cm(
        "ORPH-SYN-01",
        "orphaned",
        "Usage Optimization",
        "Synapse workspaces with no dedicated SQL or Spark pools",
        "synapse_workspaces",
        "synapse_pools",
        conf="low",
    )
)
def synapse_workspaces_without_pools(snap):
    """Workbook rule: workspace with zero sqlPools and zero bigDataPools. Learn (read 2026-10-18): every workspace has a serverless SQL endpoint that costs nothing
    until queried, so such a workspace may still be in use and its direct cost may be near zero (the linked storage is not assessed here). Severity info.
    Pool resources are matched to the workspace by id prefix, case-insensitive."""
    owners = set()
    for p in _rows(snap, "synapse_pools"):
        pid = str(p.get("id") or "").lower()
        for marker in ("/sqlpools/", "/bigdatapools/"):
            if marker in pid:
                owners.add(pid.split(marker)[0])
    for w in _rows(snap, "synapse_workspaces"):
        if str(w["id"]).lower() not in owners:
            yield Finding(
                "ORPH-SYN-01", w["id"], "info", "Synapse workspace has no dedicated SQL or Spark pool; serverless SQL may still be in use",
                {"location": w.get("location")},
            )  # fmt: skip


@check(
    _cm(
        "OPT-FWPREM-01",
        "optimization",
        "Rate Optimization",
        "Azure Firewall Premium without IDPS or TLS inspection configured",
        "azure_firewalls",
        "firewall_policies",
        conf="low",
    )
)
def firewall_premium_unused_features(snap):
    """Workbook rule: Premium firewall whose policy has IDPS mode neither Alert nor Deny and no TLS inspection certificate. Learn (read 2026-10-18): Premium also offers URL
    filtering and web categories, which this check does NOT inspect, so 'no premium feature used' is not proven; the message says IDPS and TLS only. Policies with a parent
    policy are skipped because the effective IDPS mode is the stricter of parent and child (Learn). Firewalls whose policy is not in the snapshot are skipped. A missing
    IDPS property is treated as not enabled, as in the workbook (UNVERIFIED live)."""
    pols = {str(p["id"]).lower(): p for p in _rows(snap, "firewall_policies")}
    for f in _rows(snap, "azure_firewalls"):
        if str(f.get("skuTier") or "").lower() != "premium":
            continue
        pol = pols.get(str(f.get("policyId") or "").lower())
        if pol is None or not _blank(pol.get("basePolicyId")):
            continue
        if str(pol.get("idpsMode") or "").lower() in ("alert", "deny") or not _blank(pol.get("tlsSecretId")):
            continue
        yield Finding(
            "OPT-FWPREM-01", f["id"], "low", "Premium firewall: its policy has no IDPS (Alert or Deny) and no TLS inspection; check URL filtering and web categories before considering Standard",
            {"policy": pol["id"], "idpsMode": pol.get("idpsMode"), "location": f.get("location")},
        )  # fmt: skip


@check(
    _cm(
        "RIGHT-VMCPU-01",
        "optimization",
        "Rate Optimization",
        "Running VMs whose peak CPU fits a half-size VM",
        "vm_cpu",
        conf="medium",
        basis="none",
    )
)
def vm_cpu_rightsizing(snap):
    """Opt-in ([run] rightsizing). Uses hourly Maximum CPU over 30 days (RIGHTSIZING.md): candidate when P99 of hourly maxima, scaled by current/target vCPUs, stays at or
    below 60%. CPU only: memory, disk and network are NOT inspected, so the message says so. No saving is claimed (needs list price). Confidence is never high before live validation."""
    data = snap.load("vm_cpu") or {}
    rows, skipped = data.get("rows") or [], data.get("skipped") or []
    hours = (data.get("window") or {}).get("hours")
    if not rows and skipped:
        raise NotAssessed(f"{len(skipped)} running VM(s) could not be assessed (for example: {skipped[0].get('reason')})")
    for r in rows if isinstance(rows, list) else []:
        a = metrics.assess_row(r, hours) if isinstance(r, dict) else None
        if a and a["verdict"] == "candidate":
            yield Finding(
                "RIGHT-VMCPU-01", r["id"], "low",
                f"CPU peaks fit {r['targetSize']} ({a['window_days']} days of data, CPU only; check memory, disk and network before resizing)",
                {"current": r["vmSize"], "candidate": r["targetSize"], "vcpus": r["vcpus"], "target_vcpus": r["targetVcpus"], "assessment": a},
            )  # fmt: skip
