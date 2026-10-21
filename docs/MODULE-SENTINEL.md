# Sentinel FinOps module: design (2026-10-21, PROPOSED, ADR 0010)
Evidence: docs/KB/notes/12-sentinel-finops.md and 13-sentinel-workbook-techniques.md (Learn and Microsoft MIT workbooks read 2026-10-21). All checks below are `offline-only` until gate G2.

## Goal
Give a customer who lost control of Sentinel a per-table map of what is ingested, what it costs (actual vs list), how it is stored, what depends on it, and what could be reviewed, without suggesting anything that removes detection coverage unseen.

## Config (owner-only toggles, all default off)
```
[sentinel]
enabled = false
scopes = []              # tenant, management group, subscription or workspace ids; uses the existing authorizationScopeFilter
query_usage = false      # tier B: Usage aggregates (needs ADR 0007)
query_audit = false      # tier B: LAQueryLogs/SentinelHealth counts, only if the tables exist
scan_rules = false       # reads alertRules; see section Rule scan (DECISIONS-PENDING #14)
seats = 0                # M365 E5 seats, needs input; 0 = allowance not assessed
```
Multi-tenant: one scoped run per tenant, rolled up by the report; no cross-tenant credential reuse in one process.

## Checks by tier (proposed IDs)
| ID | Tier | What | Evidence |
|---|---|---|---|
| SEN-INV-01 | A | Sentinel workspaces, region, pricing SKU and commitment (workspace and solution), billing model classic or simplified | ARG: workspaces, `microsoft.operationsmanagement/solutions` named SecurityInsights |
| SEN-SPRAWL-01 | A | Several Sentinel workspaces, per region, informational | ARG |
| SEN-PLAN-01 | A | Table plan, analytics retention, total retention, archive days per table; flags long analytics retention beyond the included 90 days | Tables API GET |
| SEN-SOC-01 | A | Microsoft SOC optimization data-value recommendation states per workspace | recommendations GET (preview) |
| SEN-DCR-01 | A | Collection rules: ingestion-time transforms present or absent per destination workspace | DCR GET |
| SEN-PORTAL-01 | A | Defender portal onboarding vs 2027-03-31 retirement | `onboardingStates`: UNVERIFIED readable; else "not assessed" |
| SEN-TOP-01 | B | Billable GB and share per table, peaks and averages | Usage |
| SEN-TIER-01 | B | Commitment tier fit using daily series (peak-aware, DEV-PRINCIPLES R10), 31-day lock caveat, classic caveat | Usage plus prices from cost data |
| SEN-ANOM-01 | B | Ingestion spikes per table | Usage series |
| SEN-ALLOW-01 | B+C | E5 and Defender for Servers P2 allowances used vs available | Usage plus seats (input) plus cost export lines |
| SEN-CON-01 | B | Connector enabled but no ingestion, or ingestion without connector | dataConnectors plus Usage |
| SEN-NOCON-01 | B | High-cost table with no consumer evidence: Review verdict | SOC-01 evidence, plus rule scan if enabled, plus audit counts if enabled |
| SEN-SPLIT-01 | B | Lake/Auxiliary/split candidates, worded as options with prerequisites (needs lake onboarding, Defender portal, write roles held by the customer) | combines the above |
| SEN-COST-01 | C | Actual vs list per meter, savings shown separately for each | ADR 0006 data |
Without a needed input a check returns not assessed with the reason (rule 6).

## Per-table verdicts (output sheet "Sentinel tables")
Columns: table, GB/day average and peak, share, actual cost, list cost, plan, retention, DCR transform present, consumer evidence (and its source), query activity (if audit on), allowance coverage, verdict, what is unknown.
Verdicts: Protected (enabled consumer found), Review (cost high, no consumer evidence, unknowns listed), Unknown (consumer evidence not collected), Covered (free table or allowance). Never "Remove".
Wording rule for any "no consumer": "no consumer found by <source>; this does not prove the data is unused" (KB 13 U2).

## Query allowlist for tier B (ADR 0007 addendum if approved)
Fixed templates only, always with a bounded time range: Usage aggregates; optional LAQueryLogs table counts; optional SentinelHealth counts. No `union *`, no `find`, no content columns, no per-computer or per-IP groupings in v1. Dot-prefixed text blocked. Query text is not user-configurable.

## Rule scan (decision #14), impact
What it reads: `alertRules` (name, description, enabled, severity, tactics, last modified, query text). Needs Sentinel Reader (`Microsoft.SecurityInsights/*/read`); that generic Reader suffices is UNVERIFIED.
If ON:
- Gains: table and Event ID consumers per enabled rule, so Review verdicts and DCR filter options can be backed by dependency evidence, and Protected verdicts become trustworthy.
- Handling (proposed): query text lives in memory only; the snapshot stores a derived map (table names, Event IDs, enabled flag, last modified) and a hash; rule names pseudonymised in outputs unless an owner toggle says otherwise; ADR 0009 style guard test for any rule text in committed files.
- Limits that remain: functions, parsers, `union *`, Defender custom detections not visible as alert rules (UNVERIFIED), text-match false positives and negatives.
- Cost: more code and tests (parser, redaction, fixtures); my estimate is about a third of the module's tier B effort (speculation).
- Customer trust: reading detection logic is a separate permission conversation.
If OFF (proposed default):
- Consumer evidence comes from Microsoft's own SOC optimization states (SOC-01) and optional audit counts. Those cover analytics rule use of billable tables with ingestion in the last 30 days, are computed by Microsoft every 24 hours, and the API is preview.
- Table verdicts are Review or Unknown; SEN-SPLIT-01 options carry "dependency not verified" and never reach a savings headline.
- Event-ID level DCR advice is not offered.

## Build order
1. Tier A checks with fixtures, synthetic data, goldens (offline). Needs only Reader. Can start now.
2. Table verdict sheet and report section skeleton from tier A data (shows "not assessed" for B/C columns).
3. After ADR 0007: Usage client path, SEN-TOP/TIER/ANOM/CON.
4. After ADR 0006 data wiring: SEN-ALLOW, SEN-COST, savings with actual vs list.
5. After decision #14: rule scan and SEN-NOCON/SPLIT upgrades.
6. G2 on a test tenant with a Sentinel-enabled workspace and ingested data (cost money; tell the tenant preparer).
Each step ends with tests, golden re-approval after `ruff format`, PARITY entry, checkpoint.

## Open points (UNVERIFIED or DON'T KNOW)
Api-versions to pin for tables, alertRules, recommendations, dataConnectors, DCRs; ARG exposure of DCRs; onboardingStates readability; data lake usage via API (DON'T KNOW); Microsoft cost estimator API (DON'T KNOW); behaviour under protected tables or DataActionsOnly (returns empty, must be reported as not assessed).
