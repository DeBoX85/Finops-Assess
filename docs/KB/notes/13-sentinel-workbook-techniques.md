# KB 13: Sentinel cost workbooks and tools, technique catalogue

Read 2026-10-21. Method: workbook JSON in Azure/Azure-Sentinel (MIT, sparse clone, last upstream commit 2026-10-21) parsed with a
throwaway script; every query and ARM call quoted below was read in the file. Nothing was executed against any tenant, so
every technique is UNVERIFIED as to behaviour until gate G2. Third-party items are leads, not evidence.
Companion: KB 12 (cost model, access, projects). Licence rule: CLAUDE.md rule 7 (GPL/AGPL/ELv2/unlicensed: ideas only).

## 1. Workbooks read (all MIT, Microsoft)
OptimizationWorkbook, SentinelCosts, AzureSentinelCost (+EUR/GBP), WorkspaceUsage, LogSourcesAndAnalyticRulesCoverage,
FirewallLogOptimization, ArchivingBasicLogsRetention, LogAnalyticsQueryAnalysis, DCR-Toolkit, DataCollectionHealthMonitoring,
AnalyticsHealthAudit, SentinelWorkspaceReconTools, Sentinel_Central, WorkspaceAuditing, SentinelHealth,
MicrosoftSentinelDeploymentandMigrationTracker. Studied closely: the first eight plus DCR-Toolkit. The rest were only
inventoried by title (health, recon, central, migration tracker): DON'T KNOW their detail.

## 2. Technique catalogue (what each does, where the data comes from)
| # | Technique | Source | Data path | Access | Notes for F-CAT |
|---|---|---|---|---|---|
| T1 | Find Sentinel workspaces | Optimization | ARG `resources / type =~ microsoft.operationsmanagement/solutions / name contains SecurityInsights`, workspace id in `properties.workspaceResourceId` | Reader, ARG | Resolves the earlier UNVERIFIED "ARG detection". Tier A. |
| T2 | Workspace and Sentinel pricing SKU | Optimization | ARG: workspace `properties.sku.name`, `capacityReservationLevel`; solution `properties.sku.name`, `capacityReservationLevel` | Reader, ARG | Two SKUs exist (classic vs simplified/unified). Tier A. Interpretation rules needed per billing model. |
| T3 | Table plan, retention, archive | Optimization, Archiving, WorkspaceUsage | ARM GET `.../workspaces/{ws}/tables?api-version=2021-12-01-preview` filtered by `plan` and `archiveRetentionInDays` | Reader | Newer api-versions exist (2025-07-01, 2026-03-01 in templates): pick and verify. Tier A (REST). The Archiving workbook also PATCHes: never. |
| T4 | SOC optimization recommendation states | Optimization | ARM GET `.../providers/Microsoft.SecurityInsights/recommendations?api-version=2024-01-01-preview` | Sentinel Reader | Preview API. Read only. |
| T5 | Billable volume per table | Optimization, Cost, Usage | Log query on `Usage` (IsBillable, Quantity, DataType, Solution) | Log query (ADR 0007) | Core. See unit trap U1. |
| T6 | Per-table size by actual bytes | Cost, Firewall | `_BilledSize` / `_IsBillable` per row | Log query | Row-level scan. Use only with summarize and no content columns. Cost trap U4. |
| T7 | Commitment tier what-if | Optimization | Daily `Usage` GB x tier price, tier fee plus overage at tier effective rate, min across tiers | Log query plus prices | Prices are user parameters in the workbook (hardcoded defaults). We must take prices from cost data or the Retail Prices API, never constants. |
| T8 | Ingestion anomalies | Optimization | `make-series` per table and `series_decompose_anomalies(1.5, 7, 'linefit', 1, 'ctukey', 0.01)`, score >= 3 | Log query | `union withsource * ` over all tables: expensive, see U4. A `Usage`-based variant is possible. |
| T9 | Stale tables | Optimization | last record age per table, joined to `Usage` | Log query | Same `union *` caveat. |
| T10 | E5 and Defender for Servers allowances | SentinelCosts, Optimization | Eligible DataType list x seats x 5 MB/day; cap per day then sum | Log query plus seat count (needs input) | Seats are a user input. Defender for Servers: 500 MB/node/day, pooled per subscription, benefit shows as zero-cost lines in cost exports (Learn, below). |
| T11 | Analytics rule to table mapping | LogSourcesAndAnalyticRulesCoverage | ARM GET `.../providers/Microsoft.SecurityInsights/alertRules` (api 2021-10-01-preview), substring match of table name in `properties.query`; also `alertRuleTemplates` | Sentinel Reader | Substring matching: see U2. Needs ADR-style privacy handling because rule KQL is customer content. |
| T12 | Event ID dependency | same, DCR-Toolkit | regex over rule KQL for `EventID ==`, `in (...)`, `between` | same | Regexes miss `!=`, joins, functions, ASIM parsers. |
| T13 | DCR inventory and transforms | DCR-Toolkit, Optimization | ARM GET `/subscriptions/{id}/providers/Microsoft.Insights/dataCollectionRules` (api 2021-09-01-preview used); `dataFlows[].transformKql`, `xPathQueries`, `destinations`, workspace `defaultDataCollectionRuleResourceId` | Monitoring Reader | Read-only GET. ARG coverage of DCRs UNVERIFIED. Tier A or B. |
| T14 | Per EventID / per computer ingestion | DCR-Toolkit, Optimization | `SecurityEvent / summarize sum(_BilledSize) by EventID, Computer` | Log query | Computer names are customer data: pseudonymise (redact.py). Never project message text. |
| T15 | Query activity per table | LogAnalyticsQueryAnalysis, Practical365 | `LAQueryLogs` (must be enabled) | Log query | Only Logs-blade queries. |
| T16 | Firewall volume and noise | FirewallLogOptimization | `CommonSecurityLog` by vendor/DeviceAction, noise = allow share; Syslog by severity | Log query | Heuristic "noise": allow events are not necessarily noise. Static vendor rule-dependency table in workbook is a snapshot and says so. |
| T17 | Retention cost of old data | SentinelCosts | `union * | where TimeGenerated < ago(90d)` x price | Log query | Dubious: data older than 90d only exists where retention is extended, and `union *` scan. Prefer Tables API retention x `Usage`. |
| T18 | Workspace health and automation cost | Optimization, SentinelCosts | SentinelHealth failures, Logic App execution count x hardcoded 0.000125 | Log query, ARG | Out of FinOps core; SOAR cost is a possible later module. |

## 3. Pitfalls found in the existing tools (design rules for ours)
- U1 Unit mixing: the same workbooks divide `Quantity` (MB) by 1000 in some places and 1024 in others (Optimization uses /1000,
  SentinelCosts uses /1024, Cost uses /1024/1024/1024 on bytes). Learn's own query uses /1000. We pick one definition, state it,
  and test it with a metamorphic test.
- U2 Substring matching of table names in rule KQL gives false positives (name inside a comment, or `Event` inside `SecurityEvent`)
  and false negatives (saved functions, ASIM parsers, `union *`, workspace functions, watchlists). So: "no rule found" must be
  reported as "no consumer found by text match, not proof of non-use". Microsoft's own firewall workbook says the same:
  "A zero mapped count does not mean the data has no detection or investigative value".
- U3 Privacy: some workbook queries return data values or message text (`evaluate narrow()` over `take 1000`, `SyslogMessage`,
  `RenderedDescription`). F-CAT queries must be an allowlist of aggregates over `Usage` and bytes only, no content columns.
  Hostnames and IPs in `by Computer` or `by SourceIP` are customer data.
- U4 Cost of measuring: `union withsource=* ` touches every table. Querying Basic or Auxiliary tables is billed per GB scanned
  (Learn "Query data in Basic and Auxiliary tables", billing details not read: UNVERIFIED amount). Prefer `Usage`, which is small.
- U5 Hardcoded prices (4.3, 5.0, 4.0 per GB in different workbooks; sentinel-pricing thresholds frozen at Feb 2022). We take
  prices from the customer's own cost data and label list-price fallbacks as list.
- U6 Classic vs simplified billing changes what the SKUs mean and whether Basic/Auxiliary exist (Learn: not on legacy tiers).
- U7 The Archiving workbook and Log Horizon can change retention and plans. F-CAT never calls PATCH/PUT/POST on these.

## 4. First-party facts verified today that matter for recommendations (Learn)
- Filter and split transformations exist in the Defender portal Tables page; they need the workspace onboarded to the Defender
  portal, data lake onboarding for split, Log Analytics Contributor and Defender "Data (manage)". Filter DISCARDS data. Split mirrors
  matching data to the lake and sends the rest to the lake only, into a `_SPLT` table. Warning on conflicts with existing DCR
  transforms. (sentinel/transformation-filter-split.) These changes are WRITES: we only recommend.
- Data lake billing: ingestion and processing per GB for lake-only tables, storage at a fixed 6:1 compression assumption, query per
  GB scanned, advanced insights per compute hour; after onboarding these meters replace archive/search/auxiliary meters.
  (sentinel/billing.)
- A Sentinel cost estimator exists (microsoft.com/security/pricing/microsoft-sentinel/cost-estimator, referenced from the billing
  page). Whether it has an API: DON'T KNOW. Release date claim from a blog (April 2026): UNVERIFIED.
- Defender for Servers P2: 500 MB per node per day, pooled per subscription, applied at workspace level, only for listed security
  tables and only for security events collected through the supported AMA path; benefit does not appear on the invoice (zero
  cost) but does appear in Cost Management exports as meter "Standard Data Included per Node"; the M365 E5 benefit appears as
  "Free Benefit - M365 Defender Data Ingestion". (defender-for-cloud/data-ingestion-benefit; azure-monitor/fundamentals/cost-usage.)
  A Microsoft Q&A answer says custom DCRs from the Sentinel connector do not qualify; Q&A is lower authority: UNVERIFIED.
- Free trial: first 10 GB/day free for 31 days, 20 workspaces per tenant limit. (sentinel/billing.)
- Custom detections in the Defender portal are described by Microsoft as the preferred rule type and can reduce ingestion cost;
  they work on data not necessarily ingested into Sentinel. Impact: rule inventory must include Defender custom detections
  (needs Graph permission in Log Horizon, source: its README; our access model for this: DON'T KNOW).

## 5. Third-party items read this round (leads only)
- Charbel Nemnom (published 2026-03-11, modified 2026-06-22), readable at charbelnemnom.com/sentinel-cost-estimation-and-optimization/:
  tier placement, DCR filtering "free on analytics tables", allowances, SCU pre-purchase. Several numbers are the author's own
  derivations and the article has internal inconsistencies (5,000 SCU discount quoted as 44 percent and as 8 percent). UNVERIFIED.
  Page read only to 100,000 of 118,920 characters.
- Practical365 (Thijs Lecomte, undated): review order that matches ours (spend, costly tables, rule use, query use, age, tiers).
  Claim "Auxiliary logs cannot be used in analytic rules": UNVERIFIED on Learn.
- Undercode "data lake workbook": low quality, probable AI-generated, wrong cmdlet names, no licence: do not use.
- Microsoft training lab E09 (Azure-Sentinel repo, MIT): `Usage` queries plus latency via `ingestion_time()`; needs Billing Admin
  and Security Admin roles for the portal parts.
- Community Defender XDR sizing script (DefenderIngestToSentinel): no licence file, ignore code.

## 6. What this changes in the module design
1. Tier A can already enumerate Sentinel workspaces, SKUs, table plans and retention, DCR transforms, recommendation states.
2. Tier B (ADR 0007) is needed only for `Usage` aggregates and, optionally, LAQueryLogs and SentinelHealth counts. A fixed query
   allowlist of aggregates removes most of the privacy concern (U3).
3. Rule-to-table dependency (T11/T12) is the coverage safeguard. It reads customer detection logic through `alertRules`, so it needs
   its own opt-in, redaction of rule names and queries in outputs, and the "no consumer found by text match" wording (U2).
4. Cost proof requires cost data (ADR 0006) to join billed amounts and allowance lines to the table inventory.
