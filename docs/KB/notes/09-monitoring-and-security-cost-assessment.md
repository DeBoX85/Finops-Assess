# 09. Monitoring and security cost assessment (Sentinel, Defender, App Insights, Log Analytics)
Date: 17 Oct 2026. Status words: VERIFIED = read on Microsoft Learn this session. PROPOSAL = my design, not a source claim. UNVERIFIED = not checked.

## 1. Verified facts (Microsoft Learn)

### Log Analytics
- Commitment tiers apply to Analytics Logs only. Basic and Auxiliary ingestion are flat per-GB. Up to 30% saving vs pay-as-you-go, start at 100 GB/day, 31-day commitment, can be lowered only within 6 hours of configuring, overage billed at the tier rate. https://learn.microsoft.com/azure/azure-monitor/logs/cost-logs#commitment-tiers
- Dedicated cluster: use when ingestion reaches at least 100 GB/day, and it lets several workspaces in one region pool volume to reach a tier. https://learn.microsoft.com/azure/azure-monitor/logs/workspace-design
- Linux Log Analytics agent can only report to one workspace; Azure Monitor Agent can report to several (duplicate ingestion risk when separate Sentinel and operational workspaces both receive the same data). Same page.
- If Sentinel is enabled, all data in that workspace is subject to Sentinel pricing, so mixing operational and security data has a cost effect. https://learn.microsoft.com/azure/azure-monitor/fundamentals/best-practices-cost
- Daily cap is a preventative control, not a cost-reduction method; Learn advises an alert at about 90% of the cap. Same page.
- Usage table: IsBillable, Quantity (MB), DataType, Solution. A Plan column was added mid-May 2026; older rows lack it. Per-record: _IsBillable, _BilledSize, _ResourceId. `find` queries are expensive, restrict to one day. https://learn.microsoft.com/azure/azure-monitor/logs/analyze-usage
- Advisor emits 4 Log Analytics cost recommendations: ingestion anomaly (Medium), Basic logs candidate for tables over 1 GB/month (Low), change pricing tier (Medium), remove unused restored tables (Low). https://learn.microsoft.com/azure/advisor/advisor-reference-cost-recommendations#azure-monitor
- Pricing tier changes appear in the Activity Log as "Create Workspace" with properties.sku.name in the change history. https://learn.microsoft.com/azure/azure-monitor/logs/change-pricing-tier
- ARM workspace properties (api 2023-09-01): sku.name (CapacityReservation, Free, LACluster, PerGB2018, PerNode, Premium, Standalone, Standard), sku.capacityReservationLevel, retentionInDays, workspaceCapping.dailyQuotaGb, features.clusterResourceId, defaultDataCollectionRuleResourceId. https://learn.microsoft.com/azure/templates/microsoft.operationalinsights/2023-09-01/workspaces
  - Caution: the 2020 doc says max retention 730 days; newer versions say "allowed values per pricing plan". The 12-year total retention in my earlier summary comes from other Learn pages and the retention ceiling for the property itself is UNVERIFIED here.

### Application Insights
- Workspace-based resources store data in Log Analytics tables (AppRequests, AppDependencies, AppTraces, etc.), so their cost is visible through workspace _BilledSize by _ResourceId. Classic resources also expose systemEvents billing records. https://learn.microsoft.com/azure/azure-monitor/logs/analyze-usage
- Earlier in the session (Learn): daily caps on App Insights and on the workspace are separate and the lower one wins; sampling detection query exists. Not re-fetched in this batch.

### Sentinel
- Azure portal support ends 31 Mar 2027; Defender portal only after that. https://learn.microsoft.com/azure/sentinel/billing-monitor-costs
- Data lake tier has its own meters; the Defender portal Cost management view is in preview. Security Reader can view; Billing Administrator or Security Administrator can set limits. Enforcement covers Data Lake Query and Advanced Data Insights only and can lag up to 4 hours. Same page.
- Usage by solution/data type KQL is documented; ingestion alert playbook Send-IngestionCostAlert is community content in Azure/Azure-Sentinel (not Microsoft-supported, treat as reference only).
- Earlier in the session: analytics tier pay-as-you-go and commitment tiers, data lake meters, graph meter (https://learn.microsoft.com/azure/sentinel/billing).

### Defender for Cloud
- ARG table SecurityResources, type microsoft.security/pricings gives pricingTier per plan per subscription. https://learn.microsoft.com/azure/defender-for-cloud/resource-graph-samples
- pricings API: pricingTier Free/Standard, subPlan (VirtualMachines: P1 or P2; resource-level supports P1 only), enforce flag (2024-01-01), latest 2025-10-01-preview. https://learn.microsoft.com/azure/templates/microsoft.security/pricings
- Storage plan has subPlan PerTransaction (classic) vs newer per-storage-account model. https://learn.microsoft.com/azure/defender-for-cloud/defender-for-storage-classic-enable
- Plan prices, pre-purchase plan and billing details: from earlier session pages, not re-fetched.

### FinOps naming
- Learn path for the capability is /cloud-computing/finops/framework/optimize/workloads (titled "Workload optimization"); finops.org 2026 name is "Usage Optimization". The URL guessed in the user's list failed because of the wrong path.

## 2. User-supplied sources: reliability
| Source | Rating | Why |
|---|---|---|
| learn.microsoft.com pages | High | Vendor docs, dated |
| Foundry blog 4466810, several techcommunity posts | Unusable | Only metadata returned, no body read |
| jeffreyappel.nl, modernsecurity.nl, mindbyte.nl | Medium, third party | Read, but each claim needs Learn confirmation before use; used only to suggest checks |
| dolevshor/azure-finops-guide | UNVERIFIED | Community repo, licence and accuracy not checked |
| finops-toolkit alerts page | Medium | Vendor project page, not a billing source of truth |

## 3. Check catalogue (PROPOSAL)
Columns: ID, check, data source, minimum permission, billing applicability, confidence, savings basis.

| ID | Check | Source | Permission | Billing | Confidence | Savings |
|---|---|---|---|---|---|---|
| LA-01 | Workspace on PerGB2018 with 30-day average ingestion above 100 GB/day | ARM workspace + Usage via query API | Reader + Log Analytics Reader | All | High on data, estimate on discount (up to 30% per Learn) | Actual cost x tier rate difference, list price shown separately |
| LA-02 | Commitment tier set above actual ingestion (paying for unused commit) | ARM sku + Usage | same | All | High | Actual |
| LA-03 | Several small workspaces in one region that could pool in a dedicated cluster | ARM + Usage | same | All | Medium (cluster minimum is 100 GB/day) | Estimate |
| LA-04 | Tables eligible for Basic/Auxiliary plan with high volume | Tables API + Usage Plan column | same | All | Medium (eligibility and query needs are a human call) | Estimate |
| LA-05 | Restored tables left active | Advisor / Tables API | Reader | All | High | Actual |
| LA-06 | Retention above need or archive misuse | ARM retentionInDays + table retention | Reader | All | Medium (compliance may require it) | Estimate |
| LA-07 | No daily cap and no ingestion alert, or cap set and hit (data loss risk) | ARM workspaceCapping + alert rules | Reader | All | High | Risk, not savings |
| LA-08 | Duplicate ingestion to two workspaces from the same machines | DCR associations + Heartbeat | Reader + LA Reader | All | Low to medium | Estimate |
| LA-09 | Ingestion anomaly week over week | Usage | LA Reader | All | High | Not a saving |
| AI-01 | App Insights classic resources (not workspace-based) | ARG | Reader | All | High | Not a saving, migration item |
| AI-02 | High dependency/trace volume without sampling | AppDependencies _BilledSize, itemCount | LA Reader | All | Medium | Estimate |
| AI-03 | Per-resource cap vs workspace cap conflict | ARM + App Insights billing props | Reader | All | Medium | Risk |
| AI-04 | App Insights resources with no data in 30 days | Workspace query | LA Reader | All | Medium | Actual (often small) |
| DC-01 | Defender plans enabled with no matching resources | SecurityResources pricings + ARG inventory | Reader / Security Reader | All | High | Actual from cost data |
| DC-02 | Servers P2 where P1 may suffice | pricings + inventory | Security Reader | All | Medium (feature need is a human call) | Estimate |
| DC-03 | Plan enabled on dev/test subscriptions | pricings + tags/subscription type | Reader | All | Medium | Actual |
| DC-04 | Defender for Storage on high-transaction accounts under the classic per-transaction model | pricings + metrics | Reader | All | Medium | Estimate |
| DC-05 | Data ingestion benefit not used where eligible | Not verified | n/a | n/a | UNVERIFIED | n/a |
| SE-01 | Sentinel workspace ingesting non-security tables | Usage by Solution/DataType | LA Reader | All | Medium | Estimate |
| SE-02 | Analytics-tier tables suited to data lake tier | Tables + Usage | LA Reader, Security Reader | All | Medium | Estimate |
| SE-03 | Sentinel pay-as-you-go vs commitment tier | ARM + Usage | same | All | High | Estimate |
| SE-04 | No cost alerts/limits on data lake meters | Not available via read-only API as far as verified | n/a | n/a | UNVERIFIED | n/a |
| SE-05 | Azure portal retirement (31 Mar 2027) readiness | Learn statement | n/a | n/a | High | Not a saving |
| XF-01 | Foundry playground evaluations on by default (billed) | Settings, per earlier Learn page | Reader | All | Medium | Estimate |

Open questions for the user are in README.

## 4. Correction (17 Oct 2026): is Reader enough for workspace queries?
VERIFIED on https://learn.microsoft.com/azure/azure-monitor/logs/manage-access :
- Querying a workspace needs Microsoft.OperationalInsights/workspaces/query/read.
- The Log Analytics Reader role's grant is `*/read`; Learn describes this as allowing, for workspaces, reading settings and querying data. The built-in Reader role also contains `*/read`, and Learn's custom-role Example 4 says a user inheriting `*/read` from Reader or Contributor can read all log types.
- So Reader at subscription scope very likely covers the Usage-table queries. My earlier "Reader + Log Analytics Reader" in the check catalogue (LA-xx, AI-xx, SE-xx) was stricter than needed.
NOT VERIFIED (must test on a real tenant): (a) whether tenants using granular RBAC (role assignment conditions, DataAction workspaces/tables/data/read) or protected tables block Reader; (b) whether a Usage-only custom role via the legacy per-table action query/Usage/read works; (c) behaviour for resource-context access mode.
Privacy note: any role that can query can read all log content (for example SecurityEvent), not just Usage. The tool would only run aggregate Usage/_BilledSize queries, but the permission granted is broader than the tool's use.
Without query access: ARM properties (sku, retention, cap), Advisor and Cost Management still work. The Azure Monitor workspace metric "Ingestion Volume" is a record count, not GB, so it cannot replace Usage for billable volume (https://learn.microsoft.com/azure/azure-monitor/reference/supported-metrics/microsoft-operationalinsights-workspaces-metrics).
