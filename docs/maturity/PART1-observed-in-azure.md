# Maturity, Part 1: what the tool reads from Azure (DRAFT v0.2, owner-facing)
Rule used to split the questionnaire (owner, 2026-10-18): if it can be seen in the portal, CLI, PowerShell, Resource Graph or an API, the tool reads it and the owner reviews it. If not, it goes to the customer in Part 2.
Nothing here is asked of the customer. Evidence is existence and configuration, not how well it is used: a budget that exists says nothing about whether anyone reads it. Practice is covered by Part 2.
All signals below are DESIGN (unverified live). Billing-type limits: classic CSP and Sponsorship have no Cost Management data; CSP customers see cost only if the partner enables cost visibility.

| # | Capability (finops.org name) | What the tool looks at | Needs |
|---|---|---|---|
| 1 | Data Ingestion | Cost data available per subscription; exports configured; FOCUS export and its version | Cost Management Reader |
| 2 | Allocation | Tag coverage of resources and of cost; tag inheritance; allocation rules; management group structure | Reader, Cost Management Reader |
| 3 | Reporting and Analytics | Saved views or scheduled exports, where readable | Cost Management Reader |
| 4 | Anomaly Management | Anomaly or scheduled alerts configured | Cost Management Reader |
| 5 | Planning and Estimating | Nothing readable | none |
| 6 | Forecasting | Budgets with forecast-based thresholds | Cost Management Reader |
| 7 | Budgeting | Budgets per subscription or management group, thresholds, recipients | Cost Management Reader |
| 8 | KPIs and Benchmarking | Nothing readable | none |
| 9 | Unit Economics | Readiness only: product or application tags present | Reader |
| 10 | Architecting and Workload Placement | Legacy or Basic SKUs, old VM series (cost-relevant only) | Reader |
| 11 | Usage Optimization | Orphaned and idle resources, auto-shutdown, autoscale, Advisor cost backlog and age (peak-aware, R10) | Reader |
| 12 | Rate Optimization | Commitment coverage and utilisation, expiring commitments, Hybrid Benefit | billing or Reservations reader |
| 13 | Sustainability | Nothing planned (confirm against the workbook Sustainability tab) | none |
| 14 | Licensing and SaaS | Hybrid Benefit flags, marketplace spend | Reader, Cost Management Reader |
| 15 | FinOps Practice Operations | Nothing readable | none |
| 16 | Governance, Policy and Risk | Policy assignments for tags, SKUs, locations and their compliance; hierarchy depth | Reader |
| 17 | FinOps Assessment | Nothing readable | none |
| 18 | Automation, Tools and Services | Auto-shutdown, autoscale, lifecycle policies, scheduled exports | Reader |
| 19 | FinOps Education and Enablement | Nothing readable | none |
| 20 | Invoicing and Chargeback | Billing structure (invoice sections, profiles) | billing reader |
| 21 | Intersecting Disciplines | Nothing readable | none |
| 22 | Executive Strategy Alignment | Nothing readable | none |

Capabilities with "Nothing readable" are scored only from Part 2. Where both exist, the report shows both side by side and flags disagreement, for example "customer says budgets are reviewed monthly, but no budgets exist".
