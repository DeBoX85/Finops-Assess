# Maturity questionnaire: DRAFT v0.1 for owner review (2026-10-18)
Status: DRAFT. Nothing is built on this yet. Everything marked "design" is my proposal, not a standard.

## Sources and what is verified
- Capability names and the 4 domains / 22 capabilities: finops.org/framework/domains/ (read 2026-10-18). VERIFIED. Content is CC BY 4.0, attribution required in the product.
- Scoring idea: finops.org/wg/finops-assessment/ (read 2026-10-18): each capability is scored 0 to 4 on five lenses (Knowledge, Process, Metrics, Adoption, Automation), as a percentage of 20, with an optional target score per capability. VERIFIED. That page does not describe Crawl/Walk/Run.
- Discrepancy: Microsoft Learn's framework page lists the lens "alignment" where finops.org lists "adoption" (Learn page ms.date 2025-04-25, KB note 04). Using finops.org as canonical.
- Everything below (questions, anchors, Crawl/Walk/Run cut-offs, evidence signals) is my DESIGN and UNVERIFIED against any real engagement.

## How scoring would work (design)
1. Each capability has 2 to 3 questions. Each answer is 0 to 4 plus "don't know" and "not applicable". Anchors for every question: 0 none, 1 ad hoc, 2 defined but partial, 3 consistent, 4 optimised/automated.
2. Each question is tagged with a lens. A capability's score is the mean of its answered questions per lens, shown as a percentage. Lenses with no answers are "not assessed".
3. Where the tool has technical evidence, it is shown NEXT to the answer, never silently replacing it. If the answer and the evidence disagree, the report flags the gap ("answered 3, evidence suggests 1: tag coverage 22%").
4. Crawl/Walk/Run (design): Crawl under 40%, Walk 40 to 69%, Run 70% or more of the capability maximum, only when at least 3 lenses are answered. Cut-offs are placeholders to be tuned.
5. Targets: you can set a target per capability (finops.org suggests a target may be below maximum). Gap to target is what the report highlights.
6. Never blended into a single overall tenant score. Show domain and capability level. Technical-evidence scores can be shown per subscription and management group; questionnaire answers apply at tenant or management group level.
7. Tool reports coverage: "X of 22 capabilities have any evidence, Y have answers".

## Capabilities, evidence signals, and questions
Legend: Auto = what the tool could read from Azure (read-only), with billing-type limits. Q = question for you or the customer, with lens in brackets.

### Understand Usage and Cost
1. Data Ingestion. Auto: Cost Management data available per subscription (not for classic CSP or Sponsorship); scheduled exports present; FOCUS export present and its version. Q: How is cost data collected and kept beyond what the portal shows? [Process]. How complete and trusted is it (all subscriptions, marketplace, shared services)? [Metrics]
2. Allocation. Auto: tag coverage % of resources and of cost; tag inheritance setting; cost allocation rules; management group structure. Q: Is there an agreed allocation model (who pays for what)? [Process]. What share of cost is allocated to an owner? [Metrics]
3. Reporting and Analytics. Auto: little (saved views and scheduled alerts only if readable). Q: Who gets which cost reports, how often? [Process]. Are reports used in decisions? [Adoption]
4. Anomaly Management. Auto: anomaly/scheduled alerts configured (Scheduled Actions). Q: Is there a defined way to detect, triage and resolve cost anomalies? [Process]. How fast are they handled? [Metrics]

### Quantify Business Value
5. Planning and Estimating. Auto: none. Q: Are costs estimated before deploying workloads? [Process]. Is the estimate compared with actuals afterwards? [Metrics]
6. Forecasting. Auto: budgets that use forecast thresholds. Q: Is spend forecast, by whom, how often? [Process]. How accurate (compare forecast vs actual)? [Metrics]
7. Budgeting. Auto: budgets per subscription/management group, thresholds, notification recipients, action groups. Q: Are budgets owned and reviewed? [Process]. Are budget breaches acted on? [Adoption]
8. KPIs and Benchmarking. Auto: none. Q: Which cost KPIs are tracked? [Metrics]. Are they compared with targets or peers? [Knowledge]
9. Unit Economics. Auto: readiness only, such as product/application tags. Q: Is cost tied to a business unit (per customer, per transaction)? [Metrics]. Used for decisions? [Adoption]

### Optimize Usage and Cost
10. Architecting and Workload Placement. Auto: limited, such as legacy/Basic SKUs and old VM series (cost-relevant only). Q: Are cost and efficiency part of architecture reviews? [Process]. Is region/placement chosen with cost in mind? [Knowledge]
11. Usage Optimization. Auto: orphaned resources, stopped/idle resources, auto-shutdown on non-production, autoscale, Advisor cost backlog and its age. Q: Is there a regular process to act on waste? [Process]. Who owns clean-up, and how often is it done? [Adoption]. Right-sizing decisions look at peaks, not averages (R10). [Knowledge]
12. Rate Optimization. Auto: reservation and savings plan coverage and utilisation, expiring commitments, Hybrid Benefit usage. Q: Who owns commitment decisions and the review cycle? [Process]. Is there a target for coverage? [Metrics]
13. Sustainability. Auto: none planned (to confirm after reading the workbook Sustainability tab). Q: Is emissions/efficiency considered with cost? [Knowledge]
14. Licensing and SaaS. Auto: Azure Hybrid Benefit flags, marketplace spend, support plan spend (billing-type limits). Q: Is licence entitlement tracked and applied? [Process]. SaaS spend visibility? [Metrics]

### Manage the FinOps Practice
15. FinOps Practice Operations. Auto: none. Q: Is there a defined FinOps team or recurring review with named roles? [Process]. Does it meet regularly? [Adoption]
16. Governance, Policy and Risk. Auto: Azure Policy assignments (allowed SKUs/locations, required tags, tag inheritance) and compliance, management group hierarchy depth, default management group use. Q: Are cost policies agreed and enforced? [Process]. How are exceptions handled? [Adoption]
17. FinOps Assessment. Auto: none. Q: Is maturity assessed on a schedule and acted on? [Process]
18. Automation, Tools and Services. Auto: auto-shutdown schedules, autoscale, lifecycle management policies, automated exports. Q: How much of reporting and clean-up is automated? [Automation]. Which tools are used? [Knowledge]
19. FinOps Education and Enablement. Auto: none. Q: Do engineers and finance understand cloud cost basics? [Knowledge]. Is there training or onboarding? [Process]
20. Invoicing and Chargeback. Auto: billing structure (invoice sections, billing profiles) if billing read access is granted. Q: Are invoices reconciled and costs charged back or shown back? [Process]. Disputes handled how? [Metrics]
21. Intersecting Disciplines. Auto: none. Q: Do FinOps, security, ITAM, procurement and sustainability teams work together? [Adoption]
22. Executive Strategy Alignment. Auto: none. Q: Do executives sponsor and review cloud cost goals? [Adoption]. Are cost targets tied to business strategy? [Alignment with strategy: Knowledge]

## Decisions I need from you on this draft
1. Is two questions per capability the right depth, or do you want fewer/more?
2. Do you answer all of it, or should some questions be marked "customer to answer"?
3. Crawl/Walk/Run cut-offs (40% / 70%): keep as placeholders?
4. Should capabilities with no technical evidence and no answer appear as "needs input" in the report (my default)?
