"""Collectors write raw data into the snapshot. Phase 1: inventory + disks."""
from __future__ import annotations
from . import arg

KQL_SUBSCRIPTIONS = ("resourcecontainers | where type == 'microsoft.resources/subscriptions' "
                     "| project id, name, subscriptionId, tenantId, state=tostring(properties.state), "
                     "mgAncestors=properties.managementGroupAncestorsChain | order by id asc")

# Types and ancestor properties per Learn ARG sample queries (read 2026-10-17). Visibility depends on the identity's rights.
KQL_MANAGEMENT_GROUPS = ("resourcecontainers | where type =~ 'microsoft.management/managementgroups' "
                         "| project id, name, displayName=tostring(properties.displayName), "
                         "ancestors=properties.details.managementGroupAncestorsChain | order by id asc")

# Logic mirrors the unattached-disk rule in microsoft/finops-toolkit (MIT, see NOTICE.md): no managedBy,
# state not ActiveSAS, excluding ASR replica/seed disks.
KQL_UNATTACHED_DISKS = (
    "resources | where type =~ 'microsoft.compute/disks' and isempty(managedBy) "
    "| extend diskState = tostring(properties.diskState) "
    "| where diskState != 'ActiveSAS' and tags !contains 'ASR-ReplicaDisk' and tags !contains 'asrseeddisk' "
    "| project id, name, subscriptionId, resourceGroup, location, skuName=tostring(sku.name), sizeGB=toint(properties.diskSizeGB), "
    "diskState, timeCreated=tostring(properties.timeCreated) | order by id asc")

COLLECTORS = {
    "subscriptions": KQL_SUBSCRIPTIONS,
    "management_groups": KQL_MANAGEMENT_GROUPS,
    "unattached_disks": KQL_UNATTACHED_DISKS,
}

def collect(client, snapshot, config, errors: list):
    for name, kql in COLLECTORS.items():
        try:
            res = arg.query(client, kql, config.subscriptions or None, config.management_groups or None)
        except Exception as e:
            errors.append({"collector": name, "error": f"{type(e).__name__}: {e}"})
            continue
        snapshot.save(name, {"rows": res.rows, "total_records": res.total_records, "pages": res.pages, "warnings": res.warnings})
