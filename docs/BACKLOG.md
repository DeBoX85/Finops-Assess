# Backlog: work that needs NO tenant access (2026-10-17)
Order is my proposal. [needs you] marks items where a decision from the owner changes the work.
1. [needs you] ADR 0004 (proposed): where check logic lives. KQL-only logic cannot be tested offline. Proposal: KQL does coarse selection, Python applies precise rules and exclusions on projected properties, so rules are unit-testable and auditable. Costs more data transfer. Decide, then refactor ORPH-DISK-01.
2. Output audit Layer A: finding fingerprints and evidence fields, invariants checker, Audit section/sheet, reproducibility hash (docs/AUDIT.md).
3. Synthetic estate + golden report (approval tests).
4. Cost data research and collectors: Cost Management Query/Exports/Details API versions, scopes by billing type, rate limits, dimensions; fixtures from documented schemas.
5. FOCUS ingestion and normalisation (1.2-preview columns, known gaps), list-price join design (Retail Prices API), savings maths with golden tests (actual vs list).
6. Billing account type detection research (EA, MCA, CSP, PAYG; Billing API 2019-10-01-preview status is an open item).
7. More orphaned/idle resource checks ported from the 23 hub queries (MIT, notices kept) and AOE list, with fixtures; read azqr rule catalogue for parity.
8. Phase 0 parity matrix: azqr rules vs hubs vs AOE vs workbooks vs Advisor (offered earlier, not built).
9. Monitoring/security modules: collectors and checks from note 09 (Log Analytics, App Insights, Sentinel, Defender); check which properties ARG exposes; fixtures.
10. Maturity rubric draft: finops.org capabilities mapped to evidence, with "needs input" items and questionnaire [needs you to review].
11. HTML dashboard design (light/dark, print to PDF, per-customer tailoring options like logo, colours, sections) and PDF render check with headless Chromium [needs you for branding/taste].
12. `fcat doctor` permission probe design; customer-facing "access we need and why" generated from the check catalogue.
13. Threat model and privacy review of the tool (what it collects, where it stores it, retention, handling of outputs).
14. THIRD_PARTY/NOTICE audit of everything reused.
15. Remaining research: FOCUS 1.4 changelog, conformance full report, Cost Management api-version status, Copilot in Cost Management status, Reddit sentiment (blocked).
Needs the tenant: G2 live gate, canary resources, Reader-only workspace query test, precision sampling, oracle parity runs, contract recordings.
