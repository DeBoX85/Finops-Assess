# FinOps toolkit workbooks: verified inventory from source

Verified 17 Oct 2026 by cloning https://github.com/microsoft/finops-toolkit (branch dev, shallow) and parsing the workbook JSON. Commit read: f12c29e (2026-10-15, "[Power BI] Fix SkuMeterName column error in storage reports for FOCUS 1.2 exports (#2333)"). Source version file `src/workbooks/.scaffold/ftkver.txt` reads `15.0-dev`.

Raw extraction: `sources/workbook-queries-raw.json` (467 query/parameter rows across 15 workbook files). Extraction script is not part of the repo; query type codes seen: 1 = Azure Resource Graph, 0 = Log Analytics, 12 = ARM/REST endpoint, 7 = merge of other result tables, 2 = parameters.

## What the Learn and site pages say (OPENED)
- Learn overview (ms.date 2025-04-02, updated 2026-02-11): two workbooks, Optimization and Governance.
- Site workbooks page: version v14 (April 2026). v14 changes: Optimization feedback link fixed, dev/test subscriptions excluded from AHB reports, AHB reports now include Windows VMs from all publishers. "Do not incur any cost."
- Deployment needs Contributor (ARM template), Workbook Contributor to save, Reader on each monitored subscription. Reader-only import of the JSON works but cannot be saved.
- The Learn Optimization page names only two areas (rate optimization, usage optimization) and has no per-check list. The real detail is only in the source.

## Source layout (src/workbooks)
- governance/ (single workbook.json)
- optimization/ with module workbooks: CostOptimization (overview), AHB, Compute (with its own AHB.workbook), Storage, Databases, Networking, Top10Services, Sustainability, commitment-discounts, Reservations, Reservations Preview, SavingsPlan. Compiled into optimization/workbook.json.
- CORRECTION to the earlier research report: it listed "Databases and Sustainability tabs" as unverified. Both exist in source (Databases: 5 queries; Sustainability: 1 query).

## Optimization workbook modules and checks

### CostOptimization (overview)
Advisor security recommendations, Advisor reliability recommendations, resource distribution per region. (ARG)

### Compute
- VMs in a stopped (not deallocated) state: powerState != 'VM deallocated' and != 'VM running'. (ARG, uses properties.extended.instanceView.powerState)
- VMs in deallocated state, processor type per VM, VM list per processor type, Advisor cost recommendations for compute.
- Quick fix links exist for some rows (Advisor/portal), which we will NOT replicate (read-only).

### AHB (Azure Hybrid Benefit); present both as AHB/AHB.workbook and Compute/AHB.workbook
- Windows VMs with/without AHB (summary per subscription), consumed cores per AHB priority, cores not enabled, total cores enabled last 7 days.
- Linux VMs (RHEL/SLES) with/without AHB, VMSS with/without AHB, custom image AHB (AHB/AHB.workbook only), Coverage Summary, Eligible resources, Eligible licenses (AHB/AHB.workbook only).
- SQL VM, SQL DB, SQL elastic pool, SQL Managed Instance AHB enabled/disabled with consumed cores.
- Needs ARM call `Microsoft.Compute/skus` (queryType 12, "Get VM vCPU") to map VM size to vCPU. So AHB core counting needs a REST call, not ARG alone.

### Storage
- Idle backups: protected items with lastBackupTime older than 90 days (ARG recoveryservicesresources).
- Recovery vault storage replication (GRS vs LRS).
- Storage accounts not v2.
- Unattached disks: managedBy empty and diskState != ActiveSAS, excluding tags kubernetes.io-created-for-pvc, ASR-ReplicaDisk, asrseeddisk, RSVaultBackup.
- Disk last modified date: ARM call to resources with $expand=createdTime,changedTime (api-version 2021-04-01).
- Premium disks attached to powered-off VMs.
- Snapshots older than 30 days (timeCreated < ago(30d)), snapshots on premium storage, snapshots whose source disk was deleted (leftanti merge), all snapshots, all managed disks.

### Networking
- App Gateways with empty backend pools; Load Balancers with empty backend pools.
- Unattached public IPs; public IP list; public IPs with DDoS protection.
- Idle VNet gateways: no connection references the gateway.
- Idle NAT gateways; idle private DNS zones (0 VNet links); idle private endpoints (connection state Disconnected); idle ExpressRoute circuits.
- Azure Firewall Premium (check for unused premium features) and firewalls per location.

### Databases
- Cosmos DB: collections whose RU/s could be reduced; collections that would benefit from another throughput mode; accounts likely cheaper under continuous backup mode. These three are Advisor recommendations read through ARG advisorresources (e.g. recommendationTypeId 8b993855-1b3f-4392-8860-6ed4f5afd8a7), with Advisor's own annual-savings values.
- "Databases idle for over 30 days": FINDING, the query only matches SQL database names containing "old", "Dev" or "test". It does NOT measure activity. The title overstates what it checks.
- Idle SQL pool (Synapse).

### Top10Services
- Unused Synapse workspaces; all AKS clusters; web and function app status; App Service plan details; idle App Service plans (numberOfSites == 0) joined with autoscale settings.
- Log Analytics workspaces and 30-day billable ingestion trend from the workspace `Usage` table (IsBillable == true). This is the only Optimization query that needs Log Analytics data access (queryType 0).
- Advisor cost recommendations for monitoring.

### Sustainability
One query for Advisor carbon-savings recommendations (shows "There aren't any Carbon Savings recommendations" when empty).

### Commitments: Reservations, SavingsPlan, commitment-discounts
- CORRECTION to the earlier research: the "Reservation and savings plan recommendations" in Reservations.workbook and SavingsPlan.workbook come from Azure Advisor via ARG (`advisorresources`, category Cost, shortDescription contains "Reserved Instance" or "savings plan", filtered by lookbackPeriod and term). Reader is enough. Suppressions are joined and excluded.
- Reservations Summary and details, Savings plan Summary and details: same Advisor route.
- commitment-discounts/commitment.workbook and "Reservations Preview": use the Billing REST API (`/providers/Microsoft.Billing/billingAccounts/{id}/billingProfiles/...`, api-version 2019-10-01-preview for the account lists) for reservation recommendations at billing account/profile scope, EA and MCA variants merged. This path needs billing-scope permissions. "Total commitment-based savings" for 1 and 3 years.
- Note: the 2019-10-01-preview Billing api-version is old. Check it still works before reuse. (Not tested.)

## Governance workbook (single file, 66 distinct query titles)
- Inventory: counts of all resources, per subscription (top 10), by type, by location; VMs by OS type and size; VMSS capacity; compute disks; compute networking; managed disks; NICs; resource details.
- Utilisation hints: "Underused assets" (Advisor), "Managed disks free space" (Log Analytics InsightsMetrics, needs VM insights data).
- Power state: VM state chart, VM list by power state.
- Networking: counts by type, NSGs, NSG rules, public IPs, App Gateways, Load Balancers.
- Change and health: active Service Health events, changes in the past day, resources deleted, resource age (ARM createdTime/changedTime), resource status.
- Tags: resources with a tag, tag with empty value, untagged resources.
- Cost: "Overall cost" and "Overall cost filtered by tag" call the Cost Management Query API through an ARM endpoint (type 12).
- Security: secure scores by subscription and control, alerts (Defender), top attacked resources, governance rules and status per rule/owner, recommendations.
- Compliance: resource compliance (Policy). Failures by resource/operation/category from the Activity Log (AzureActivity table in Log Analytics, needs diagnostics sent to a workspace).
- Limits: compute, network, storage account quota/limits via ARM REST (`/providers/microsoft.compute/locations/{loc}/usages` style).
- Jobs by status / list of jobs (Log Analytics, Automation-type data).
- Needs Log Analytics: managed disk free space, activity failures, jobs. Everything else is ARG or ARM REST.

## Gaps and lessons for our tool
1. Most orphan/idle checks are simple ARG predicates with no cost or age scoring. We add: age, estimated monthly cost (actual and list price), confidence, and exclusions (the Unattached disks tag exclusions are worth copying).
2. Some checks are heuristics with misleading titles (idle SQL by name pattern). Do not copy blindly. Mark confidence Low or replace with Azure Monitor metric tests.
3. Commitment recommendations: Advisor via ARG is the least-privilege route. The Billing API route adds EA/MCA billing-scope detail.
4. Only three Optimization/Governance data needs go beyond ARG and ARM REST: Log Analytics (ingestion trend, disk free space, activity failures), Cost Management Query, Billing API.
5. The workbook queries are MIT-licensed (repo LICENSE not yet re-read; site footer says MIT). Reuse needs attribution. TODO confirm LICENSE text.
6. The workbooks use portal-side "{TagName}"/"{TagValue}"/"{ResourceGroup}" parameter placeholders that must be stripped when porting queries to a CLI.

## Sources
- https://github.com/microsoft/finops-toolkit (cloned; commit f12c29e)
- https://learn.microsoft.com/en-us/cloud-computing/finops/toolkit/workbooks/finops-workbooks-overview
- https://microsoft.github.io/finops-toolkit/workbooks
- https://learn.microsoft.com/en-ie/cloud-computing/finops/toolkit/workbooks/optimization
- The GitHub web URL https://github.com/microsoft/finops-toolkit/tree/dev/src/workbooks could not be fetched by the web tool (robots disallowed). It is not dead; the same files were read from the clone.
