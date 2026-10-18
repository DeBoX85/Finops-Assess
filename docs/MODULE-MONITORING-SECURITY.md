# Monitoring and security cost module: design (2026-10-18)
Builds on docs/KB/notes/09 (research and the proposed catalogue LA-/AI-/DC-/SE- IDs). This page decides what can be built when, based on what access each check needs. Facts below were re-read on Microsoft Learn on 2026-10-18 unless marked UNVERIFIED.

## Access tiers
| Tier | Needs | Allowlist change | Checks (note 09 IDs) | Status |
|---|---|---|---|---|
| A | Reader and Azure Resource Graph only (`resources`, `securityresources` tables) | none | inventory and configuration checks: LA-07 (no daily cap), AI-01 (App Insights not workspace-linked), DC plan inventory and dev/test plan check (DC-03), plus Sentinel detection (UNVERIFIED how) | built offline (below) |
| B | Query a workspace: POST `https://api.loganalytics.azure.com/v1/workspaces/{workspaceId}/query` (Learn: Logs query API request format). A different host from management.azure.com, so the allowlist and the single-scope token provider both change. Which token scope it needs: UNVERIFIED | new ADR 0007 (draft, owner decision parked as DECISIONS-PENDING #10) | LA-01..04, LA-08, LA-09, AI-02, AI-04, SE-01..03 (all need the Usage table or per-record `_BilledSize`) | not started; blocked on the decision |
| C | Cost data (actual cost, list price) | ADR 0006 (parked) | every "savings" figure; actual versus list shown separately | not started; blocked |

Reader alone is not enough for tier B: querying needs `Microsoft.OperationalInsights/workspaces/query/read` (note 09 section 4).

## What tier A can honestly say
- LA-07: a workspace without a daily cap. Learn calls the cap a preventative control, not a saving, so this is an informational governance finding, confidence low. Free-tier workspaces are skipped (fixed daily limit; UNVERIFIED value). How ARG shows "no cap" (null or -1) is UNVERIFIED; the check treats null and negative as no cap.
- AI-01: an Application Insights resource with no workspace link. Learn: the `workspaceResourceId` property is "required to create an application with this API version. Applications from older versions will not have this property." So absence means an older resource, not necessarily a defect. Informational migration finding. Property name casing in ARG (WorkspaceResourceId vs workspaceResourceId) is UNVERIFIED; the query reads both.
- DC plan check: Defender for Cloud plans at pricing tier Standard on a subscription whose offer looks like Dev/Test (quota ID contains "DevTest"). Source for the pricing table and fields: Learn, Defender for Cloud Resource Graph samples (`SecurityResources | where type == 'microsoft.security/pricings'`, `properties.pricingTier`). Whether a plan is wanted on dev/test is a business call, so confidence low and wording is "review". The Dev/Test inference from quota ID alone is a heuristic (UNVERIFIED), tags are not consulted.

## What tier A cannot say
Whether anything is over-provisioned, which tables dominate cost, or what a change would save. Those need B and C. Reports must say "not assessed because the workspace query access is not enabled" for them, never silence.

## Build order
1. Tier A checks (done 2026-10-18, offline-only).
2. ADR 0007 decision, then a `loganalytics` client path with its own allowlist entry and tests (blocked entries stay blocked, as in ADR 0003).
3. Usage-based checks with peak-aware logic where relevant (ingestion spikes versus averages: DEV-PRINCIPLES R10).
4. Savings maths once ADR 0006 allows cost data; show actual and list price separately.

## Sources
- https://learn.microsoft.com/azure/azure-monitor/logs/api/request-format (read 2026-10-18)
- https://learn.microsoft.com/azure/defender-for-cloud/resource-graph-samples (read 2026-10-18)
- https://learn.microsoft.com/javascript/api/@azure/arm-appinsights/applicationinsightscomponentproperties (read 2026-10-18)
- docs/KB/notes/09-monitoring-and-security-cost-assessment.md (Learn pages read 2026-10-17)
