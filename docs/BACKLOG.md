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

## Added 2026-10-17 (owner requirements)
- 16. Report tailoring config: branding (logo, colours, name, per-run override for external collaborators), module on/off, module weight and ranking. Owner-set only. Affects HTML/Excel/JSON length and style; JSON keeps full data.
- 17. Auth risk test: AzureCliCredential and MFA/conditional access on CSP and MCA test tenants (claims challenge unsupported). Needs tenant.
- 18. Billing-type specifics for CSP and MCA (Azure for Startups type): which Cost Management APIs and scopes work. Research first, verify on Learn.
- 19. FOCUS file import: `fcat import-focus <folder|file>` reads a customer-provided cost export offline (no Azure permissions). Fits the no-write rule. Design first.
- 20. Dashboard mock-ups (2 to 3 variants) with editable branding/scope/layout config. Owner agreed, taste review after.
- 21. Maturity questionnaire draft for owner review BEFORE implementation (owner request 2026-10-18).
- 22. Extra accuracy tests (owner request 2026-10-18): runtime invariants and completeness counters; property-based tests per check; metamorphic tests; cross-source reconciliation (Advisor/azqr/cost totals); schema-drift detection on collector output; recorded-response contract tests (after tenant). Add to AUDIT.md.
- 23. ADR 0005 export write mode: finish design after owner decision; implement only after levels 1 and 1.5.
- 24. Right-sizing/idle checks (R10): peak-aware logic design, fixtures with spiky workloads (low average, high peak must NOT be flagged). Research how Advisor and AOE choose windows and statistics.
- 25. Live-testing setup decision (before G2): where the tool runs (owner laptop), whether Claude Code runs locally for live sessions, and what customer output may enter a Claude session (confidentiality / NDA check by owner). Write docs/LIVE-TESTING.md after the decision.
- 26. Cost collectors (item 4) implementation waits for ADR 0006 sign-off. Meanwhile: design collector outputs and FOCUS import (item 19) which need no allowlist change.
