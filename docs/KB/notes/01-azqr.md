# azqr (Azure Quick Review) knowledge note

Verified: 17 Oct 2026, by opening the pages listed under Sources. Status words: OPENED = page content read; NOT SEEN = page did not show it.

## Identity
- Repo: https://github.com/Azure/azqr (OPENED). Public, 782 stars, 141 forks, 1,170 commits on main, 3 open issues, 1 open PR.
- Licence: MIT, "Copyright (c) Microsoft Corporation." (LICENSE file OPENED).
- Language: Go. README says build needs "Go 1.23.x or higher". Single self-contained cross-platform binary.
- Latest release number and last commit date: NOT SEEN on the repo page (fields were blank). The docs site shows "Last modified October 16, 2026" for most pages (commit 8d03fa7, "fix: add ARO cluster ownership lookup to VM modernization plugin #1064") and 15 Oct 2026 for the Usage page. The repo page was served with an image timestamp of 2026-08-01, so the repo snapshot may be cached. Treat "actively maintained" as supported by the docs dates only.

## How it works (from README, Overview, Related)
- Two recommendation types:
  1. Azure Resource Graph (ARG) queries, taken from APRL (Azure Proactive Resiliency Library v2) and from dolevshor/azure-orphan-resources.
  2. ARM rules written in Go against the Azure Go SDK.
- APRL queries merged in from v2.0.0-preview (Aug 2024 per Related page). Orphan resources merged in from v2.4.0.
- Scan scope: all accessible subscriptions by default, or --subscription-id, --management-group-id, --resource-group.
- Auth: Azure SDK DefaultAzureCredential (env vars, workload identity, managed identity, Azure CLI, azd). AZURE_TOKEN_CREDENTIALS=dev|prod switches priority. README notes Azure CLI auth "will make scans run slower".
- Permission: Reader at subscription or management group. ai-gov plugin also needs Monitoring Reader. Cost stage needs cost access; error AccountCostDisabled seen when only Reader is held. The docs do not name a Cost Management role (NOT SEEN).
- Sovereign clouds: supported via AZURE_CLOUD=AzurePublic|AzureGovernment|AzureChina, or custom endpoints. (Out of scope for now per user, but cheap to keep in mind.)
- No overall timeout, resource cap or memory cap (Usage page, CI/CD section).

## Stages (Usage page)
advisor, defender, defender-recommendations, arc, policy, cost, diagnostics.
- Enabled by default: diagnostics, advisor, defender. Others off.
- Cost stage: DISCREPANCY inside azqr docs. README and Overview say "Cost data for the last calendar month". Usage page says "Cost analysis for the last 3 months". Do not rely on either until tested.
- Flag syntax also differs between pages (`--stages cost --stages policy` in README, `--stages cost,policy` in Usage).

## Outputs
- xlsx (default), csv, json, sarif 2.1.0, JSON to stdout (--json --stdout).
- Core sheets: Recommendations, ImpactedResources, ResourceTypes, Inventory (SKU, tier, kind, calculated SLA), OutOfScope.
- Optional sheets: Advisor, Defender, DefenderRecommendations, Azure Policy, Arc SQL, Costs.
- Subscription IDs masked by default (--mask=false to show).
- --fail-on High|Medium|Low for CI gating (core and diagnostics findings only).
- Filters YAML: include/exclude subscriptions, resourceGroups, resourceTypes (abbreviations), services, recommendations, and tags (tags added per Usage page; README shows an older filter format without tags).
- `azqr rules` lists recommendations as markdown or JSON.
- MCP server: `azqr mcp` (stdio) or `azqr mcp --mode http --addr :8080`.

## Recommendation catalogue (Recommendations page, OPENED but output truncated at row 249)
- Page states "Total Supported Azure Resource Types: 107". Overview/README say "70+ resource types". Related page says "more than 400 recommendations". Treat the counts as inconsistent; the catalogue should be pulled with `azqr rules --json` for an exact count.
- Fields: Id, Resource Type, Category, Impact (High/Medium/Low), Recommendation text, Learn link.
- Categories seen: HighAvailability, MonitoringAndAlerting, DisasterRecovery, Scalability, Governance, Security, OtherBestPractices, ServiceUpgradeAndRetirement, BusinessContinuity, SLA.
- KEY FINDING: there is NO Cost category. YAML plugin categories also have no Cost value (valid list: High Availability, Security, Disaster Recovery, Scalability, Governance, Monitoring and Alerting, Business Continuity, Service Upgrade and Retirement, Other Best Practices).
- Orphan/idle checks sit under "Governance" (examples seen): unattached managed disks, public IPs not attached, NICs not attached, NSGs not attached, NAT gateways not attached to a subnet, route tables not attached, App Service plans with no apps, empty resource groups, DDoS plans without protected resources, App Gateways without backends, load balancers with empty backend pools, SQL elastic pools without databases, private DNS zones without VNet links, traffic manager without endpoints, IP groups unused, API connections unused, expired certificates, private endpoints not connected, VNets without subnets, VNet gateways without P2S/connections, availability sets unused, Front Door WAF policies without associations.
- SPECULATION: IDs such as 1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d and 0b1c2d3e-4f5a-6b7c-8d9e-0f1a2b3c4d5e follow a sequential pattern and look hand-assigned (the orphan-resource set), not product-group GUIDs.
- Other cost-relevant items seen: Basic to Standard SKU upgrades (LB, public IP), App Gateway v2 migration, storage account v1 to v2, ACR retention policies, VM v6/v7 modernization.

## YAML plugins (Plugins page, OPENED)
- One .yaml per plugin: name, version, description, optional author/license; list of queries with aprlGuid, description, recommendationControl, recommendationImpact, recommendationResourceType, and query or queryFile (.kql).
- Optional per query: longDescription, learnMoreLink[], recommendationTypeId, recommendationMetadataState, potentialBenefits, pgVerified, automationAvailable, tags[].
- Query must return id, name, resourceGroup, location. Use `=~` for type comparison.
- Discovery: ./plugins, ~/.azqr/plugins, /etc/azqr/plugins.
- Limits (stated): ARG queries only (no ARM calls), subscription scope, no custom logic.
- Design lesson: this schema is a good template for a "checks as data" format but lacks cost fields (estimated saving, confidence, billing-type applicability, required role). Our format must add them.

## Internal plugins (Internal Plugins page, OPENED; disabled by default)
| Plugin | Version | Data source | Cost relevance |
|---|---|---|---|
| ai-gov | 1.0.0 | Azure Monitor Metrics (24-48h) | 429 throttling for OpenAI/Cognitive Services, capacity not cost |
| carbon-emissions | 1.0.0 | Azure Carbon Optimization API | sustainability, month-over-month by resource type |
| zone-mapping | 1.0.0 | ARM Subscriptions API | none |
| region-selection | 0.2.0-beta | ARM Providers/SKU APIs, Cost Management + Retail Prices, published RTT stats | 15% weight on cost difference; CostComparison sheet |
| sql-eol | 0.6.0-beta | ARG | ESU cost model, SQL MI migration savings (2:1 consolidation assumption) |
| vm-modernization | 0.1.0 | ARG + Retail Prices API | per-VM current/projected cost for v6/v7 moves |
| service-health | 0.1.0-beta | ARG servicehealthresources (90 days) | none |
- vm-modernization and sql-eol show azqr already computes per-resource list-price cost estimates via the Retail Prices API. This is a reusable pattern for the "list price" half of the user's actual-vs-list savings requirement.

## What azqr does NOT do (relevant to our goal)
- No cost category or savings quantification across the estate (only the Costs sheet and two plugins).
- No commitment (reservation / savings plan) analytics found in the pages read.
- No maturity model, no FinOps Framework mapping, no FOCUS checks.
- Excel is the primary output; no HTML dashboard found in the pages read (NOT SEEN, not confirmed absent).
- Orphan checks are query-presence only; I did not see age, cost or confidence logic.

## Related projects (Related page, OPENED)
- azqr started 2022 to combine SLA, availability zone and diagnostic-settings reviews. Compared with PSRule.Rules.Azure: azqr scans deployed resources only, not ARM/Bicep. Compared with Azure/review-checklists: azqr gives an actionable list.
- Customers in restrictive environments valued a self-contained binary with read-only permissions. Same driver as our "nothing deployed" constraint.

## Pages not yet opened
Install, Troubleshooting, Contributing, Reference, Profiling (azqr docs). Repo sub-paths (internal/, data/, docs/) not browsed.

## Sources
- https://github.com/Azure/azqr
- https://github.com/Azure/azqr/blob/main/LICENSE
- https://azure.github.io/azqr/docs/
- https://azure.github.io/azqr/docs/overview/
- https://azure.github.io/azqr/docs/usage/
- https://azure.github.io/azqr/docs/plugins/
- https://azure.github.io/azqr/docs/plugins/internal-plugins/
- https://azure.github.io/azqr/docs/recommendations/
- https://azure.github.io/azqr/docs/related/
