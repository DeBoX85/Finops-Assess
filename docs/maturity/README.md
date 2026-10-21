# Maturity questionnaire: v0.2 (2026-10-18)
- PART1-observed-in-azure.md: owner-facing; what the tool reads automatically.
- PART2-customer-questions.md: send as is to the customer. 13 plain-language questions, three answers (Crawl, Walk, Run in plain words) plus "Not sure".
## Scoring (design, simplified at owner request)
Answer A, B, C maps to Crawl, Walk, Run. "Not sure" is recorded as needs input, never as zero. Each question maps to capabilities (below); a capability with no evidence and no answer shows "needs input / pending". No percentage cut-offs. The five-lens 0 to 4 scoring from finops.org (Knowledge, Process, Metrics, Adoption, Automation) stays available as an optional deep mode for a later iteration.
Why: finops.org defines Crawl, Walk and Run qualitatively and says the goal is never Run everywhere; Walk can be right. Microsoft advises starting with a lightweight, self-guided assessment on a few capabilities and reassessing (Learn says 1 to 3 months on the assessment page and 3 to 6 months on the framework page; the sources disagree). I found no official numeric cut-offs, so I dropped my 40/70 placeholders.
## Question to capability map
Q1 Practice Operations, Executive Strategy Alignment. Q2 Executive Strategy Alignment, KPIs and Benchmarking. Q3 Planning and Estimating, Architecting and Workload Placement. Q4 Forecasting, Budgeting. Q5 Allocation, Invoicing and Chargeback. Q6 Anomaly Management. Q7 Unit Economics, KPIs and Benchmarking. Q8 Usage Optimization, Sustainability (partial). Q9 Rate Optimization, Licensing and SaaS. Q10 Governance, Policy and Risk. Q11 FinOps Education and Enablement. Q12 Intersecting Disciplines, Sustainability. Q13 Reporting and Analytics, Data Ingestion, Automation Tools and Services, FinOps Assessment.
One question covers several capabilities, so this is a screening level, not a full assessment. Known weakness: a single answer cannot separate, for example, Budgeting from Forecasting. UNVERIFIED design.
## Sources (read 2026-10-18)
finops.org/framework/domains (22 capabilities), finops.org/wg/finops-assessment (0 to 4 on five lenses), finops.org/framework/maturity-model (Crawl/Walk/Run definitions), Learn framework and assessment pages.

## Target level per capability (backlog 36, owner agreed 2026-10-21)
`fcat maturity INPUT.toml --out DIR` (src/fcat/maturity.py) reads the customer's answers plus optional owner-set targets and writes maturity.json and maturity.md. Offline, no Azure access.
```
[answers]   # q1..q13, A = Crawl, B = Walk, C = Run, D = Not sure
q4 = "B"
q6 = "D"
[targets]   # optional, capability name (case-insensitive) = crawl | walk | run
Budgeting = "run"
```
Rules: a capability's current level is the LOWEST level among its answered questions (cautious); no answered question means "needs input"; "Not sure" is never scored as zero; no default target is invented, because finops.org says the goal is not Run everywhere; status is below, meets, above, no target or needs input. Levels come from answers only. Folding Azure scan evidence into the levels is a separate step that needs the PART1 mapping reviewed by the owner (UNVERIFIED design).
