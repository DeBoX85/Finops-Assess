# KB 14: GitHub FinOps and cost tools, gap analysis against F-CAT (2026-10-21)

Trigger: owner asked whether features are missing, after looking at similar tools on GitHub.
Method: web search for candidates, shallow clones, read LICENSE, README, file list and last commit. Tool code was NOT read except file lists, so what a tool "does" below is what its README claims (UNVERIFIED as to correctness). Nothing was executed. Rule 7 applies: ideas only, no code, queries or data copied from GPL, unlicensed or ELv2/AGPL repos.

## 1. What was read

| Repo | Licence (file read 2026-10-21) | Last commit | Kind | Reusable? |
|---|---|---|---|---|
| globalcloudgenius/azure-finops-assessment-toolkit | MIT (Isaac Obaro) | 2026-09-19 | One PowerShell script, Azure CLI login, ARM inventory + Cost Management cost details, HTML/PDF executive report | Notice needed if reused |
| MarcSteene/AzureCostOptimizationReportingTool (ACORT) | GPL-3.0 | 2022-07-07 | PowerShell, deployed into the customer tenant (Logic App, managed identity, runbook), email report | No (GPL, rule 7) |
| EmergentSoftware/azure-assessment | no licence file | 2026-10-14 | PowerShell scripts (VM, disk, backup vault) plus an Azure Functions job API with Terraform | No (no licence) |
| robinpats182/finops-agent | no licence file | 2026-10-11 | Python, ARG rules (orphan disk, unused IP), Azure OpenAI tool-calling loop, proposal for human approval | No (no licence) |
| finopsfoundation/frameworkassessment | no licence file at repo root | 2022-10-03 | Markdown playbook for FinOps maturity: capabilities scored on five lenses | No to copy text; the method is public on finops.org and was already used as a source |
| devopsabcs-engineering/finops-scan-workshop | MIT | 2026-04-17 | Workshop for PSRule, Checkov, Cloud Custodian, Infracost with SARIF output | Workshop text only; the four tools have their own licences (UNVERIFIED by me) |
| hystax/optscale | Apache-2.0 (LICENSE.md read) | 2026-10-15 | Full hosted platform, multi-cloud, K8s, Databricks, agent-based ingestion | Not comparable in shape; ideas only |
| mobieus-engineering-development/azure-finops-assessment | not accessible | n/a | n/a | Not assessed, because the repo could not be opened |

Not opened (so no claim): Cloud Custodian, Infracost, OpenCost, Prowler, FinOpsPP/Framework-Assessment, hyperglance. Azure Optimization Engine, finops-toolkit and azqr were covered earlier (KB 01 to 04). The search was a few web searches, not an exhaustive crawl, so a better match may exist.

## 2. Candidate gaps (my judgement, not verified facts)

Checked against docs/PARITY.md, BACKLOG.md, PLAN.md and a grep of src/ and docs/ on 2026-10-21.

| # | Gap | Seen in | Is it really missing in F-CAT? | Needs |
|---|---|---|---|---|
| G1 | Reconcile cost lines to live inventory: spend on resources that no longer exist, spend not mapped to any resource, plus tie-out totals. Their sample headline was one deleted VPN gateway at 98.7% of month-to-date spend (their own report, a single small tenant, so not a benchmark). | GCG | Yes. Only "snapshot source deleted" mentions deleted. Backlog 22 says reconciliation waits for data. | Cost data (ADR 0006) |
| G2 | Run-to-run comparison: what is new, fixed, worse since the last assessment. | Foundation playbook (trend analysis stage), OptScale (continuous) | Yes. grep found no baseline or diff feature. Fingerprints (AUDIT layer A) make a diff cheap to build. | Nothing new; offline |
| G3 | Cost-weighted prioritisation: rank findings by money, with actual versus list. | ACORT (cost potential per subscription), GCG | Planned (backlog 4, 5, 26), not built. This is a priority question, not a new idea. | ADR 0006 |
| G4 | Non-production checks: Dev/Test offer not in use, VMs in dev/test without auto-shutdown, premium or geo-redundant storage in dev/test. | ACORT README | Partly. Dev/Test is used to exclude from some checks; no check reports the missing offer or missing auto-shutdown. | Reader + ARG (auto-shutdown may need a separate resource type: UNVERIFIED) |
| G5 | Storage accounts without lifecycle management rules. | ACORT README | Yes (grep: no "lifecycle"). | Reader; ARG exposure of management policy is UNVERIFIED |
| G6 | Smaller orphan items: empty availability sets, deallocated VMs over 90 days, snapshots older than 1 year (ours uses 30 days). | ACORT README | Partly: deallocated lists are PLANNED (backlog 7). | Reader + ARG |
| G7 | Per-capability depth for maturity: Foundation playbook scores each capability on five lenses (Knowledge, Process, Metrics, Adoption, Automation), 0 to 4, with a target score per capability. | Foundation playbook | By design no: owner chose a simplified Crawl/Walk/Run screen. A "target level per capability" idea (good enough is not always Run) fits the existing maturity README and is cheap. | Owner decision |
| G8 | Multi-tenant or MSSP batch run with a roll-up. | OptScale (multi-account) | Unclear. grep of src/fcat/config.py found no tenant list, so I believe a run is one tenant. Owner wants scoped MSSP Sentinel runs, so this may matter beyond Sentinel. | Owner decision |
| G9 | Live Retail Prices API pricing per region and redundancy for saving estimates. | Emergent disk tool | Planned (PLAN M3, backlog 5), not built. Not new. | HTTP allowlist change (ADR) |

## 3. Deliberate non-goals (do not add)

| Capability | Seen in | Why not |
|---|---|---|
| Acting on resources: stop, delete, power schedules, remediation | OptScale, Cloud Custodian (via workshop) | Hard rule 1, recommend only |
| Deploying into the tenant: Logic App, runbook, Functions job API | ACORT, Emergent | Owner constraint: nothing deployed in the target tenant |
| LLM in the loop to explain findings | finops-agent | Sends customer data to a model; conflicts with privacy rules. Their rule "code decides, model explains" is sound, but this is a decision for the owner, not a default. |
| Recurring email reports | ACORT | Tool runs from a laptop, no hosting. Run-to-run diff (G2) covers the need without a service. |
| IaC scanning and pre-deployment cost estimates | PSRule, Checkov, Infracost | Different job (shift-left on code), not a tenant assessment |
| Multi-cloud, Kubernetes allocation, Databricks | OptScale | Azure only; sovereign clouds also out |

## 4. Where F-CAT is already ahead (from the READMEs read; not a ranking of quality)

- None of the Azure assessment scripts read describe a per-finding evidence trail, a self-audit of invariants, a "not assessed, because X" state, or offline golden tests. Their READMEs do not mention them (absence in a README is weak evidence).
- GCG and ACORT need cost or deployment rights up front; F-CAT is Reader-first with a permission probe (`fcat doctor`).
- Only the Foundation playbook and F-CAT's questionnaire treat maturity as evidence plus input. The other tools score waste only.

## 5. Caveats

- Everything in section 4 is relative to the READMEs, not the code.
- F-CAT checks are `offline-only` until G2 passes on a real tenant (hard rule 8). This note does not change that.
- Sources (all read 2026-10-21): the repos' own README and LICENSE files at the URLs https://github.com/{owner}/{repo}.
