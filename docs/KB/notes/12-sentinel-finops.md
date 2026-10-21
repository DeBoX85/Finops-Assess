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
