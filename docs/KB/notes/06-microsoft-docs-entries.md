# File entries 1-22 (Microsoft docs): verification log (17 Oct 2026)
Fetch summaries are from a small summariser model. Re-open before quoting.

## 1 azure.com/solutions/finops: OPENED (note 04)
## 2 Learn FinOps Framework: OPENED (note 04). ms.date 2025-04-25, older capability names than finops.org
## 3 Toolkit overview: OPENED. ms.date 2025-04-02, meta-updated 2026-02-11. Lists hubs, Power BI, workbooks (Cost optimization, Governance), AOE, PowerShell, Bicep Registry modules, open data. "Monthly releases tracked as milestones" (contradicted in practice: tags show v13 then v14 only, Apr 2026 latest, so cadence is not monthly in 2026. Source: note 03)
## 4 Hubs overview: OPENED. ms.date 2026-04-01
- Design principles: Be the standard, Built for scale, Open and extensible. Data store ADX or Fabric RTI, ADLS Gen2 staging, Data Factory, Key Vault.
- Supported: EA, MCA, MPA (CSP via subscription exports), Azure Gov, 21Vianet. MOSA (PAYG) only in hubs 0.1.1; hubs 0.2+ need FOCUS exports that MOSA subscriptions do not support. Management group exports not supported for MCA or CSP (as of May 2024).
- Cost: from $120/mo + $10 per $1M monitored (ADX single node); Fabric F2 about $300; without ADX/Fabric $5 per $1M; about 20 GB per $1M.
- Permissions: deployer Owner or Contributor + RBAC Admin; exports Cost Management Contributor (sub/RG), Enterprise Reader/Department Reader/Account Owner (EA), Contributor on billing account/profile/invoice section (MCA).
- IMPORTANT for our design: PAYG/MOSA subscriptions cannot produce FOCUS exports. Our tool must use the Cost Management Query/Details API for those, not exports. (Derived from this page; MOSA export support in Cost Management itself still to verify.)
## 7 Hubs data model: OPENED. ms.date 2026-04-01
- Datasets: Costs, CommitmentDiscountUsage, Prices, Recommendations, Transactions. Recommendations columns: ResourceId, ResourceName, ResourceType, SubAccountId, x_EffectiveCostSavings, x_EffectiveCostBefore, x_EffectiveCostAfter, x_RecommendationDate, x_RecommendationId, x_RecommendationCategory, x_RecommendationDescription, x_RecommendationDetails (dynamic). Matches note on the 22 query JSONs; note x_EffectiveCostSavings/Before/After exist, so we can reuse these names in our JSON schema for hub compatibility.
- Schema: hub release 12+ uses v1_2 (FOCUS 1.2); 0.7-11 v1_0. r# suffix for revisions in a version.
## 6 Hubs deploy: OPENED. ms.date 2026-05-12
- Scopes: subscriptions, RGs, EA/MCA/MPA. MCA price sheet/reservation exports at billing profile level only. Exports: Parquet+Snappy to msexports container. Backfill order: price sheets, costs, reservations.
## 8 Hubs template: OPENED. ms.date 2026-04-13
- enableRecommendations default False; enableAHBRecommendations False; enableSpotRecommendations False (template default is OFF; v14 announcement said built-in queries on by default when enabled. Check: parameter default False means the feature itself is opt-in. DISCREPANCY in how I summarised note 03 ("Built-in queries on by default") vs this default, needs checking in template source).
- Storage Premium_LRS default; ADX Dev(No SLA) default; ADX required for Power BI above roughly $2-5M monthly cost (as stated). Managed exports not supported for MCA billing profiles.
## 9 Remote hubs: OPENED. ms.date 2024-11-01 (updated 2026-02-11). Cross-tenant by storage account key (full access). Min template 0.4. Relevance: hub multi-tenant pattern relies on shared keys; pinned multi-tenant idea for us should avoid that.
## 10 Implementing FinOps guide: OPENED. ms.date 2026-04-01. No maturity model, points to Framework and a "FinOps review assessment" on Learn assessments.
## 11 Cost Management best practices: OPENED. ms.date 2025-07-09. Stale items: legacy Consumption Usage Details link, AzureCon 2015 video, Batch low-priority VMs (superseded by Spot), claim "management groups aren't supported for MCA" (needs verifying), savings percentages (65/72/55 percent are marketing figures, verify)
## 12 VM cost optimisation best practices: OPENED. ms.date 2024-02-21. Dev/test tips (B-series, HDD, LRS, schedules), Premium SSD v2, Azure Policy ideas (allowed SKUs, no public IPs on NICs). Usable as rule ideas
## 13 Training: get-started-with-finops: OPENED, loads, 9 units incl. FinOps Maturity Model. ms.date 2024-11-22
## 14 Training: adopt-finops-on-azure: OPENED, loads, 8 units. ms.date 2025-07-21
## 15 Azure FinOps guide (techcommunity 3704132): PARTIAL. Only metadata returned, last modified 16 Sep 2025, body not seen, status of content UNVERIFIED
## 16 Learn FinOps docs hub: OPENED (note 04)
## 17 microsoft.github.io/finops-toolkit: OPENED (note 03)
## 18 Learn changelog: OPENED. Live page newest entry is v14 (April 2026), v13 Update 1 on 11 Feb 2026, v13 on 31 Jan 2026. NO v15 section. The file's claim "v15 in progress Oct 2026" is therefore unsupported by the live page. (Repo source docs have a v15 section marked June 2026; see note 03.)
Correction to note 03: hub Recommendations feature is OFF by default (enableRecommendations=false in hub.bicep). Fixed there.

(Numbering note: from here "U#" is my index of the 89 unique URLs extracted from the HTML, in file order. The HTML has 96 numbered entries, so numbers can drift from the file's own numbering by a few places. A URL register CSV will carry both.)

## U5 techcommunity Copilot + FinOps hubs guide (4420302): PARTIAL, body not retrievable. Metadata: modified 8 Jun 2025. Claims ~30 minutes basic setup (description only, unverified)
## U19 techcommunity FinOps-ready landing zone part 2 (4555727): PARTIAL, body not retrievable. Last modified 11 Sep 2026
## U20 techcommunity custom analyses with hubs (4408601): PARTIAL, body not retrievable. Modified 16 May 2025
## U21 azure.com blog "How Microsoft Cloud is embracing FinOps practitioners": OPENED. Published 27 Jun 2023 (Flanakin). STALE (FinOps X 2023 event, preview features, "AI assistant upcoming")
## U22 Learn sample finops-hub quickstart template: OPENED. ms.date 2025-05-08; older than hub releases v13/v14 (commit 58ed802), so use the repo, not this sample. Currency of the quickstart template UNVERIFIED
## U41 finops.org: OPENED. Newest: State of Tokenomics Sep 2026; FinOps X 2026 keynote; events London 8-9 Feb 2027, San Diego 7-10 Jun 2027. Tokenomics/AI focus
## U42 learn.finops.org: OPENED. Certifications: Practitioner, Professional, Engineer, FOCUS Analyst, Technology Value, AI Value. Prices as listed ($500 most, $400 FOCUS Analyst); not needed for tool
## U43 github.com/finopsfoundation: OPENED (first 10 of 20 repos visible). focus_converters (137 stars, MIT), focus_validator (41, MIT), focus_scrub (1, MIT), focus_converter_azure (3, MIT), framework (88), tac (49, Apache-2.0), definition (37, Apache-2.0). Counts from a single fetch, not independently checked. focus_converter_azure has 3 stars: low adoption, maintenance status UNVERIFIED
## U44 finops.org/members/microsoft: OPENED (note 04)

# URL register part 2: Microsoft OSS and community (U45-U59), fetched 17 Oct 2026
Stars, forks, commit counts from one fetch each. Last-commit dates were NOT shown by the fetch tool for any repo, so "actively maintained" is UNVERIFIED for all of them unless stated.
| U | Repo | Findings |
|---|---|---|
| 45 | microsoft/finops-toolkit | see notes 02, 03 (MIT) |
| 47 | Azure-Samples/azure-finops-agent | 23 stars, 14 forks, 352 commits, MIT, .NET 10 backend, Vue 3. README: replaces multi-week assessment, maturity score, CFO deck, "read and write on your behalf, never delete" (writes, so not read-only). In Azure-Samples org; "official Microsoft" not stated. The user's file claims 542+ commits: fetch shows 352 (CONTRADICTED, possibly a typo) |
| 48 | ms-sambell/azure-finops-workbook | 92 stars, 10 commits, licence not shown. Workbook: hybrid licence audit, tagging audit, storage/AKS/Log Analytics/orphans/Recovery Services/App Service/VM insights. Described as WIP example |
| 49 | dolevshor/azure-finops-guide | 215 stars, 89 commits, MIT. Curated links (not code) |
| 50 | finoops/Azure-FinOps-Top-Resources | 12 stars, 9 commits, one README. Lists PSRule Cost Optimisation, Cost CLI, Azure Cost Estimator, Infracost |
| 51 | julianobarbosa/azure-finops-mcp-server | 2 stars, 39 commits, MIT, Python 3.10+. Tools get_cost, run_finops_audit (stopped VMs, unattached disks, unassociated IPs) |
| 52 | pigottk4/finops-cost-management-azure | 0 stars, 4 commits, no licence. Terraform for budgets/policy. SECURITY FLAG: README reportedly points to a Windows desktop installer from an external site that does not match repo contents. Do not run; do not reuse |
| 53 | 9t29zhmwdh-coder/azure-cost-forecasting-engine | 0 stars, 55 commits, MIT, Python 3.11 stdlib only. Query API ingestion, forecast ensemble (linear + Holt), anomaly mean+2.5 sd, RI/rightsizing detection, HTML/JSON/MD output, needs Cost Management Reader. Looks genuine but brand new/unused; code not reviewed. Design reference only |
| 54 | andy-diericks/azure-pricing-radar | 1 star, 448 commits, MIT. Polls Retail Prices API every 6h. Page says developed autonomously by Claude Code agents. Data source idea for price history, not a dependency |
| 55 | CloudHiro/azure-finops | 1 star, 154 commits, no licence. ARM templates for runbooks/policies (AHB enforcement, VMSS autoscale, unused disk/deallocated VM cleanup, unused subscription detection). README anchors broken. Deploys actions, not read-only. Ideas only |
| 56 | finoops/FinOps-Cheatsheet | 10 stars, 10 commits, one README, no licence. Exam-prep glossary. No tool value |
| 57 | devopsabcs-engineering/finops-scan-workshop | 0 stars, 26 commits, MIT. Workshop combining PSRule for Azure (WAF Cost rules on IaC), Checkov, Cloud Custodian (orphans, tags, rightsizing), Infracost; SARIF output. Confirms PSRule.Rules.Azure and Cloud Custodian as useful rule sources |
| 58 | NakitaMei/azure-focus-pipeline | 0 stars, 2 commits, no licence. FOCUS validator that turns spec sentences into checks (166 checks claimed, 70 of 88 conditional rules implemented at 1.2). CLAIM TO VERIFY: "Azure's native export declares version 1.0r2". This conflicts with Microsoft docs naming 1.2-preview; unverified, from a 2-commit repo. Design reference for FOCUS conformance checks |
| 59 | hystax/optscale | about 2.2k stars, 2,143 commits, Apache-2.0, multi-cloud incl. Azure; page lists generic idle/rightsizing/commitment checks, does not confirm which apply to Azure. Needs deployment (platform) |
| 60 | opencost/opencost | 6.7k stars, 882 forks, Apache-2.0. Kubernetes-centred, Helm install. Azure non-K8s use not explained on page |
| 61 | kubecost/kubecost | EXISTS, not archived, 675 stars, Apache-2.0, 3,835 commits. File says it exists; relationship to OpenCost and licence terms of the commercial product NOT verified (repo licence may not cover the product) |
| 62 | cloud-custodian/cloud-custodian | 6.1k stars, 1.6k forks, Apache-2.0. YAML policies (resource, filters, actions, mode). Azure supported. Policy-as-data model is a reference for our checks-as-data format |

## Claim check against the user's file
- File says azure-finops-agent: "542 commits, MIT licensed, C#/.NET + Vue. Actively maintained by Microsoft." Fetched: 352 commits (not 542), MIT yes, .NET 10 + Vue 3 yes, "maintained by Microsoft" not stated (it is under Azure-Samples). The "542+" figure also appears against the toolkit entry in the file; toolkit commit count not checked.
| 63 | kubeshop/komiser | FETCH ERROR on first attempt (CLIENT_ERROR). Retried below |
| 64 | steampipe/steampipe | FETCH ERROR on first attempt. Retried below (org is turbot/steampipe) |
| 65 | infracost/infracost | 12.5k stars, Apache-2.0, 1,100+ resources across AWS/Azure/GCP. Pre-deployment estimator for IaC, not a live-estate scanner. Codebase split into other repos (infracost/cli). Pricing source not stated |
| 66 | project-koku/koku | 316 stars, 5,202 commits, licence file not named on page. Needs PostgreSQL, Trino, S3-like storage, Celery: a platform deployment. Azure support not claimed on page (an Azure downloader test path exists). Not suited |
| 67 | JGrubb/open-finops-stack | 13 stars, MIT. FOCUS-based pipeline; AWS CUR done, multi-cloud planned. Not Azure yet |
| 68 | turbot/powerpipe | 516 stars, AGPL-3.0 (plus commercial terms). Dashboards-as-code over SQL. Azure mods exist per page, Azure cost mod unconfirmed. AGPL matters if we embed |
| 69 | ManageIQ/manageiq | 1.4k stars, 49,759 commits, Apache-2.0. General hybrid IT management platform, not FinOps-specific, needs deployment |
| 70 | cleancloud-io/cleancloud | 119 stars, MIT, Python (inferred), 50 rules across AWS/Azure/GCP, read-only (List/Get/Describe only, per README). Azure checks: stopped VMs, unattached disks, old snapshots, unused public IPs, empty LBs and App Gateways, idle VNet gateways, empty App Service plans, idle SQL DBs, idle App Services, unused ACRs, untagged resources; opt-in AI/ML idle compute clusters, instances, online endpoints, AI Search, Azure OpenAI provisioned deployments. CLOSEST existing peer to our orphan/idle goal. Idle-SQL definition and cost estimate method not seen (READ SOURCE LATER) |
| 63/64 | komiser, steampipe | Steampipe via turbot/steampipe OPENED: 7.9k stars, 341 forks, AGPL-3.0 (+ Turbot commercial terms), Azure plugin exists; page says nothing about cost data. The file's URL steampipe/steampipe errored; the working org is turbot. Komiser (kubeshop and tailwarden URLs) errored twice: status UNVERIFIED, retry once more |
| 71 | mnshahab/finops-operating-system | 1 star, 148 commits, MIT. Docs/templates repo (KPI dictionary, maturity assessment, playbooks). Mixed complete/planned, README link inconsistencies. Could inform maturity questionnaire only after reading actual files (not read) |
| 72 | finopsfoundation/focus_converter_azure | 3 stars, 1 commit, MIT. Effectively an empty shell. The file points here for Azure conversion; real converter is in focus_converters |
| 73 | finopsfoundation/focus_converters | 139 stars, 179 commits (dev), MIT, AWS/GCP/Azure/OCI, 73 open issues. FOCUS version targeted not stated on page |
| 74 | pach-boop/tokencur | 0 stars, 66 commits, MIT. AI/LLM usage to FOCUS 1.2; claims passes Foundation validator in CI (unverified). No Azure OpenAI source. Not directly relevant |
| 75 | gregoire-costory/awesome-agentic-finops | 29 stars, 13 commits, CC0. Maintained by vendor Costory. Leads: msftnadavbh/AzurePricingMCP (MIT), mivano/azure-cost-cli, thgossler/AzSaveMoney, rowilson/azure-cost-management-pbit, TheCloudTheory/arm-estimator, mindaugasnakrosis/azure-costs-analyzer. NEW LEADS not in the user's file; each needs its own check |
| 79 | PacktPublishing/FinOps-Handbook-for-Microsoft-Azure | 12 stars, 18 commits, no licence shown, code samples for chapters 1-13; ISBN 9781801810166; publication date and edition not on page |

# URL register part 3: topics and blogs (U76-U89), fetched 17 Oct 2026
| U | Source | Findings |
|---|---|---|
| 76 | github.com/topics/azure-finops | OPENED. 6 repos listed. New leads: CloudMonitorFinOps/reporting (31 stars, Power BI FOCUS reports, updated 1 Sep 2026), mindaugasnakrosis/azure-costs-analyzer (4 stars, Python, read-only audit as a Claude Code skill via az CLI, updated 11 May 2026), JeyaPrakashI/Multi-Cloud-Governance-Ledger-FOCUS-1.3 (3 stars). Topic pages are listings, low authority |
| 77, 78 | github.com/topics/finops, /finops-foundation | Listing pages. Not opened separately yet |
| 80 | amnic.com FOCUS guide 2026 | OPENED. Dated 4 Jun 2026. Says current release is FOCUS 1.3 (ratified "Dec 4, 2025"; spec site says Dec 5) so it predates or misses 1.4 (ratified 4 Jun 2026). Azure support described as "up to 1.2". Vendor (Amnic) bias, several unsupported claims. LOW authority |
| 81 | medium @cocamatias FOCUS | OPENED. 20 Apr 2026. Says FOCUS 1.2 "defines 65 standardized columns": CONTRADICTED (65 is the 1.4 Cost and Usage count per spec page; 1.2 TOC shows 57). Author sells a related service. LOW authority |
| 82 | nops.io/blog/finops-focus | OPENED. Published 6 Sep 2024, modified 9 Feb 2026. Describes 1.0, FOCUS 1.1 "planned". STALE, vendor bias |
| 83 | varcio.com FOCUS guide | OPENED. 6 Oct 2026. Lists 1.0 to 1.3 only (no 1.4). Cites Amnic as source. Vendor bias. States rule "reconcile with BilledCost, analyze with EffectiveCost" (common practice, plausible) |
| 84 | holori.com FOCUS | OPENED. 5 Mar 2025, modified 4 Feb 2026. Says 1.2 upcoming June 2025 (it shipped 29 May 2025). STALE, vendor |
| 85 | yobitel.com FOCUS | OPENED. Updated 4 Jul 2026. Says 1.1 production, 1.2 late draft, Azure 1.0 GA with 1.1 preview: CONTRADICTED by Microsoft (1.2-preview) and by FOCUS site (1.4 ratified). UNRELIABLE |
| 86 | medium hkaanturgut toolkit | OPENED. 9 Mar 2026. Conceptual overview, no version details, cannot be checked against v14. Low value |
| 87 | prosperops.com Azure FinOps | OPENED. Published Aug 2025, updated Jul 2026. Vendor. Uses a 2020 Forbes waste stat and undated market share. Mentions reservation exchange advice that may be outdated (see below) |
| 88 | nops.io Azure FinOps | OPENED. Dates conflict (Mar 2026 / Apr 2026 / byline Oct 2026). Many unsourced/inconsistent stats. Vendor. Mentions "Microsoft Ends Azure Reservation Exchanges before Feb 2027" as a related post title: VERIFY on Microsoft Learn |
| 89 | osamaoracle.com Azure FinOps part 1 | OPENED. 12 Oct 2026. Practitioner opinion, no sources. Useful ideas only: 4-tag minimum schema (costcenter, owner, environment, application), deny-RG-without-tag, inherit tags via modify policy, unallocated cost bucket as KPI, budgets at 80 and 100 percent, anomaly detection everywhere. Treat as hypothesis, check against Microsoft docs |

## Retry results and verifications (17 Oct 2026)
- U63 Komiser: https://github.com/mlabouardy/komiser OPENED: 4.1k stars, 453 forks, 2,986 commits, licence Elastic License 2.0 (ELv2, NOT an OSI open-source licence; links to tailwarden/komiser). The file says kubeshop/komiser; that URL errored. Azure supported. Idle/untagged resource flags. Licence is a constraint for reuse: do not copy code; ideas only.
- Reservation exchange policy (Microsoft Learn, OPENED via Learn search; page reservation-exchange-policy-changes): from 1 Feb 2027, reservations bought after that date are not exchangeable if the service is supported by savings plans (VMs, App Service, SQL Database and similar); reservations bought before keep one final exchange; cancellation limit stays $50,000 in a rolling 12 months per billing profile or enrollment; trade-in to savings plans unchanged; renewals after 1 Feb 2027 count as new purchases and are not exchangeable. Partner Center notes customers get notifications from 30 Jul 2026. nOps/ProsperOps "exchange or cancel" advice is therefore time-limited. IMPLICATION for the tool: commitment recommendations must reflect this; reservations purchased before 1 Feb 2027 with poor utilisation have a closing window (today is 17 Oct 2026, so about 3.5 months).

## Final entries
- U46 github.com/microsoft/finops-toolkit/releases OPENED: v14 29 Apr 2026 (Latest), v13 31 Jan 2026, v12 17 Jul 2025, v0.11 2 Jun 2025, v0.10 5 May 2025. No v15. Confirms note 03. (v14 date on GitHub is 29 Apr 2026; Learn says "April 2026".)
- U77 github.com/topics/finops OPENED: 1,468 repos. Azure-relevant: mivano/azure-cost-cli (1.1k stars, C#, updated 20 Jul 2026), microsoft/finops-toolkit (591 stars, updated 5 Aug 2026), infracost, opencost, optscale, cloud-custodian. Peers to study: azure-cost-cli.
- U78 github.com/topics/finops-foundation OPENED: 2 repos: OptimNow/cloud-finops-skills (49 stars, knowledge pack + MCP server, updated 30 Aug 2026), admbe/FluxOp (2 stars).
- Note: the topic-page star counts come from a different snapshot than repo pages (e.g. OpenCost 6.7k both; Cloud Custodian 6k vs 6.1k). Treat star counts as approximate.
