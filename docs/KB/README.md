# F-CAT knowledge base (state at 17 Oct 2026)

Purpose: verified baseline and data repository before design and development of a read-only Azure FinOps assessment tool.
Rule used throughout: every fact carries its source; "OPENED" means the page was actually fetched in this session; summaries from the fetch tool come from a small model and must be re-opened before being quoted in a client deliverable. Nothing here has been tested against a live tenant.

## Contents
| File | What it holds |
|---|---|
| notes/01-azqr.md | azqr architecture, stages, outputs, licence, gaps (no Cost category) |
| notes/02-finops-toolkit-workbooks.md | Every Optimization and Governance workbook check, parsed from source, with defects found |
| notes/03-toolkit-release-state.md | Toolkit release state: latest tag v14 (29 Apr 2026), v15 unreleased |
| notes/04-initial-links.md | The links in your first message (AOE, open data, FOCUS generator page, Azure FOCUS schema, conformance, blogs, framework) |
| notes/05-focus-spec-and-sources.md | FOCUS version history and Azure position |
| notes/06-microsoft-docs-entries.md | Entry-by-entry log of all 89 unique URLs in Finops_research.html |
| notes/08-language-and-licence.md | Language and licence evidence and preliminary recommendation (reddit sentiment could not be reached) |
| notes/09-monitoring-and-security-cost-assessment.md | Sentinel, Defender, App Insights, Log Analytics: verified facts, source reliability, proposed check catalogue |
| notes/07-hub-recommendation-queries.md | Inventory of the 23 hub ARG recommendation queries (20 default, 3 optional; count reconciled against Learn page and source) |
| notes/10-cost-api-and-billing-types.md | Cost Management data by billing type, APIs, limits |
| notes/11-cost-governance-azure.md | Cost governance on Azure: CAF, WAF, FinOps, Policy, tags, budgets, anomaly alerts, exports; what a Reader can see (2026-10-20) |
| sources/url-register.csv | One row per URL: status, reliability, note |
| sources/workbook-queries-raw.json | 467 raw workbook query rows |
| sources/hub-recommendation-queries/ | 23 hub query JSONs (MIT, Microsoft; attribution needed) |

## Headline findings
1. Azure FOCUS exports lag the spec. FOCUS 1.4 was ratified 4 Jun 2026 (second source confirms). Azure emits 1.2-preview (105 columns, 94% conformance against 1.2 per Microsoft). The tool must target what Azure emits and treat 1.3 and 1.4 as a forward mapping.
2. ListCost and ContractedCost are 0 for reservation usage and Marketplace in Azure FOCUS data. The "list price" half of the actual-vs-list savings requirement therefore needs a price sheet or Retail Prices API join.
3. Toolkit: latest release is v14 (GitHub shows 29 Apr 2026). The file's "v15 Oct 2026" is unsupported by the live changelog, GitHub releases and tags. The repo source changelog has a v15 section marked June 2026 that conflicts with them.
4. Hub Recommendations feature is off by default (enableRecommendations=false). Hubs cost from about $120 per month and need deployment, which conflicts with the "nothing deployed" constraint. AOE also needs deployment (Automation, Log Analytics, SQL, storage).
5. PAYG/MOSA subscriptions cannot use FOCUS exports (hubs 0.2+ docs). The tool needs a Cost Management Query API path for them.
6. No existing tool does cost-focused, read-only, estate-wide assessment with confidence and savings. Nearest peers: CleanCloud (MIT, 50 rules, read-only), azure-cost-cli (C#), azqr (no Cost category), toolkit workbooks (Advisor and ARG predicates, some misleading titles and bugs).
7. Time-bound item: Azure reservation exchanges end for new purchases from 1 Feb 2027 (Microsoft Learn). Reservations bought earlier keep one final exchange. This is relevant to commitment findings today.
8. Licences: azqr MIT, toolkit MIT, Cloud Custodian Apache-2.0, OptScale Apache-2.0, Steampipe and Powerpipe AGPL-3.0, Komiser ELv2 (not open source). Reuse of Komiser, Steampipe or Powerpipe code is a licence risk.

## Claims in your file that are contradicted or unsupported
- "v15 release Oct 2026" and "v15 in progress": not supported (see 3).
- "542 commits" for azure-finops-agent: page shows 352. "Actively maintained by Microsoft": it is in Azure-Samples, not stated as a Microsoft product.
- "FOCUS 1.4 adds AI/ML cost columns": not supported by anything read; 1.4 sources describe Invoice Detail, Billing Period and invoice reconciliation.
- Entry for Komiser uses kubeshop/komiser (errors); working repo is mlabouardy/komiser.
- Entry for focus_converter_azure points to an empty shell (1 commit); the converter is focus_converters.
- Header says 87 sources; file has 96 numbered entries and 89 unique URLs.
- pigottk4/finops-cost-management-azure README mentions an external Windows installer: treat as unsafe.

## Not done yet (be aware)
- Not opened or only metadata: techcommunity posts 4420302, 4555727, 4408601, 3704132 (bodies not retrievable), Copilot in Cost Management post.
- FOCUS 1.4 column list and changelog, Microsoft conformance full report (198 KB, not read), azqr install/troubleshooting/contributing/reference/profiling pages, azqr rule catalogue (needs `azqr rules --json`).
- Repo last-commit dates were not shown by the fetch tool, so maintenance status of community repos is unverified.
- Not yet tested: any ARG query, Billing API 2019-10-01-preview, Cost Management API versions.
- Language and licence: see notes/08. Preliminary: Python CLI, MIT. Reddit sentiment could not be checked (site blocked). Pending your answer on whether the tool will stay private/proprietary.
