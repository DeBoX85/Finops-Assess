# Initial links: verification notes (17 Oct 2026)

Status words: OPENED = page content read via fetch; summaries below come from a fetch tool that summarises pages with a small model, so exact wording and numbers should be re-checked against the page before being quoted in a deliverable.

## Microsoft FinOps toolkit and docs

### Azure Optimization Engine overview (Learn, OPENED)
URL: https://learn.microsoft.com/en-ie/cloud-computing/finops/toolkit/optimization-engine/overview
Dates: ms.date 2026-04-01, "last updated" 2026-04-01, metadata updated_at 2026-05-18.
- Recommendation areas: Cost, High availability, Performance, Security, Operational excellence.
- Cost list: augmented Advisor VM right-sizing (fit score from guest OS metrics), underused VMSS, premium SSD disks, App Service plans, SQL DBs (DTU SKUs only), orphaned disks and public IPs, Standard LBs / App Gateways without backend pool, long-deallocated VMs, storage accounts without retention policy, empty App Service plans, stopped (not deallocated) VMs.
- Non-cost but useful for assessment: service principal credentials without expiry or expiring, NSG rules pointing to empty subnets / orphaned NICs / orphaned public IPs, RBAC assignment limits, resource group limits, empty or wasteful subnets, Basic LBs without backend pool, VM availability zone / set structure.
- Data sources: Advisor, Azure Monitor agent guest metrics (Perf table), raw exports in storage, resource configuration, optional Entra ID, optional EA/MCA billing data, Azure Policy compliance. ARG not listed as a source on this page (appears only under related products).
- Architecture: storage account, Log Analytics workspace, Automation (managed identity), Azure SQL database (1 year history, suppressions), workbooks, Power BI report. Weekly refresh, data about 3 hours after deploy.
- Permissions: deployer needs Owner on subscription; managed identity gets Reader on subscription; optional Global Reader in Entra (needs Privileged Role Administrator), optional EA Enrollment Administrator / MCA Billing Profile Owner for commitments.
- Cost to run: NOT STATED on the page.
- Implication: AOE requires a deployment in the customer tenant, so it conflicts with the "nothing deployed" constraint. Its check list is a useful catalogue; v14 announcement says AOE capabilities are migrating into FinOps hubs.

### Open data (Learn, OPENED; site page OPENED)
URLs: https://learn.microsoft.com/en-ie/cloud-computing/finops/toolkit/open-data and https://microsoft.github.io/finops-toolkit/open-data
Learn: ms.date 2026-04-04, updated 2026-05-18. Site page: v14 (April 2026).
- Datasets: Pricing units, Regions, Resource types (CSV and JSON), Services, Commitment discount eligibility (new in v14, weekly via GitHub Actions from Retail Prices API), dataset examples (zip, EA demo account, includes FOCUS 1.0 and 1.0-preview(v1)), dataset metadata (zip, FOCUS 1.0 and 1.0-preview(v1)).
- Download pattern: https://github.com/microsoft/finops-toolkit/releases/latest/download/<File>
- PowerShell equivalents: Get-FinOpsPricingUnit, Get-FinOpsRegion, Get-FinOpsResourceType, Get-FinOpsService.
- Update frequency and preview/GA status are not stated except commitment eligibility weekly. Remember the earlier finding: eligibility columns were swapped in a bug (#2279), so validate before use.
- Use for us: region name normalisation, service to FOCUS ServiceCategory mapping, resource type display names. All usable offline if bundled (MIT, attribution).

### FinOps hubs, AOE, workbooks, azure.com FinOps, finops.org member page, Learn overview/framework (OPENED earlier)
- Hubs site: pricing from about $120/month plus $10/month per $1M monitored spend (as stated on the page); needs Microsoft.CostManagementExports and Microsoft.EventGrid providers. Supports the argument that a hub is a deployment we avoid.
- AOE site page: PowerShell deployment, Log Analytics workspaces; no relation to hubs stated (the v14 announcement does state migration).
- azure.com/solutions/finops: lists Cost Management, Azure Copilot, Fabric, Advisor, Policy, Monitor, Migrate, Foundry, Carbon optimization; no date; mentions a Forrester TEI (June 2025).
- finops.org Microsoft member page: says Microsoft supports FOCUS and lists "FOCUS 1.2 in Microsoft Cost Management: July 2, 2025"; lists a FinOps Review Assessment.
- Learn FinOps overview ms.date 2026-04-01. Learn framework page ms.date 2025-04-25: 4 domains, 22 capabilities with older names; Crawl-Walk-Run maturity per capability on knowledge, process, metrics, alignment, automation; reassess every 3 to 6 months. Microsoft says it "largely follows" the FinOps Framework with enhancements.
- Cost Management hub lists EA, MCA, individual accounts; no dedicated exports article in that hub listing.
- Copilot in Cost Management blog (techcommunity 3887800): page body not retrievable, only a 2023-08-01 modified date. Current Copilot status UNVERIFIED.

## FOCUS and Azure

### FOCUS data generator page, Microsoft Azure (OPENED)
URL: https://focus.finops.org/docs/implementation/data-generators/microsoft-azure/
- States "FOCUS Version Supported: v1.2".
- Enable via the FOCUS export template in Cost Management exports; 7 years of history can be exported in FOCUS format (as stated there).
- Conformance Summary and Full Report exist on Learn (cloud-computing/finops/focus/conformance-summary, conformance-full-report) listing known gaps versus the 1.2 spec. Gaps NOT listed on this page. TO READ.
- Page cites a blog saying FOCUS 1.0 exports also exist and does not reconcile the two.

### Cost and usage details (FOCUS) schema (Learn, OPENED)
URL: https://learn.microsoft.com/en-us/azure/cost-management-billing/dataset-schema/cost-usage-details-focus
Dates: ms.date 2025-06-26, metadata updated_at 2025-10-09.
- Versions documented: 1.2-preview (105 columns), 1.0 (96), 1.0-preview(v1) (94), plus 1.0r2 (date format now includes seconds).
- 1.2-preview columns currently null/empty: CapacityReservationId, CapacityReservationStatus, CommitmentDiscountQuantity, CommitmentDiscountStatus, CommitmentDiscountUnit, SkuPriceDetails.
- x_SkuMeterName deprecated for SkuMeter; x_SkuDetails to be removed when SkuPriceDetails is ready.
- Billing account types supported: not enumerated on this page.
- DISCREPANCY: Azure's own schema page says 1.2-preview, finops.org says v1.2, finops.org member page says "FOCUS 1.2 in Microsoft Cost Management: July 2, 2025". Earlier research said FOCUS 1.4 was ratified 4 Jun 2026. So Azure export is behind the spec by at least two versions (needs confirmation against focus.finops.org specification page). Conclusion: our tool must not assume FOCUS 1.4 columns exist in Azure exports.

### azure.com blog: FOCUS, a new specification (OPENED)
Published 26 Oct 2023 (modified 12 Jun 2025). Historical. Describes FOCUS 0.5 era and says Microsoft planned FOCUS support after 1.0. STALE, useful only as history.

### azure.com blog: Democratizing FinOps with FOCUS and Fabric (OPENED)
Published 28 Nov 2023 by Michael Flanakin (modified 12 Jun 2025). Recommends exports to Fabric, FOCUS, FinOps Framework. Does not mention hubs. Preview and "coming months" statements are STALE.

### FinOps Framework on finops.org (OPENED)
URL: https://www.finops.org/framework/
- Domains and capabilities (current naming): Understand Usage and Cost (Data Ingestion, Allocation, Reporting and Analytics, Anomaly Management); Quantify Business Value (Planning and Estimating, Forecasting, Budgeting, KPIs and Benchmarking, Unit Economics); Optimize Usage and Cost (Architecting and Workload Placement, Usage Optimization, Rate Optimization, Licensing and SaaS, Sustainability); Manage the FinOps Practice (Executive Strategy Alignment, FinOps Practice Operations, Governance Policy and Risk, FinOps Education and Enablement, Invoicing and Chargeback, FinOps Assessment, Automation Tools and Services, Intersecting Disciplines).
- Count here is 4 + 5 + 5 + 8 = 22 (counted by me from the fetch summary; the summary did not state the total).
- "2026 Framework Updates: Executive Strategy Alignment, Refining Scopes" (20 Mar 2026) listed. Whether Executive Strategy Alignment is new or renamed is NOT STATED.
- Licence: CC BY 4.0, attribution to the FinOps Foundation required.
- Maturity: Crawl, Walk, Run.
- Mapping implication: Microsoft Learn naming is older than finops.org naming. The assessment should use finops.org names as primary and keep a mapping to the Learn names.

## Open questions from this batch
1. Exact FOCUS version Azure exports by default and which versions are selectable in the export wizard.
2. Content of Microsoft's FOCUS conformance reports (known gaps).
3. FOCUS 1.4 ratification and contents (check focus.finops.org specification).
4. Whether Copilot in Cost Management still exists in the same form.
5. AOE running cost.

## Addendum: FOCUS conformance and spec versions (17 Oct 2026)

### Microsoft FOCUS conformance summary (read in full from repo source docs-mslearn/focus/conformance-summary.md, ms.date 04/01/2026)
- Scope: Cost Management "FOCUS 1.2-preview" dataset versus the FOCUS 1.2 spec. Conformance score stated: 94%.
- Missing data (workarounds given by Microsoft): ContractedUnitPrice/ContractedCost are 0 for EA Marketplace, EA reservation usage with cost allocation, and all MCA reservation usage; ListCost is 0 for EA/MCA Marketplace and reservation usage (join with price sheet); SkuId/SkuPriceId null for savings plan unused and Marketplace; PublisherName null for reservation usage, purchases, savings plan unused; InvoiceId unsupported for EA; ChargeDescription null in some cases; ServiceName empty for EA Marketplace purchases and some MCA purchases/credits; CapacityReservation*, CommitmentDiscountQuantity/Unit and SkuPriceDetails not populated; AvailabilityZone absent.
- Inconsistent data: SkuPriceId does not identify a single price; CommitmentDiscountId case differs from lowercased ResourceId; ResourceName case may vary.
- Implication for us: ListCost cannot be taken from the FOCUS export for reservation usage or Marketplace, so list-price savings need a price sheet or Retail Prices join. Directly supports the user's "actual vs list" requirement.
- Full report is 198 KB at docs-mslearn/focus/conformance-full-report.md (not yet read in full).

### FOCUS specification page (https://focus.finops.org/focus-specification/, OPENED, summarised by fetch tool)
- Versions listed: v1.4 (latest), v1.3, v1.2, v1.1, v1.0, v0.5. No release dates on the page.
- v1.4 content: 4 datasets: Cost and Usage (65 columns), Billing Period (6), Contract Commitment (30), Invoice Detail (22); 23 supported features; 15 attributes; 4 metadata sections.
- Changelog not read, so "what is new in 1.4" is still UNVERIFIED. The 4 Jun 2026 ratification date from earlier research is NOT confirmed by this page.
- The user's file claim that FOCUS 1.4 adds AI/ML cost columns: NOT confirmed here.
