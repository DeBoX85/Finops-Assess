"""Generate the synthetic estate snapshot (deterministic, no real data, no GUIDs) and optionally approve the golden report.
python scripts/make_synthetic.py            regenerate tests/synthetic/snapshot
python scripts/make_synthetic.py --approve  also rewrite tests/golden/report.json (a human must review the diff first)
"""

import json
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SNAP = ROOT / "tests" / "synthetic" / "snapshot"
GOLDEN = ROOT / "tests" / "golden" / "report.json"


def estate():
    quota = {1: "EnterpriseAgreement_2014-09-01", 2: "CSP_2015-05-01", 3: "Sponsored_2016-01-01"}  # supported / ambiguous / unsupported
    subs = [
        {"id": f"/subscriptions/sub-synth-{i}", "name": f"Synthetic Sub {i}", "quotaId": quota[i], "mgAncestors": ["mg-synth-root"]}
        for i in (1, 2, 3)
    ]
    mgs = [
        {
            "id": "/providers/Microsoft.Management/managementGroups/mg-synth-root",
            "name": "mg-synth-root",
            "displayName": "Synthetic Root",
            "ancestors": [],
        },
        {
            "id": "/providers/Microsoft.Management/managementGroups/mg-synth-prod",
            "name": "mg-synth-prod",
            "displayName": "Synthetic Prod",
            "ancestors": ["mg-synth-root"],
        },
    ]
    disks = []

    def disk(n, sub=1, **kw):
        d = {
            "id": f"/subscriptions/sub-synth-{sub}/resourceGroups/rg-synth/providers/Microsoft.Compute/disks/disk-{n:03d}",
            "name": f"disk-{n:03d}",
            "subscriptionId": f"sub-synth-{sub}",
            "resourceGroup": "rg-synth",
            "location": ["westeurope", "northeurope", "swedencentral"][n % 3],
            "skuName": ["Premium_LRS", "StandardSSD_LRS", "Standard_LRS"][n % 3],
            "sizeGB": 32 * (1 + n % 8),
            "diskState": "Unattached",
            "timeCreated": f"2025-0{1 + n % 9}-15T10:00:00Z",
            "tags": {"env": "dev"} if n % 4 == 0 else None,
        }
        d.update(kw)
        return d

    for n in range(1, 61):  # bulk: 60 plain orphans spread over subscriptions
        disks.append(disk(n, sub=1 + n % 3))
    disks += [  # edge cases, each documents a rule
        disk(100, diskState="ActiveSAS"),  # excluded: SAS export in progress
        disk(101, tags={"ASR-ReplicaDisk": "x"}),  # excluded: ASR replica, tag case as Azure writes it
        disk(102, tags={"asrseeddisk": "1"}),  # excluded: ASR seed disk
        disk(103, tags={"ASRSEEDDISK": "1"}),  # excluded: upper case tag key
        disk(104, tags={"env": "prod", "owner": "team-a"}),  # reported: unrelated tags
        disk(105, sizeGB=None),  # reported: size missing
        disk(106, sizeGB=0),  # reported: zero size
        disk(107, sizeGB=32767, skuName="UltraSSD_LRS"),  # reported: very large
        disk(108, name="disk-ünïcode-日本", location=None),  # reported: unicode name, missing location
        disk(109, tags={}),  # reported: empty tags
    ]
    base = "/subscriptions/sub-synth-1/resourceGroups/rg-synth/providers/Microsoft."
    pips = [
        {"id": base + "Network/publicIPAddresses/pip-orphan-1", "skuName": "Standard", "allocation": "Static", "location": "westeurope"},
        {"id": base + "Network/publicIPAddresses/pip-orphan-2", "skuName": "Basic", "allocation": "Dynamic", "ipConfigId": ""},
        {
            "id": base + "Network/publicIPAddresses/pip-vm",
            "skuName": "Standard",
            "ipConfigId": base + "Network/networkInterfaces/nic-vm/ipConfigurations/ip1",
        },
        {
            "id": base + "Network/publicIPAddresses/pip-via-orphan-nic",
            "skuName": "Standard",
            "ipConfigId": base + "Network/networkInterfaces/nic-orphan/ipConfigurations/ip1",
        },
        {"id": base + "Network/publicIPAddresses/pip-nat", "skuName": "Standard", "natGatewayId": base + "Network/natGateways/nat-1"},
    ]
    nics = [
        {
            "id": base + "Network/networkInterfaces/nic-orphan",
            "vmId": None,
            "privateEndpointId": None,
            "publicIpIds": [base + "Network/publicIPAddresses/pip-via-orphan-nic"],
        },
        {"id": base + "Network/networkInterfaces/nic-vm", "vmId": base + "Compute/virtualMachines/vm-1"},
        {"id": base + "Network/networkInterfaces/nic-pe", "privateEndpointId": base + "Network/privateEndpoints/pe-1"},
    ]
    nsgs = [
        {"id": base + "Network/networkSecurityGroups/nsg-orphan", "nicRefs": [], "subnetRefs": []},
        {"id": base + "Network/networkSecurityGroups/nsg-subnet", "nicRefs": [], "subnetRefs": [{"id": "subnet-1"}]},
        {"id": base + "Network/networkSecurityGroups/nsg-absent", "nicRefs": None, "subnetRefs": None},
    ]
    asps = [
        {"id": base + "Web/serverFarms/asp-empty", "skuName": "P1v3", "skuTier": "PremiumV3", "numberOfSites": 0},
        {"id": base + "Web/serverFarms/asp-free", "skuName": "F1", "skuTier": "Free", "numberOfSites": 0},
        {"id": base + "Web/serverFarms/asp-used", "skuName": "B1", "skuTier": "Basic", "numberOfSites": 3},
    ]
    vms = [
        {
            "id": base + "Compute/virtualMachines/vm-stopped",
            "vmSize": "Standard_D4s_v5",
            "powerState": "PowerState/stopped",
            "powerDisplay": "VM stopped",
            "osDiskId": base + "Compute/disks/VM-STOPPED-OS",
            "dataDisks": [],
        },
        {
            "id": base + "Compute/virtualMachines/vm-dealloc",
            "vmSize": "Standard_D4s_v5",
            "powerState": "PowerState/deallocated",
            "powerTime": "2026-05-01T00:00:00Z",  # 153 days before the synthetic collection time: IDLE-VMDEAL-01 must fire
            "osDiskId": base + "Compute/disks/vm-dealloc-os",
        },
        {  # 16 days: must NOT fire. No disk id so no other check is touched.
            "id": base + "Compute/virtualMachines/vm-dealloc-recent",
            "vmSize": "Standard_B2s",
            "powerState": "PowerState/deallocated",
            "powerTime": "2026-09-15T00:00:00Z",
        },
        {"id": base + "Compute/virtualMachines/vm-run", "vmSize": "Standard_B2s", "powerState": "PowerState/running"},
        {
            "id": base + "Compute/virtualMachines/vm-unmanaged",
            "vmSize": "Standard_D2s_v3",
            "powerState": "PowerState/running",
            "osDiskId": None,
            "osDiskVhdUri": "https://stsynth.blob.core.windows.net/vhds/vm-unmanaged-os.vhd",
        },
    ]
    P = lambda ips=0, adr=0: {"properties": {"backendIPConfigurations": [{}] * ips, "backendAddresses": [{}] * adr}}  # noqa: E731
    net = base + "Network/"
    batch3 = {
        "load_balancers": [
            {"id": net + "loadBalancers/lb-nopool", "skuName": "Standard", "backendPoolCount": 0},
            {"id": net + "loadBalancers/lb-ok", "skuName": "Standard", "backendPoolCount": 2},
            {"id": net + "loadBalancers/lb-basic", "skuName": "Basic", "backendPoolCount": 0},
        ],
        "app_gateways": [
            {"id": net + "applicationGateways/agw-empty", "skuName": "WAF_v2", "backendPools": [P()]},
            {"id": net + "applicationGateways/agw-ok", "skuName": "Standard_v2", "backendPools": [P(adr=1)]},
            {"id": net + "applicationGateways/agw-v1", "skuName": "Standard_Medium", "skuTier": "Standard", "backendPools": [P(ips=1)]},
        ],
        "elastic_pools": [
            {"id": base + "Sql/servers/sql1/elasticPools/pool-empty", "skuName": "GP_Gen5"},
            {"id": base + "Sql/servers/sql1/elasticPools/pool-used", "skuName": "GP_Gen5"},
        ],
        "sql_databases": [
            {"id": base + "Sql/servers/sql1/databases/db1", "elasticPoolId": base + "Sql/servers/sql1/elasticPools/POOL-USED"}
        ],
        "vnet_gateways": [
            {"id": net + "virtualNetworkGateways/gw-idle", "gatewayType": "Vpn", "skuName": "VpnGw1"},
            {"id": net + "virtualNetworkGateways/gw-p2s", "gatewayType": "Vpn", "p2sConfigured": True},
            {"id": net + "virtualNetworkGateways/gw-conn", "gatewayType": "ExpressRoute"},
        ],
        "vnet_connections": [{"id": net + "connections/c1", "gateway1": net + "virtualNetworkGateways/GW-CONN", "gateway2": ""}],
        "nat_gateways": [
            {"id": net + "natGateways/nat-orphan", "subnetCount": 0},
            {"id": net + "natGateways/nat-used", "subnetCount": 1},
        ],
        "ddos_plans": [
            {"id": net + "ddosProtectionPlans/ddos-unused", "vnetCount": 0},
            {"id": net + "ddosProtectionPlans/ddos-used", "vnetCount": 3},
        ],
        "er_circuits": [
            {"id": net + "expressRouteCircuits/erc-pending", "providerState": "NotProvisioned"},
            {"id": net + "expressRouteCircuits/erc-ok", "providerState": "Provisioned"},
        ],
    }
    mon = base + "OperationalInsights/workspaces/"
    tier_a = {
        "la_workspaces": [
            {"id": mon + "law-nocap", "skuName": "PerGB2018", "dailyQuotaGb": -1},
            {"id": mon + "law-capped", "skuName": "PerGB2018", "dailyQuotaGb": 10.0},
            {"id": mon + "law-free", "skuName": "Free"},
        ],
        "app_insights": [
            {"id": base + "Insights/components/ai-old", "workspaceResourceId": ""},
            {"id": base + "Insights/components/ai-new", "workspaceResourceId": mon + "law-capped"},
        ],
        "defender_pricings": [
            {
                "id": "/subscriptions/sub-synth-4/providers/Microsoft.Security/pricings/VirtualMachines",
                "name": "VirtualMachines",
                "subscriptionId": "sub-synth-4",
                "pricingTier": "Standard",
                "subPlan": "P2",
            },
            {
                "id": "/subscriptions/sub-synth-4/providers/Microsoft.Security/pricings/Arm",
                "name": "Arm",
                "subscriptionId": "sub-synth-4",
                "pricingTier": "Free",
            },
            {
                "id": "/subscriptions/sub-synth-1/providers/Microsoft.Security/pricings/VirtualMachines",
                "name": "VirtualMachines",
                "subscriptionId": "sub-synth-1",
                "pricingTier": "Standard",
            },
        ],
    }
    subs.append(
        {"id": "/subscriptions/sub-synth-4", "name": "Synthetic Dev", "quotaId": "MSDNDevTest_2014-09-01", "mgAncestors": ["mg-synth-root"]}
    )
    subs.append(
        {
            "id": "/subscriptions/sub-synth-5",
            "name": "Synthetic Staging",
            "quotaId": "EnterpriseAgreement_2014-09-01",
            "mgAncestors": ["mg-synth-root"],
        }
    )
    comp = base + "Compute/"
    batch4 = {
        "snapshots": [
            {
                "id": comp + "snapshots/snap-old",
                "skuName": "Standard_LRS",
                "sizeGB": 128,
                "timeCreated": "2026-06-01T00:00:00Z",
                "sourceResourceId": comp + "disks/disk-src-ok",
            },
            {
                "id": comp + "snapshots/snap-new-premium",
                "skuName": "Premium_LRS",
                "sizeGB": 64,
                "timeCreated": "2026-09-25T00:00:00Z",
                "sourceResourceId": comp + "disks/disk-src-ok",
            },
            {
                "id": comp + "snapshots/snap-orphan-src",
                "skuName": "Standard_LRS",
                "sizeGB": 32,
                "timeCreated": "2026-09-30T00:00:00Z",
                "sourceResourceId": comp + "disks/disk-deleted",
            },
        ],
        "all_disks": [
            {"id": comp + "disks/disk-src-ok", "skuName": "Premium_LRS", "sizeGB": 128},
            {"id": comp + "disks/vm-stopped-os", "skuName": "Premium_LRS", "sizeGB": 128},
            {"id": comp + "disks/vm-dealloc-os", "skuName": "StandardSSD_LRS", "sizeGB": 64},
            {
                "id": "/subscriptions/sub-synth-4/resourceGroups/rg-synth/providers/Microsoft.Compute/disks/dev-prem",
                "subscriptionId": "sub-synth-4",
                "skuName": "Premium_LRS",
                "sizeGB": 256,
            },
        ],
        "storage_accounts": [
            {"id": base + "Storage/storageAccounts/stlegacy", "kind": "Storage", "skuName": "Standard_LRS"},
            {"id": base + "Storage/storageAccounts/stv2", "kind": "StorageV2", "skuName": "Standard_LRS"},
            {"id": base + "Storage/storageAccounts/stv2nolc", "kind": "StorageV2", "skuName": "Standard_LRS"},
            {
                "id": "/subscriptions/sub-synth-4/resourceGroups/rg-synth/providers/Microsoft.Storage/storageAccounts/stdevgrs",
                "subscriptionId": "sub-synth-4",
                "kind": "StorageV2",
                "skuName": "Standard_GRS",
            },
        ],
        "private_dns_zones": [
            {"id": net + "privateDnsZones/privatelink.unused.example", "linkCount": 0, "recordSets": 1},
            {"id": net + "privateDnsZones/privatelink.used.example", "linkCount": 2},
        ],
        "private_endpoints": [
            {"id": net + "privateEndpoints/pe-dead", "connState": "Disconnected"},
            {"id": net + "privateEndpoints/pe-ok", "connState": "Approved"},
        ],
    }
    sub4 = "/subscriptions/sub-synth-4/resourceGroups/rg-synth/providers/Microsoft."
    batch5 = {
        "vm_licensing": [
            {
                "id": base + "Compute/virtualMachines/win-payg",
                "subscriptionId": "sub-synth-1",
                "osType": "Windows",
                "publisher": "MicrosoftWindowsServer",
                "licenseType": None,
                "resType": "microsoft.compute/virtualmachines",
                "vmSize": "Standard_D4s_v5",
            },
            {
                "id": base + "Compute/virtualMachines/win-ahb",
                "subscriptionId": "sub-synth-1",
                "osType": "Windows",
                "publisher": "MicrosoftWindowsServer",
                "licenseType": "Windows_Server",
            },
            {
                "id": base + "Compute/virtualMachines/linux-1",
                "subscriptionId": "sub-synth-1",
                "osType": "Linux",
                "publisher": "canonical",
                "licenseType": None,
            },
            {
                "id": sub4 + "Compute/virtualMachines/win-dev",
                "subscriptionId": "sub-synth-4",
                "osType": "Windows",
                "publisher": "MicrosoftWindowsServer",
                "licenseType": None,
            },
        ],
        "sql_vms": [
            {
                "id": base + "SqlVirtualMachine/sqlVirtualMachines/sql-payg",
                "subscriptionId": "sub-synth-1",
                "sqlLicenseType": "PAYG",
                "sqlImageSku": "Enterprise",
                "sqlImageOffer": "SQL2022-WS2022",
            },
            {
                "id": base + "SqlVirtualMachine/sqlVirtualMachines/sql-ahub",
                "subscriptionId": "sub-synth-1",
                "sqlLicenseType": "AHUB",
                "sqlImageSku": "Enterprise",
            },
            {
                "id": sub4 + "SqlVirtualMachine/sqlVirtualMachines/sql-dev",
                "subscriptionId": "sub-synth-4",
                "sqlLicenseType": "PAYG",
                "sqlImageSku": "Standard",
            },
        ],
        "aks_pools": [
            {
                "id": base + "ContainerService/managedClusters/aks-1",
                "poolName": "system",
                "poolMode": "System",
                "autoScale": True,
                "priority": None,
            },
            {
                "id": base + "ContainerService/managedClusters/aks-1",
                "poolName": "apps",
                "poolMode": "User",
                "autoScale": True,
                "priority": None,
                "vmSize": "Standard_D4s_v5",
                "minCount": 2,
                "maxCount": 8,
                "nodeCount": 3,
            },
        ],
        "advisor_cost": [
            {
                "id": base + "Advisor/recommendations/rec-resize",
                "impact": "High",
                "problem": "Right-size or shutdown underutilized virtual machines",
                "solution": "Resize",
                "status": "New",
                "savingsAmount": 100.0,
                "savingsCurrency": "USD",
                "targetResourceId": "/subscriptions/sub-synth-1/resourcegroups/rg-synth/providers/microsoft.compute/virtualmachines/vm-run",
            },
            {
                "id": base + "Advisor/recommendations/rec-dismissed",
                "impact": "Medium",
                "problem": "Buy reserved instances",
                "status": "Dismissed",
                "savingsAmount": 50.0,
                "savingsCurrency": "USD",
            },
        ],
    }
    rsv = "Microsoft.RecoveryServices/vaults/"
    syn = base + "Synapse/workspaces/"
    batch6 = {
        "backup_items": [
            {
                "id": base + rsv + "vault1/backupFabrics/Azure/protectionContainers/c1/protectedItems/vm-old",
                "lastBackupTime": "2026-05-01T00:00:00Z",
                "protectionState": "Protected",
                "workloadType": "VM",
            },
            {
                "id": base + rsv + "vault1/backupFabrics/Azure/protectionContainers/c1/protectedItems/vm-recent",
                "lastBackupTime": "2026-09-30T00:00:00Z",
                "protectionState": "Protected",
                "workloadType": "VM",
            },
        ],
        "recovery_vaults": [
            {"id": sub4 + "RecoveryServices/vaults/vault-dev-grs", "subscriptionId": "sub-synth-4", "redundancy": "GeoRedundant"},
            {"id": sub4 + "RecoveryServices/vaults/vault-dev-lrs", "subscriptionId": "sub-synth-4", "redundancy": "LocallyRedundant"},
            {"id": base + "RecoveryServices/vaults/vault-prod-grs", "subscriptionId": "sub-synth-1", "redundancy": "GeoRedundant"},
        ],
        "cosmos_accounts": [
            {
                "id": base + "DocumentDB/databaseAccounts/cosmos-many-copies",
                "backupType": "Periodic",
                "retentionHours": 240,
                "intervalMinutes": 240,
                "multiWrite": False,
            },
            {
                "id": base + "DocumentDB/databaseAccounts/cosmos-default",
                "backupType": "Periodic",
                "retentionHours": 8,
                "intervalMinutes": 240,
                "multiWrite": False,
            },
        ],
        "synapse_workspaces": [{"id": syn + "syn-empty"}, {"id": syn + "syn-sql"}],
        "synapse_pools": [{"id": syn + "syn-sql/sqlPools/pool1", "poolType": "microsoft.synapse/workspaces/sqlpools"}],
        "azure_firewalls": [
            {"id": net + "azureFirewalls/fw-premium-idle", "skuTier": "Premium", "policyId": net + "firewallPolicies/pol-off"},
            {"id": net + "azureFirewalls/fw-premium-idps", "skuTier": "Premium", "policyId": net + "firewallPolicies/pol-alert"},
        ],
        "firewall_policies": [
            {"id": net + "firewallPolicies/pol-off", "skuTier": "Premium", "idpsMode": "Off", "tlsSecretId": None},
            {"id": net + "firewallPolicies/pol-alert", "skuTier": "Premium", "idpsMode": "Alert", "tlsSecretId": None},
        ],
    }

    # Cost governance phase 1 (hand-derived expectations are in tests/test_golden.py).
    def tres(sub, rg, i, tags):
        return {
            "id": f"/subscriptions/sub-synth-{sub}/resourceGroups/{rg}/providers/Microsoft.Storage/storageAccounts/tg{sub}x{i:02d}",
            "type": "microsoft.storage/storageaccounts",
            "subscriptionId": f"sub-synth-{sub}",
            "resourceGroup": rg,
            "tags": tags,
        }

    full = {"env": "prod", "owner": "team-a", "costcenter": "100"}
    inv = (
        [tres(1, "rg-synth", i, dict(full)) for i in range(1, 11)]  # 10 carry env, owner, costcenter
        + [tres(1, "rg-synth", i, {"Env": "Prod", "owner": "team-a"}) for i in range(11, 14)]  # capital E and capital P
        + [tres(1, "rg-synth", i, {"env": "dev"}) for i in range(14, 17)]
        + [tres(1, "rg-synth", i, None) for i in range(17, 21)]  # 4 untagged
        + [tres(2, "rg-synth", i, {"env": "dev"} if i <= 2 else None) for i in range(1, 11)]  # 8 of 10 untagged
        + [tres(3, "rg-synth", i, {"env": "dev"}) for i in range(1, 5)]  # fewer than 10 resources: not judged by TAG-COV-01
    )
    rgs = [
        {
            "id": "/subscriptions/sub-synth-1/resourceGroups/rg-synth",
            "type": "microsoft.resources/subscriptions/resourcegroups",
            "subscriptionId": "sub-synth-1",
            "name": "rg-synth",
            "tags": {"costcenter": "100", "owner": "team-a"},
        },
        {
            "id": "/subscriptions/sub-synth-2/resourceGroups/rg-synth",
            "type": "microsoft.resources/subscriptions/resourcegroups",
            "subscriptionId": "sub-synth-2",
            "name": "rg-synth",
            "tags": {"env": "dev"},
        },
        {
            "id": "/subscriptions/sub-synth-3/resourceGroups/rg-synth",
            "type": "microsoft.resources/subscriptions/resourcegroups",
            "subscriptionId": "sub-synth-3",
            "name": "rg-synth",
            "tags": None,
        },
    ]
    pa = "/subscriptions/sub-synth-1/providers/Microsoft.Authorization/policyAssignments/"
    gov = {
        "tag_inventory": inv,
        "container_tags": rgs,
        "policy_assignments": [
            {
                "id": pa + "require-env",
                "name": "require-env",
                "scope": "/subscriptions/sub-synth-1",
                "enforcementMode": "Default",
                "definitionId": "/providers/Microsoft.Authorization/policyDefinitions/871b6d14-10aa-478d-b590-94f262ecfa99",
                "parameters": {"tagName": {"value": "env"}},
            },
            {
                "id": pa + "custom-initiative",
                "name": "custom-initiative",
                "scope": "/subscriptions/sub-synth-1",
                "enforcementMode": "Default",
                "definitionId": "/providers/Microsoft.Authorization/policySetDefinitions/00000000-0000-0000-0000-000000000000",
                "parameters": None,
            },
        ],
        "policy_states": [
            {"assignmentId": (pa + "require-env").lower(), "state": "NonCompliant", "n": 15},
            {"assignmentId": (pa + "require-env").lower(), "state": "Compliant", "n": 19},
        ],
    }

    # Cost governance phase 2 (budgets, anomaly rules, exports). Rows have the shape fcat.govcost projects; no e-mail addresses exist here.
    def note(typ, enabled=True, email=True):
        return {
            "enabled": enabled,
            "operator": "GreaterThan",
            "threshold": 80,
            "thresholdType": typ,
            "hasEmail": email,
            "hasRole": False,
            "hasGroup": False,
        }

    def budget(sub, name, notes, end):
        return {
            "id": f"/subscriptions/sub-synth-{sub}/providers/Microsoft.Consumption/budgets/{name}", "subscriptionId": f"sub-synth-{sub}", "name": name,
            "level": "subscription", "amount": 5000, "category": "Cost", "timeGrain": "Monthly", "startDate": "2026-01-01T00:00:00Z",
            "endDate": end, "currentSpend": None, "notifications": notes,
        }  # fmt: skip

    def rule(sub, status):
        return {
            "id": f"/subscriptions/sub-synth-{sub}/providers/Microsoft.CostManagement/scheduledActions/anomaly", "subscriptionId": f"sub-synth-{sub}",
            "name": "anomaly", "kind": "InsightAlert", "status": status, "viewId": None, "frequency": "Daily", "endDate": None, "hasRecipient": True,
        }  # fmt: skip

    gov2 = {
        "budgets": [
            budget(1, "b-main", [note("Actual"), note("Forecasted")], "2027-12-31T00:00:00Z"),
            budget(1, "b-old", [note("Actual", email=False)], "2026-06-30T00:00:00Z"),  # ended, and its notification names nobody
            budget(2, "b-actual-only", [note("Actual")], None),
        ],
        "anomaly_rules": [rule(1, "Enabled"), rule(3, "Disabled")],
        "cost_exports": [
            {
                "id": "/subscriptions/sub-synth-1/providers/Microsoft.CostManagement/exports/daily-actual",
                "subscriptionId": "sub-synth-1",
                "name": "daily-actual",
                "exportType": "ActualCost",
                "format": "Csv",
                "hasSchedule": True,
                "scheduleStatus": "Active",
                "recurrence": "Daily",
                "runHistoryReturned": True,
                "lastRunStatus": "Failed",
                "lastRunEnd": "2026-09-30T00:00:00Z",
                "lastRunErrorCode": None,
            }
        ],
    }
    batch7 = {  # 2026-10-21, backlog 35: non-production and housekeeping checks
        "availability_sets": [
            {"id": base + "Compute/availabilitySets/as-empty", "skuName": "Aligned", "vmCount": 0},
            {"id": base + "Compute/availabilitySets/as-used", "skuName": "Aligned", "vmCount": 2},
        ],
        "devtest_schedules": [
            {
                "id": sub4 + "DevTestLab/schedules/shutdown-computevm-vm-dev-ok",
                "taskType": "ComputeVmShutdownTask",
                "status": "Enabled",
                "targetResourceId": (sub4 + "Compute/virtualMachines/vm-dev-ok").lower(),
            }
        ],
        "storage_lifecycle": [
            {"id": base + "Storage/storageAccounts/stv2/managementPolicies/default", "ruleCount": 2},
        ],
    }
    vms += [
        {
            "id": sub4 + "Compute/virtualMachines/vm-dev-ok",
            "subscriptionId": "sub-synth-4",
            "vmSize": "Standard_B2s",
            "powerState": "PowerState/running",
        },
        {
            "id": sub4 + "Compute/virtualMachines/vm-dev-noshut",
            "subscriptionId": "sub-synth-4",
            "vmSize": "Standard_D2s_v5",
            "powerState": "PowerState/running",
        },
    ]
    return {
        **batch7,
        **gov,
        **gov2,
        **batch6,
        **batch5,
        **batch4,
        **batch3,
        **tier_a,
        "vms": vms,
        "subscriptions": subs,
        "management_groups": mgs,
        "unattached_disks": disks,
        "public_ips": pips,
        "nics": nics,
        "nsgs": nsgs,
        "app_service_plans": asps,
    }


def write_snapshot():
    SNAP.mkdir(parents=True, exist_ok=True)
    (SNAP / "_meta.json").write_text(json.dumps({"collected_at": "2026-10-01T00:00:00Z"}, indent=1))
    rest = {"budgets", "anomaly_rules", "cost_exports"}  # REST collectors: rows plus a per-subscription 'scopes' list (fcat.govcost)
    for name, rows in estate().items():
        body = {"rows": rows, "total_records": len(rows), "pages": 1, "warnings": []}
        if name in rest:
            body["scopes"] = [{"subscriptionId": f"sub-synth-{i}", "status": "ok"} for i in (1, 2, 3)]
            body["api_version"] = "2026-06-01"
        (SNAP / f"{name}.json").write_text(json.dumps(body, indent=1, sort_keys=True))


def normalised_report(workdir):
    """Run the offline analysis on the synthetic snapshot and strip fields that legitimately change run to run."""
    sys.path.insert(0, str(ROOT / "src"))
    from fcat import cli

    out = pathlib.Path(workdir) / "out"
    shutil.copytree(SNAP, out / "snapshot")
    cfg = pathlib.Path(workdir) / "c.toml"
    cfg.write_text('[run]\nprofile="standard"\n')
    rc = cli.main(["analyze", "--config", str(cfg), "--out", str(out)])
    doc = json.loads((out / "report.json").read_text())
    m = doc["manifest"]
    for k in ("started", "ended", "git_commit", "tool_version", "runtime"):
        m.pop(k, None)
    return rc, doc


if __name__ == "__main__":
    write_snapshot()
    if "--approve" in sys.argv:
        with tempfile.TemporaryDirectory() as tmp:
            rc, doc = normalised_report(tmp)
        GOLDEN.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
        print(f"golden report rewritten (exit code of analysis: {rc}). Review the git diff before committing.")
