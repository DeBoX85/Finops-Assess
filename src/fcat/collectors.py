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
    "powerDisplay=tostring(properties.extended.instanceView.powerState.displayStatus), tags | order by id asc"
)

COLLECTORS = {
    "subscriptions": KQL_SUBSCRIPTIONS,
    "management_groups": KQL_MANAGEMENT_GROUPS,
    "unattached_disks": KQL_UNATTACHED_DISKS,
    "public_ips": KQL_PUBLIC_IPS,
    "nics": KQL_NICS,
    "nsgs": KQL_NSGS,
    "app_service_plans": KQL_APP_SERVICE_PLANS,
    "vms": KQL_VMS,
}


def collect(client, snapshot, config, errors: list):
    for name, kql in COLLECTORS.items():
        try:
            res = arg.query(client, kql, config.subscriptions or None, config.management_groups or None)
        except Exception as e:  # noqa: BLE001  a failing collector is recorded in the manifest, not hidden
            errors.append({"collector": name, "error": f"{type(e).__name__}: {e}"})
            continue
        snapshot.save(name, {"rows": res.rows, "total_records": res.total_records, "pages": res.pages, "warnings": res.warnings})
