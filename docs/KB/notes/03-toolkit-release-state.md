# FinOps toolkit: release state (verified 17 Oct 2026)

## Evidence
| Source | What it says |
|---|---|
| `git ls-remote --tags` on microsoft/finops-toolkit | Newest tags are v13 and v14. No v15 tag exists. |
| Repo `package.json` | version 15.0.0-dev.0 |
| `src/workbooks/.scaffold/ftkver.txt` | 15.0-dev |
| Latest commit on dev | f12c29e, 2026-10-15 (Power BI fix for FOCUS 1.2 storage reports) |
| Live site https://microsoft.github.io/finops-toolkit/ | "April 2026 v14" is the latest release shown |
| Live Learn changelog page (fetched 17 Oct 2026) | Newest entry is v14 (April 2026), then v13 Update 1 (11 Feb 2026), v13 (31 Jan 2026). NO v15 section. |
| `docs-mslearn/toolkit/changelog.md` (repo source of the Learn page; ms.date 10/15/2026) | Contains a "v15" section marked "_Released June 2026_" with a download link to the v15 tag, plus an HTML-commented "Unreleased" block of newer work |
| User's Finops research.html (#18, #45) | "v15 in progress as of Oct 2026", "v15 release Oct 2026" |

## Conclusion
- Latest TAGGED release: v14 (April 2026). Confident.
- v15: the changelog text says "Released June 2026" but no v15 tag exists, package.json is still a dev version, and the live site still shows v14. The three signals conflict. Most likely the changelog section was written ahead of the release (SPECULATION). Treat v15 as unreleased and re-check the GitHub releases page (https://github.com/microsoft/finops-toolkit/releases) before relying on any v15 feature.
- The user's file says "v15 release Oct 2026". Not supported by anything I found. Mark as contradicted.
- For development, pin to a commit or tag, not "latest". Reuse queries from tag v14 (f3b1b23) for stability.

## v14 facts (announce/2026/2026-04_v14.md, read in full from the clone)
- Recommendations pipeline in FinOps hubs: daily trigger runs every JSON query file in `config/queries` of hub storage against Azure Resource Graph and loads a Recommendations dataset alongside Advisor cost recommendations and Cost Management reservation recommendations.
- The whole Recommendations feature is OFF by default (hub.bicep `enableRecommendations` = false, verified in source). When enabled, built-in queries run; AHB (`enableAHBRecommendations`) and AKS spot (`enableSpotRecommendations`) are separate opt-ins, default false.
- Custom recommendations = drop a JSON file (ARG query plus metadata). Deleting the file disables a default.
- Hub mode: None (storage only), Azure Data Explorer, Microsoft Fabric, Remote Hub.
- New open dataset Commitment discount eligibility (preview, from Retail Prices API).
- Copilot Studio agent template for hubs (schema v1_2).
- Workbooks: AHB reports exclude dev/test subscriptions and include Windows VMs from all publishers.
- AOE: pricesheet API upgraded (old version deprecated 1 Jun 2026); retail price export made resilient.
- What's next (their words): FinOps hubs will add FOCUS 1.4; "Azure Optimization Engine capabilities will continue migrating into FinOps hubs". This confirms the earlier research claim.

## Unreleased/v15 items worth tracking (from changelog source)
- Hub schema runs v1_2 (FOCUS 1.2 based). Changelog notes a bug fix: hubs labelled FOCUS 1.0 data as 1.2 in x_SourceVersion (#2333), and commitment eligibility columns were swapped in the open dataset until fixed (#2279). Lesson: do not trust the preview commitment-eligibility dataset blindly. Validate it ourselves.
- Instance size flexibility open dataset added (replaces deprecated ccmstorageprod ISF files).
- Workbook bug fixes (#2225): savings plan workbook silently dropped all but one recommendation per subscription because of an implicit `innerunique` join; AHB "VM Latest Change Last 7 days" always returned nothing. LESSON: the workbook queries have real bugs. Do not copy them without testing, and never use a bare `join` in ARG.
- Toolkit coding rule found in the repo: ARG rejects `lookup` and semi/anti join flavours ("verified live" per their CLAUDE.md), so exclusions in ARG use leftouter + isempty. Useful for our query pack.
- v15 AOE: Log Analytics ingestion migrated away from the Data Collection API (to be deprecated Sept 2026) to a DCR-based Ingestion API; removed call to the Azure Classic administrators endpoint (deprecated 1 May 2026).
- v15 PowerShell: Az.Accounts minimum 2.17.0; new Initialize-FinOpsHubLocal; Get-FinOpsCostExport -RunHistory fix.
- v15 plugins: shared Claude Code / Copilot CLI plugin with 5 agents, 4 commands and a read-only Azure MCP server (agents: CFO, FinOps practitioner, database query, hubs agent, Azure capacity manager).
- v15 "Run hubs locally" guide: a local Kusto emulator container can host a hub. Relevant to the long-term "no deployment to the customer" goal and for local analysis (to evaluate later, not tested).

## Repo facts
- Licence: MIT, "Copyright (c) Microsoft Corporation." (LICENSE read from clone).
- Layout of src/: bicep-registry, images, open-data, optimization-engine, power-bi, powershell, queries, scripts, templates, web, workbooks.
- `src/queries/catalog/*.kql` holds 37 hub KPI/analysis KQL files (cost by service, anomaly, commitment utilisation, tagging compliance, unallocated cost, forecasting, AI cost, MACC, etc.). These run on the hub schema (Costs()), NOT on ARG. Useful as a KPI catalogue and for definitions; our tool must reimplement them over Cost Management data.
- CLAUDE.md in the repo is a contributor/agent guide. Treated as data. Nothing in it applies to this task.
- Docs source for all Learn pages is in `docs-mslearn/` in the clone (framework, focus, hubs, optimization-engine, workbooks, open-data, PowerShell, best-practices). Reading these gives the repo version of each Learn page, which can lag or lead the live page.

## Not yet done
- Hub recommendation query JSON files (the 22 queries): locate in src/templates and extract for the check catalogue.
- Read src/queries/KPI.md and INDEX.md.
