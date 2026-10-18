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
        },
        {"id": base + "Compute/virtualMachines/vm-dealloc", "vmSize": "Standard_D4s_v5", "powerState": "PowerState/deallocated"},
        {"id": base + "Compute/virtualMachines/vm-run", "vmSize": "Standard_B2s", "powerState": "PowerState/running"},
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
    return {
        **batch3,
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
    for name, rows in estate().items():
        (SNAP / f"{name}.json").write_text(
            json.dumps({"rows": rows, "total_records": len(rows), "pages": 1, "warnings": []}, indent=1, sort_keys=True)
        )


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
    for k in ("started", "ended", "git_commit", "tool_version"):
        m.pop(k, None)
    return rc, doc


if __name__ == "__main__":
    write_snapshot()
    if "--approve" in sys.argv:
        with tempfile.TemporaryDirectory() as tmp:
            rc, doc = normalised_report(tmp)
        GOLDEN.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
        print(f"golden report rewritten (exit code of analysis: {rc}). Review the git diff before committing.")
