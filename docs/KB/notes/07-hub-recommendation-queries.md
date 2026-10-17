# FinOps hubs recommendation queries: inventory (17 Oct 2026)

Source: microsoft/finops-toolkit (MIT, Copyright Microsoft Corporation), copied from the shallow clone of branch dev, commit f12c29e. Attribution is required if reused. Correction: there are 23 query files, not 22 as noted earlier in the session.

All use queryEngine ResourceGraph, scope Tenant, dataset Recommendations, version 1.0. Output columns follow the hub Recommendations schema (x_RecommendationId, x_RecommendationCategory, x_RecommendationDescription, ResourceId, x_RecommendationDetails with x_RecommendationSolution and x_RecommendationTypeId, x_RecommendationDate).

| Type | Description (from query) | Solution (from query) | TypeId |
|---|---|---|---|
| Microsoft-AdvisorCost | n/a (not matched) | n/a | n/a |
| Microsoft-BackendlessAppGateways | Application Gateway without any backend pool | Review and remove this resource if not needed | 4f69df93-5972-44e0-97cf-4343c2bcf4b8 |
| Microsoft-BackendlessLoadBalancers | Load balancer without a backend pool | Review and remove this resource if not needed | ab703887-fa23-4915-abdc-3defbea89f7a |
| Microsoft-BasicLoadBalancers | Load balancer is using the retired Basic SKU | Upgrade to Standard SKU load balancer | a2b3c4d5-e6f7-8a9b-0c1d-2e3f4a5b6c7d |
| Microsoft-BasicPublicIPs | Public IP is using the retired Basic SKU | Upgrade to Standard SKU public IP | f1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c |
| Microsoft-ClassicAppGateways | Application Gateway is using the retiring v1 SKU | Migrate to Application Gateway v2 (Standard_v2 or WAF_v2) | b3c4d5e6-f7a8-9b0c-1d2e-3f4a5b6c7d8e |
| Microsoft-EmptyAppServicePlans | App Service plan has no apps hosted on it | Delete the empty App Service plan or deploy apps to it | d7b1c874-5e1a-4e3b-9f0a-1c2d3e4f5a6b |
| Microsoft-EmptyNSGs | Network security group is not associated with any network interface or subnet | Delete the orphaned network security group or associate it with a subnet or NIC | b9c0d1e2-f3a4-5b6c-7d8e-9f0a1b2c3d4e |
| Microsoft-EmptySQLElasticPools | SQL Database elastic pool has no associated databases | Review and remove this resource if not needed | 50987aae-a46d-49ae-bd41-a670a4dd18bd |
| Microsoft-IdleVNetGateways | Virtual network gateway has no connections | Delete the idle virtual network gateway or add connections | a3b4c5d6-7e8f-9a0b-1c2d-3e4f5a6b7c8d |
| Microsoft-LegacyStorageAccounts | Storage account is using a legacy kind that is being retired | Upgrade to General Purpose v2 (StorageV2) storage account | c4d5e6f7-a8b9-0c1d-2e3f-4a5b6c7d8e9f |
| Microsoft-NonSpotAKSClusters | The AKS cluster agent pool scale set is not utilizing Spot VMs | Consider enabling Spot VMs for this AKS cluster to optimize costs, as Spot VMs offer significantly lower pricing compared to regular VMs | c26abcc2-d5e6-4654-be4a-7d338e5c1e5f |
| Microsoft-OrphanedNATGateways | NAT gateway is not associated with any subnet | Delete the orphaned NAT gateway or associate it with a subnet | b4c5d6e7-8f9a-0b1c-2d3e-4f5a6b7c8d9e |
| Microsoft-PremiumSnapshots | Snapshot is using Premium SSD storage instead of Standard | Change snapshot storage type from Premium SSD to Standard HDD | e7f8a9b0-1c2d-3e4f-5a6b-7c8d9e0f1a2b |
| Microsoft-SQLVMsWithoutAHB | SQL virtual machine is not leveraging Azure Hybrid Benefit | Review the SQL licensing option | 01decd62-f91b-4434-abe5-9a09e13e018f |
| Microsoft-StoppedVMs | Virtual machine is powered off but not deallocated | Deallocate the virtual machine to ensure it does not incur in compute costs | ab2ff882-e927-4093-9d11-631be0219975 |
| Microsoft-UnassociatedDDoSPlans | DDoS protection plan is not associated with any virtual network | Delete the DDoS protection plan or associate it with virtual networks | c5d6e7f8-9a0b-1c2d-3e4f-5a6b7c8d9e0f |
| Microsoft-UnattachedDisks | Unattached (orphaned) disk is incurring in storage costs | Remove or downgrade the unattached disk | e0c02939-ce02-4f9d-881f-8067ae7ec90f |
| Microsoft-UnattachedNICs | Network interface is not attached to any virtual machine or private endpoint | Delete the orphaned network interface | a8b9c0d1-e2f3-4a5b-6c7d-8e9f0a1b2c3d |
| Microsoft-UnattachedPublicIPs | Unattached (orphaned) public IP | Review and remove this resource if not needed | 3ecbf770-9404-4504-a450-cc198e8b2a7d |
| Microsoft-UnmanagedDisks | Virtual machine is using unmanaged disks that are being retired | Migrate to managed disks | d5e6f7a8-b9c0-1d2e-3f4a-5b6c7d8e9f0a |
| Microsoft-UnprovisionedExpressRouteCircuits | ExpressRoute circuit is not in provisioned state | Complete provisioning or delete the ExpressRoute circuit | d6e7f8a9-0b1c-2d3e-4f5a-6b7c8d9e0f1a |
| Microsoft-VMsWithoutAHB | Windows virtual machine is not leveraging Azure Hybrid Benefit | Review the virtual machine licensing option | f326c065-b9f7-4a0e-a0f1-5a1c060bc25d |

Notes
- Rows marked n/a use a different query shape (for example AdvisorCost passes Advisor fields through); read the JSON.
- Hand-made-looking TypeIds (sequential hex patterns) were seen; SPECULATION that some IDs were assigned manually. Do not treat them as globally stable identifiers.
- Queries use `join kind=leftouter` to attach SubAccountName, consistent with the ARG join rule in note 03.
- Predicates have NOT been re-tested against a live tenant. Do that before reuse.
## Count reconciled (17 Oct 2026)
Source: docs-mslearn/toolkit/hubs/configure-recommendations.md (repo copy of Learn page) and the queries folder src/templates/finops-hub/modules/Microsoft.FinOpsHubs/Recommendations/queries (23 files).
Counting the Learn list: Compute 2 default (stopped VMs, unmanaged disks), SQL 1, Advisor 1, Networking 12 (App Gateway 2, DDoS 1, ExpressRoute 1, Load Balancer 2, NAT 1, NIC 1, NSG 1, Public IP 2, VPN gateway 1), Storage 3, Web 1 = 20 default. Optional 3: AHB Windows VMs and AHB SQL VMs (enableAHBRecommendations), AKS Spot (enableSpotRecommendations). 20 + 3 = 23, matching the 23 files.
A separate research report said 22 queries (19 default, 3 optional); that is off by one default query by this count.
Note: the whole Recommendations feature is disabled unless enableRecommendations=true.
