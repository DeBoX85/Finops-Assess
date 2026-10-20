"""Collectors write raw data into the snapshot. Phase 1: inventory + disks."""

from __future__ import annotations

from . import arg

KQL_SUBSCRIPTIONS = (
    "resourcecontainers | where type == 'microsoft.resources/subscriptions' "
    "| project id, name, subscriptionId, tenantId, state=tostring(properties.state), "
    "quotaId=tostring(properties.subscriptionPolicies.quotaId), "
    "mgAncestors=properties.managementGroupAncestorsChain | order by id asc"
)

# Types and ancestor properties per Learn ARG sample queries (read 2026-10-17). Visibility depends on the identity's rights.
KQL_MANAGEMENT_GROUPS = (
    "resourcecontainers | where type =~ 'microsoft.management/managementgroups' "
    "| project id, name, displayName=tostring(properties.displayName), "
    "ancestors=properties.details.managementGroupAncestorsChain | order by id asc"
)

# Logic mirrors the unattached-disk rule in microsoft/finops-toolkit (MIT, see NOTICE.md): no managedBy,
# state not ActiveSAS, excluding ASR replica/seed disks.
KQL_UNATTACHED_DISKS = (
    "resources | where type =~ 'microsoft.compute/disks' and isempty(managedBy) "
    "| project id, name, subscriptionId, resourceGroup, location, skuName=tostring(sku.name), sizeGB=toint(properties.diskSizeGB), "
    "diskState=tostring(properties.diskState), timeCreated=tostring(properties.timeCreated), tags | order by id asc"
)

# Orphan/idle inventory (backlog 7). Property paths follow the ARM schemas as I know them and the finops-toolkit hub
# queries (MIT, see NOTICE.md); UNVERIFIED against a live tenant (offline-only until gate G2). Rules live in Python (ADR 0004).
KQL_PUBLIC_IPS = (
    "resources | where type =~ 'microsoft.network/publicipaddresses' "
    "| project id, name, subscriptionId, resourceGroup, location, skuName=tostring(sku.name), skuTier=tostring(sku.tier), "
    "allocation=tostring(properties.publicIPAllocationMethod), ipConfigId=tostring(properties.ipConfiguration.id), "
    "natGatewayId=tostring(properties.natGateway.id), linkedPublicIpId=tostring(properties.linkedPublicIPAddress.id), tags | order by id asc"
)
KQL_NICS = (
    "resources | where type =~ 'microsoft.network/networkinterfaces' "
    "| project id, name, subscriptionId, resourceGroup, location, vmId=tostring(properties.virtualMachine.id), "
    "privateEndpointId=tostring(properties.privateEndpoint.id), "
    "publicIpIds=pack_array(tostring(properties.ipConfigurations[0].properties.publicIPAddress.id), "
    "tostring(properties.ipConfigurations[1].properties.publicIPAddress.id)), tags | order by id asc"
)
KQL_NSGS = (
    "resources | where type =~ 'microsoft.network/networksecuritygroups' "
    "| project id, name, subscriptionId, resourceGroup, location, nicRefs=properties.networkInterfaces, "
    "subnetRefs=properties.subnets, tags | order by id asc"
)
KQL_APP_SERVICE_PLANS = (
    "resources | where type =~ 'microsoft.web/serverfarms' "
    "| project id, name, subscriptionId, resourceGroup, location, skuName=tostring(sku.name), skuTier=tostring(sku.tier), "
    "skuCapacity=toint(sku.capacity), numberOfSites=toint(properties.numberOfSites), tags | order by id asc"
)

KQL_VMS = (
    "resources | where type =~ 'microsoft.compute/virtualmachines' "
    "| project id, name, subscriptionId, resourceGroup, location, vmSize=tostring(properties.hardwareProfile.vmSize), "
    "powerState=tostring(properties.extended.instanceView.powerState.code), "
    "powerDisplay=tostring(properties.extended.instanceView.powerState.displayStatus), "
    "osDiskId=tostring(properties.storageProfile.osDisk.managedDisk.id), osDiskVhdUri=tostring(properties.storageProfile.osDisk.vhd.uri), "
    "dataDisks=properties.storageProfile.dataDisks, tags | order by id asc"
)

# Batch 3 (backlog 7). Predicates re-read from the hub queries at finops-toolkit f12c29e on 2026-10-18; UNVERIFIED live.
_NET = "resources | where type =~ '{t}' | project id, name, subscriptionId, resourceGroup, location, {f}tags | order by id asc"
KQL_LOAD_BALANCERS = _NET.format(
    t="microsoft.network/loadbalancers", f="skuName=tostring(sku.name), backendPoolCount=array_length(properties.backendAddressPools), "
)
KQL_APP_GATEWAYS = _NET.format(
    t="microsoft.network/applicationgateways",
    f="skuName=tostring(properties.sku.name), skuTier=tostring(properties.sku.tier), skuCapacity=toint(properties.sku.capacity), "
    "backendPools=properties.backendAddressPools, ",
)
KQL_ELASTIC_POOLS = _NET.format(t="microsoft.sql/servers/elasticpools", f="skuName=tostring(sku.name), skuTier=tostring(sku.tier), ")
KQL_SQL_DATABASES = _NET.format(t="microsoft.sql/servers/databases", f="elasticPoolId=tostring(properties.elasticPoolId), ")
KQL_VNET_GATEWAYS = _NET.format(
    t="microsoft.network/virtualnetworkgateways",
    f="gatewayType=tostring(properties.gatewayType), skuName=tostring(properties.sku.name), "
    "p2sConfigured=isnotnull(properties.vpnClientConfiguration), ",
)
KQL_VNET_CONNECTIONS = _NET.format(
    t="microsoft.network/connections",
    f="gateway1=tostring(properties.virtualNetworkGateway1.id), gateway2=tostring(properties.virtualNetworkGateway2.id), ",
)
KQL_NAT_GATEWAYS = _NET.format(
    t="microsoft.network/natgateways", f="skuName=tostring(sku.name), subnetCount=array_length(properties.subnets), "
)
KQL_DDOS_PLANS = _NET.format(t="microsoft.network/ddosprotectionplans", f="vnetCount=array_length(properties.virtualNetworks), ")
KQL_ER_CIRCUITS = _NET.format(
    t="microsoft.network/expressroutecircuits",
    f="providerState=tostring(properties.serviceProviderProvisioningState), circuitState=tostring(properties.circuitProvisioningState), "
    "skuTier=tostring(sku.tier), portId=tostring(properties.expressRoutePort.id), ",
)

# Monitoring and security, tier A (docs/MODULE-MONITORING-SECURITY.md). Property names UNVERIFIED live; two casings read where Learn is unclear.
KQL_LA_WORKSPACES = _NET.format(
    t="microsoft.operationalinsights/workspaces",
    f="skuName=tostring(properties.sku.name), capacityLevel=toint(properties.sku.capacityReservationLevel), "
    "retentionInDays=toint(properties.retentionInDays), dailyQuotaGb=todouble(properties.workspaceCapping.dailyQuotaGb), ",
)
KQL_APP_INSIGHTS = _NET.format(
    t="microsoft.insights/components",
    f="workspaceResourceId=tostring(coalesce(properties.WorkspaceResourceId, properties.workspaceResourceId)), "
    "ingestionMode=tostring(coalesce(properties.IngestionMode, properties.ingestionMode)), ",
)
# Source: Learn, Defender for Cloud Resource Graph samples (read 2026-10-18)
KQL_DEFENDER_PRICINGS = (
    "securityresources | where type == 'microsoft.security/pricings' "
    "| project id, name, subscriptionId, pricingTier=tostring(properties.pricingTier), subPlan=tostring(properties.subPlan) | order by id asc"
)

# Batch 4. Predicates from the finops-toolkit hub queries and Storage/Networking workbooks (MIT, commit f12c29e, read 2026-10-18); UNVERIFIED live.
KQL_SNAPSHOTS = _NET.format(
    t="microsoft.compute/snapshots",
    f="skuName=tostring(sku.name), skuTier=tostring(sku.tier), sizeGB=toint(properties.diskSizeGB), "
    "timeCreated=tostring(properties.timeCreated), sourceResourceId=tostring(properties.creationData.sourceResourceId), ",
)
KQL_ALL_DISKS = _NET.format(t="microsoft.compute/disks", f="skuName=tostring(sku.name), sizeGB=toint(properties.diskSizeGB), ")
KQL_STORAGE_ACCOUNTS = _NET.format(
    t="microsoft.storage/storageaccounts", f="kind=tostring(kind), skuName=tostring(sku.name), accessTier=tostring(properties.accessTier), "
)
KQL_PRIVATE_DNS = _NET.format(
    t="microsoft.network/privatednszones",
    f="linkCount=toint(properties.numberOfVirtualNetworkLinks), recordSets=toint(properties.numberOfRecordSets), ",
)
KQL_PRIVATE_ENDPOINTS = _NET.format(
    t="microsoft.network/privateendpoints",
    f="connState=tostring(iff(array_length(properties.manualPrivateLinkServiceConnections) > 0, "
    "properties.manualPrivateLinkServiceConnections[0], properties.privateLinkServiceConnections[0])"
    ".properties.privateLinkServiceConnectionState.status), ",
)

# Batch 5 (2026-10-18). Hub queries VMsWithoutAHB, SQLVMsWithoutAHB, NonSpotAKSClusters, AdvisorCost (MIT, f12c29e); UNVERIFIED live.
# VMs and scale sets share one query: VMSS keep their profile under properties.virtualMachineProfile.
KQL_VM_LICENSING = (
    "resources | where type =~ 'microsoft.compute/virtualmachines' or type =~ 'microsoft.compute/virtualmachinescalesets' "
    "| project id, name, subscriptionId, resourceGroup, location, resType=type, "
    "vmSize=tostring(coalesce(properties.hardwareProfile.vmSize, sku.name)), "
    "osType=tostring(coalesce(properties.storageProfile.osDisk.osType, properties.virtualMachineProfile.storageProfile.osDisk.osType)), "
    "publisher=tostring(coalesce(properties.storageProfile.imageReference.publisher, "
    "properties.virtualMachineProfile.storageProfile.imageReference.publisher)), "
    "licenseType=tostring(coalesce(properties.licenseType, properties.virtualMachineProfile.licenseType)), tags | order by id asc"
)
KQL_SQL_VMS = _NET.format(
    t="microsoft.sqlvirtualmachine/sqlvirtualmachines",
    f="sqlLicenseType=tostring(properties.sqlServerLicenseType), sqlImageSku=tostring(properties.sqlImageSku), "
    "sqlImageOffer=tostring(properties.sqlImageOffer), vmResourceId=tostring(properties.virtualMachineResourceId), ",
)
KQL_AKS_POOLS = (
    "resources | where type =~ 'microsoft.containerservice/managedclusters' | mv-expand pool = properties.agentPoolProfiles "
    "| project id, name, subscriptionId, resourceGroup, location, poolName=tostring(pool.name), poolMode=tostring(pool.mode), "
    "autoScale=tobool(pool.enableAutoScaling), priority=tostring(pool.scaleSetPriority), vmSize=tostring(pool.vmSize), "
    "nodeCount=toint(pool['count']), minCount=toint(pool.minCount), maxCount=toint(pool.maxCount), tags | order by id asc"
)
# savingsAmount and savingsCurrency: Learn, Resource Graph samples for Advisor (read 2026-10-18). Period of savingsAmount is NOT stated there.
KQL_ADVISOR_COST = (
    "advisorresources | where type == 'microsoft.advisor/recommendations' | where properties.category == 'Cost' "
    "| project id, subscriptionId, resourceGroup, impact=tostring(properties.impact), "
    "problem=tostring(properties.shortDescription.problem), solution=tostring(properties.shortDescription.solution), "
    "typeId=tostring(properties.recommendationTypeId), targetResourceId=tolower(tostring(properties.resourceMetadata.resourceId)), "
    "impactedValue=tostring(properties.impactedValue), status=tostring(properties.recommendationStatus), "
    "savingsAmount=todouble(properties.extendedProperties.savingsAmount), "
    "savingsCurrency=tostring(properties.extendedProperties.savingsCurrency), lastUpdated=tostring(properties.lastUpdated) | order by id asc"
)

# Batch 6 (2026-10-18). Workbook queries (MIT, f12c29e): idleBackups, backupStorageReplication, Cosmos DB backup modes, Synapse unused workspaces, Optimize Premium AZ Firewall.
# Property names from the workbook and Learn ARM schemas (read 2026-10-18); UNVERIFIED live.
KQL_BACKUP_ITEMS = (
    "recoveryservicesresources | where type =~ 'microsoft.recoveryservices/vaults/backupfabrics/protectioncontainers/protecteditems' "
    "| project id, name, subscriptionId, resourceGroup, location, vaultId=tostring(properties.vaultId), "
    "sourceResourceId=tostring(properties.sourceResourceId), workloadType=tostring(properties.workloadType), "
    "protectionState=tostring(properties.protectionState), lastBackupTime=tostring(properties.lastBackupTime) | order by id asc"
)
KQL_RECOVERY_VAULTS = _NET.format(
    t="microsoft.recoveryservices/vaults",
    f="skuName=tostring(sku.name), redundancy=tostring(properties.redundancySettings.standardTierStorageRedundancy), ",
)
KQL_COSMOS_ACCOUNTS = _NET.format(
    t="microsoft.documentdb/databaseaccounts",
    f="backupType=tostring(properties.backupPolicy.type), "
    "retentionHours=toint(properties.backupPolicy.periodicModeProperties.backupRetentionIntervalInHours), "
    "intervalMinutes=toint(properties.backupPolicy.periodicModeProperties.backupIntervalInMinutes), "
    "multiWrite=tobool(properties.enableMultipleWriteLocations), ",
)
KQL_SYNAPSE_WORKSPACES = _NET.format(t="microsoft.synapse/workspaces", f="")
KQL_SYNAPSE_POOLS = (
    "resources | where type in~ ('microsoft.synapse/workspaces/sqlpools', 'microsoft.synapse/workspaces/bigdatapools') "
    "| project id, name, subscriptionId, resourceGroup, location, poolType=type, tags | order by id asc"
)
KQL_AZURE_FIREWALLS = _NET.format(
    t="microsoft.network/azurefirewalls", f="skuTier=tostring(properties.sku.tier), policyId=tostring(properties.firewallPolicy.id), "
)
KQL_FIREWALL_POLICIES = _NET.format(
    t="microsoft.network/firewallpolicies",
    f="skuTier=tostring(properties.sku.tier), idpsMode=tostring(properties.intrusionDetection.mode), "
    "tlsSecretId=tostring(properties.transportSecurity.certificateAuthority.keyVaultSecretId), "
    "basePolicyId=tostring(properties.basePolicy.id), ",
)

# Cost governance, phase 1 (docs/COST-GOVERNANCE.md). Whole-estate tag inventory, container tags, policy assignments and state counts.
# Property names for policy are UNVERIFIED live. Policy assignments are read with AuthorizationScopeFilter=AtScopeAboveAndBelow so assignments
# made at management group or tenant root level are included (Learn query-language page, read 2026-10-20).
KQL_TAG_INVENTORY = "resources | project id, type, subscriptionId, resourceGroup, tags | order by id asc"
KQL_CONTAINER_TAGS = (
    "resourcecontainers | where type in~ ('microsoft.resources/subscriptions/resourcegroups', 'microsoft.resources/subscriptions') "
    "| project id, type, subscriptionId, name, tags | order by id asc"
)
KQL_POLICY_ASSIGNMENTS = (
    "policyresources | where type =~ 'microsoft.authorization/policyassignments' "
    "| project id, name, scope=tostring(properties.scope), definitionId=tostring(properties.policyDefinitionId), "
    "enforcementMode=tostring(properties.enforcementMode), parameters=properties.parameters | order by id asc"
)
KQL_POLICY_STATES = (
    "policyresources | where type =~ 'microsoft.policyinsights/policystates' "
    "| summarize n=count() by assignmentId=tostring(properties.policyAssignmentId), state=tostring(properties.complianceState) "
    "| order by assignmentId asc"
)
COLLECTOR_OPTIONS = {"policy_assignments": {"authorization_scope_filter": "AtScopeAboveAndBelow"}}

COLLECTORS = {
    "tag_inventory": KQL_TAG_INVENTORY,
    "container_tags": KQL_CONTAINER_TAGS,
    "policy_assignments": KQL_POLICY_ASSIGNMENTS,
    "policy_states": KQL_POLICY_STATES,
    "subscriptions": KQL_SUBSCRIPTIONS,
    "management_groups": KQL_MANAGEMENT_GROUPS,
    "unattached_disks": KQL_UNATTACHED_DISKS,
    "public_ips": KQL_PUBLIC_IPS,
    "nics": KQL_NICS,
    "nsgs": KQL_NSGS,
    "app_service_plans": KQL_APP_SERVICE_PLANS,
    "vms": KQL_VMS,
    "load_balancers": KQL_LOAD_BALANCERS,
    "app_gateways": KQL_APP_GATEWAYS,
    "elastic_pools": KQL_ELASTIC_POOLS,
    "sql_databases": KQL_SQL_DATABASES,
    "vnet_gateways": KQL_VNET_GATEWAYS,
    "vnet_connections": KQL_VNET_CONNECTIONS,
    "nat_gateways": KQL_NAT_GATEWAYS,
    "ddos_plans": KQL_DDOS_PLANS,
    "er_circuits": KQL_ER_CIRCUITS,
    "la_workspaces": KQL_LA_WORKSPACES,
    "app_insights": KQL_APP_INSIGHTS,
    "defender_pricings": KQL_DEFENDER_PRICINGS,
    "snapshots": KQL_SNAPSHOTS,
    "all_disks": KQL_ALL_DISKS,
    "storage_accounts": KQL_STORAGE_ACCOUNTS,
    "private_dns_zones": KQL_PRIVATE_DNS,
    "private_endpoints": KQL_PRIVATE_ENDPOINTS,
    "vm_licensing": KQL_VM_LICENSING,
    "sql_vms": KQL_SQL_VMS,
    "aks_pools": KQL_AKS_POOLS,
    "advisor_cost": KQL_ADVISOR_COST,
    "backup_items": KQL_BACKUP_ITEMS,
    "recovery_vaults": KQL_RECOVERY_VAULTS,
    "cosmos_accounts": KQL_COSMOS_ACCOUNTS,
    "synapse_workspaces": KQL_SYNAPSE_WORKSPACES,
    "synapse_pools": KQL_SYNAPSE_POOLS,
    "azure_firewalls": KQL_AZURE_FIREWALLS,
    "firewall_policies": KQL_FIREWALL_POLICIES,
}


# Collectors that are not ARG queries. They run only when the owner opts in and are never in COLLECTORS (which the KQL tests iterate).
REST_COLLECTORS = ("vm_cpu", "budgets", "anomaly_rules", "cost_exports")


def collect(client, snapshot, config, errors: list):
    import datetime as dt  # noqa: PLC0415

    snapshot.save("_meta", {"collected_at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")})
    for name, kql in COLLECTORS.items():
        try:
            res = arg.query(client, kql, config.subscriptions or None, config.management_groups or None, **COLLECTOR_OPTIONS.get(name, {}))
        except Exception as e:  # noqa: BLE001  a failing collector is recorded in the manifest, not hidden
            errors.append({"collector": name, "error": f"{type(e).__name__}: {e}"})
            continue
        snapshot.save(name, {"rows": res.rows, "total_records": res.total_records, "pages": res.pages, "warnings": res.warnings})
    if getattr(config, "governance_apis", False):
        from . import govcost  # noqa: PLC0415

        try:
            govcost.collect_governance(client, snapshot, config, errors)
        except Exception as e:  # noqa: BLE001
            errors.append({"collector": "governance_apis", "error": f"{type(e).__name__}: {e}"})
    if getattr(config, "rightsizing", False):
        from . import metrics  # noqa: PLC0415

        try:
            metrics.collect_rightsizing(
                client, snapshot, config, errors, dt.datetime.fromisoformat(snapshot.load("_meta")["collected_at"].replace("Z", "+00:00"))
            )
        except Exception as e:  # noqa: BLE001
            errors.append({"collector": "vm_cpu", "error": f"{type(e).__name__}: {e}"})
