# KB 12: Microsoft Sentinel cost optimisation and FinOps

Status: research note, read 2026-10-21. Nothing built. Tags: VERIFIED = read on Microsoft Learn on the date shown;
UNVERIFIED = recalled or inferred, must be checked before use. Third-party blogs returned by search were NOT opened
and are not used as evidence.

## 1. What drives Sentinel cost (VERIFIED, Learn, 2026-10-21)

Sources: billing-reduce-costs, billing-monitor-costs, log-plans (all under https://learn.microsoft.com/azure/sentinel/).

- Sentinel analyses every table in a Sentinel-enabled Log Analytics workspace, so all data in that workspace bears
  Sentinel cost. Microsoft advises a separate workspace for non-security operations data.
- Analytics tier: pay-as-you-go or commitment tiers. Increasing a tier restarts a 31-day commitment; moving down or back
  to pay-as-you-go is only possible after the 31 days. Billing is daily.
- Classic pricing: Sentinel tiers do not include Log Analytics charges, so those bill separately. Simplified pricing
  combines both into one tier.
- Pre-purchase plan: commit units (CUs), one-year term, auto-applied to eligible Sentinel cost, no assignment needed.
- Dedicated cluster: worth considering at 100 GB/day or more combined in one region; commitment floor of 100 GB/day;
  max two clusters per region and subscription; workspaces must share the region.
- Retention: analytics retention 90 days by default; longer "total retention" is cheaper and reachable through the
  data lake tier.
- Data lake tier: for secondary security data. Own meters, billed after onboarding.
- Windows Security Events via AMA and data collection rules: filter at source to cut volume.
- Changing the pricing tier needs Contributor or Owner on the workspace.
- Portal timeline: after 2027-03-31 Sentinel is supported only in the Defender portal.

## 2. Where the cost shows up (VERIFIED, billing-monitor-costs, 2026-10-21)

- Cost Management: filter service name Sentinel, Log Analytics, Azure Monitor. Analytics tier ingestion can appear under
  "Security Insights" in some usage charts.
- Ingestion by table or solution comes from the workspace `Usage` table (IsBillable, Quantity, DataType, Solution;
  Solution "SecurityInsights" is displayed as "AzureSentinel"). This is a Log Analytics query, so it needs ADR 0007.
- Data lake cost management view is in the Defender portal (preview), Security Reader for read. Whether the same usage is
  exposed by a REST API: DON'T KNOW.
- Microsoft recommends cost exports as the way to retrieve cost datasets.

## 3. What a read-only identity can see

| Item | Surface | Status |
|---|---|---|
| Workspace SKU, capacityReservationLevel, retentionInDays, workspaceCapping, clusterResourceId | ARM / ARG on `Microsoft.OperationalInsights/workspaces` | VERIFIED as properties (template reference, 2026-10-21). Already used by MON-LAWCAP-01. |
| Role scope | Microsoft Sentinel Reader = `Microsoft.SecurityInsights/*/read` plus `OperationalInsights/workspaces/*/read` and `query/read` | VERIFIED (built-in roles, Security, 2026-10-21) |
| Generic Reader reaches every SecurityInsights read and log query | | UNVERIFIED. Learn lists Reader among roles with workspace read, but the exact action coverage was not checked. Test on a real tenant. |
| Sentinel enabled on a workspace | SecurityInsights solution resource, or `onboardingStates` | PARTLY VERIFIED: onboardingStates exists (template 2025-10-01-preview). ARG detection by solution resource type is UNVERIFIED. |
| Data connectors | `Microsoft.SecurityInsights/dataConnectors` (GET list) | VERIFIED type exists, api-version 2025-03-01 and previews. Connector state per data type is readable; ingestion volume is not in this object. |
| SOC optimization recommendations | `GET .../Microsoft.SecurityInsights/recommendations?api-version=2024-01-01-preview` | VERIFIED, PREVIEW. Computed every 24 h. Data value types: table unused by analytics rules in 30 days, table unused at all, table only used by Azure Monitor, unused columns (preview). Only billable tables with ingestion in the last 30 days. |
| Re-evaluate or dismiss a recommendation | POST triggerEvaluation, PATCH | VERIFIED. Both WRITE. The tool must never call them. |
| Table plan (analytics vs data lake), per-table retention | Tables API / Defender portal | UNVERIFIED which endpoint and api-version. Not checked this session. |
| Analytics rules list | `alertRules` GET | Rule queries contain customer logic and possibly names. Reading them needs the same privacy handling as ADR 0009. UNVERIFIED that this is needed if SOC optimization is used instead. |

## 4. Limits of any automated assessment

- Whether a table is "valuable" is a security judgement. Learn itself warns to confirm a table is not ingested for
  compliance before changing its plan (soc-optimization-reference). The tool may flag for review, never say "remove".
- Actual versus list price needs cost data (ADR 0006) and, for EA/MCA discounts, the price sheet. Sentinel savings claims
  without it would be list-price estimates only, and must be labelled so (owner constraint).
- Data lake meters and Defender-portal-only settings: coverage unknown.
- The Defender portal onboarding state and "primary workspace" are tenant-level and live outside ARM as far as verified.

## 5. Not used as evidence

Charbel Nemnom, Decryption Digest, CyberOne, VirtualMetric, North Peak Cloud, Ciphers Security, Reveal Compliance blog
results from search were not opened. Treat as leads only.

## 6. Round 2 (2026-10-21): owner sources, GitHub projects, first party

Owner direction: goal is "cost proof" for customers, both internal and customer-facing use, multi-tenant allowed but
scoped, cost optimisation without losing monitoring coverage, plus an inventory of "what is being stored and watched"
for customers who lost control. SOC effectiveness is a nice to have.

### 6.1 Owner-listed sources: what could and could not be read
- NOT READ (fetch failed or robots disallowed): both charbelnemnom.com articles, both LinkedIn articles (Sami Lamppu,
  the 4662 DCR case), the techcommunity cost estimator link (returned an unrelated Teams forum post), What's New.
  Claims attributed to them in the owner's table (6:1 compression, $5K/month saving) are UNVERIFIED by me.
- Read, low authority: securesky blog (claims "up to 60%", no method, no sources: do not cite as evidence);
  underdefense pricing page (vendor, internally consistent, publish and read dates disagree, list prices only:
  UNVERIFIED against the Retail Prices API); Microsoft Q&A 5548004 (generic compute cost thread, not about Sentinel).
- Read, first party: billing-monitor-costs, soc-optimization-api, log-plans, billing-reduce-costs (see sections 1-3).

### 6.2 Similar projects (read via WebFetch summaries and search; repo metadata via gh was NOT available this session)
| Project | What it does | Licence (as read) | Reuse |
|---|---|---|---|
| lnfernux/log-horizon | PowerShell. Per table cost tier vs detection tier (enabled analytics rules, Defender custom detections), 344-entry connector knowledge base, SOC optimization recs, DCR transform discovery, noisiness score. Needs Log Analytics Reader, Sentinel Reader, Monitoring Reader (DCRs). | GPL-3.0 | Closest prior art. Do NOT copy code or its knowledge base. Learn the approach only. It WRITES (PATCH table plan and retention): ours never would. |
| madsenco/sentinel-usage-workbook | Workbook deployed into the tenant: PAYG vs commitment tier what-if, live Retail Prices API, per table top lists, 20 percent indicative reduction. Simplified billing only, classic rejected. | MIT | Deploys a resource, so conflicts with "nothing deployed". Useful for the tier what-if logic and the caveats (31-day lock, below-commitment no saving). Needs NOTICE if reused. |
| TheCloudScout/sentinel-pricing | PowerShell, average daily ingestion vs hardcoded tier thresholds (list prices, Feb 2022, West Europe), CSV out. | NOT DETERMINED | Stale thresholds: a warning against hardcoding prices. |
| mathijsvermaat/DefenderIngestToSentinel | Estimates Defender XDR table volume if routed to Sentinel, samples rows via Advanced Hunting. Needs an app registration with AdvancedHunting.Read.All. | NOT DETERMINED | Different access model (Graph app permission). Out of default scope. |
| ninjapaw/sentinel-optimizer | Client-side estimator and SIEM comparison from exported ingestion JSON. No Azure connection. | MIT | Not a collector. |
| rohit8096-ag/Sentinel-Assessment-Tool | Page summary described a MITRE coverage analyser (SentinelMITREAnalyzer) and itself noted a repo URL mismatch. | MIT per summary | UNRELIABLE summary, re-check before citing. Coverage mapping only. |
| Azure/Azure-Sentinel (Microsoft) | Hosts Workspace Usage Report and Optimization workbooks, Send-IngestionCostAlert playbook. | not checked | Not opened this session. Open before design. |

Gap in the field (my reading, UNVERIFIED as a market claim): the tools above are single workspace, interactive, PowerShell,
and none is known to combine ingestion cost with actual (discounted) billing, multi-scope runs and an Excel/HTML
deliverable. Log Horizon is the exception on depth of table-to-detection mapping.

### 6.3 Cost visibility facts that shape the design (VERIFIED, Learn, 2026-10-21)
- Table plan, retention and total retention are readable: GET .../workspaces/{ws}/tables/{table} returns plan
  (Analytics, Basic, Auxiliary), retentionInDays, totalRetentionInDays, archiveRetentionInDays, lastPlanModifiedDate
  (azure-monitor/logs/manage-logs-tables). The same URL with PATCH changes it: never call.
- Basic and Auxiliary plans are not available on legacy pricing tiers (data-platform-logs).
- 31 days of analytics retention are included in ingestion price, so lowering retention below 31 days saves nothing
  (data-retention-configure).
- LAQueryLogs must be enabled (diagnostic setting) and only records Logs-blade queries; it excludes scheduled analytics
  rules, Hunting and Advanced hunting, so zero hits do not prove a table is unused (sentinel/audit-sentinel-data).
- Querying logs: Log Analytics Reader (or any role with */read such as Reader) grants query rights over ALL log tables
  in the workspace, not just Usage. Table-level limits need granular RBAC, protected tables, or the legacy method
  (azure-monitor/logs/manage-access, manage-table-access). Protected tables and DataActionsOnly mode can make Reader
  return empty results without an error.
- nviso blog tag "cost" (June and July 2026) describes Summary Rules plus Auxiliary or lake for firewall logs. Posts
  themselves not opened.

### 6.4 Corrections after reading the repos directly (2026-10-21, shallow clones, files read, no code run)
Method: add_repo reported read access via the session git proxy; shallow clones placed outside the project in
/home/claude/<owner>/<repo> (untrusted data, nothing executed). Azure-Sentinel was a sparse blob-less clone of
Workbooks and Playbooks/Send-IngestionCostAlert only.
| Repo | Licence file | Last commit | Note |
|---|---|---|---|
| lnfernux/log-horizon | GPL-3.0 (LICENSE read) | 2026-10-07 | confirmed. Do not copy. |
| madsenco/sentinel-usage-workbook | MIT, (c) 2026 Kjartan Madsen | 2026-10-05 | confirmed. NOTICE needed if reused. |
| rohit8096-ag/Sentinel-Assessment-Tool | MIT, (c) 2026 Rohit Ashok | 2026-03-11 | repo contains SentinelMITREAnalyzer: the earlier "URL mismatch" was repo name vs module name, summary was right. |
| TheCloudScout/sentinel-pricing | NO licence file found | 2023-05-30 | stale; treat as not reusable. |
| mathijsvermaat/DefenderIngestToSentinel | NO licence file found | 2026-09-04 | treat as not reusable. |
| Azure/Azure-Sentinel | MIT, (c) Microsoft | 2026-10-21 | reusable with notice. |
Microsoft workbooks present in Azure-Sentinel/Workbooks that overlap this module: OptimizationWorkbook (uses
Microsoft.SecurityInsights/recommendations, alertRules, watchlists; tables Usage, SentinelHealth, SentinelAudit, SecurityIncident),
AzureSentinelCost (+EUR/GBP), LogSourcesAndAnalyticRulesCoverage, FirewallLogOptimization (_BilledSize by source),
ArchivingBasicLogsRetention (Tables API, api-versions 2017-10-01 and 2021-12-01-preview inside the workbook),
LogAnalyticsQueryAnalysis (LAQueryLogs), DataCollectionHealthMonitoring, AnalyticsHealthAudit. Not yet studied in
detail. The Microsoft estate already contains most of the KQL ideas; our value is multi-scope, read-only, actual-cost
joined, offline report.
