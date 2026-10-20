# Decisions and reviews waiting for the owner (parked 2026-10-18)
Owner is away from the next few steps. Rules while items are pending:
1. Do not ask the owner; keep working on anything that does not depend on an item below.
2. Where work needs an assumption, use the DEFAULT in the table, mark the code or doc "provisional: see DECISIONS-PENDING #n", and keep it cheap to change (config value or one function).
3. Anything provisional is not used for a customer deliverable until the item is closed.
4. Never act on items that touch security boundaries or Azure (#3 allowlist, #6 live setup) without the owner. Build around them.
5. Remind the owner at the next natural stopping point, or when the owner is back, with this file. When an item is decided, move it to "Closed" with the date.

| # | Item | What I need | Default I use meanwhile | What it blocks | Cost if default is wrong |
|---|---|---|---|---|---|
| 1 | Maturity questionnaire v0.2 (docs/maturity/PART1, PART2, README) | Wording review of the 13 customer questions; confirm the owner/customer split; confirm A/B/C = Crawl/Walk/Run scoring | v0.2 as written | Implementation of maturity scoring and its report section (backlog 21) | Low: wording and mapping live in data files |
| 2 | Confidence-label rule | Agree: "high" needs >= 90% correct on >= 30 audited findings across >= 2 environments; else capped at "medium" | Rule as proposed (docs/AUDIT.md section 4) | Setting any check to "high" in a customer report | Low: one threshold table |
| 3b | ADR 0006 stage 2: Cost Details report and blob download | Confirm no side effects beyond a temporary report (I will check the REST reference first), then OK | Stage 1 only (Query, Forecast) | Row-level cost data (resource-level cost, tags) | Low |
| 4 | Test tenant facts | CSP tenant: Azure plan (MCA via partner) or classic CSP, cost visibility policy on? Startups subscription: Offer / quota ID shown in portal | Unknown; tool classifies by quota ID and says "depends" | Nothing now; matters at first live test | Low |
| 5 | Live-testing setup (backlog 25) | Where Claude runs for live sessions; what customer output may enter a Claude session | Not started | G2 live gate | None until a tenant exists |
| 6 | Dashboard mock-ups (backlog 20) | Taste review of 2 to 3 mock-ups; branding assets later | I make mock-ups with editable branding/scope/layout config | Final HTML design | Medium: layout choice |
| 7 | Reassessment interval for maturity | Optional: confirm 6 months for small customers | 6 months, labelled as my judgement | Wording in the maturity report | Trivial |
| 8 | Canary test resources | Deferred by owner until something to test on | Deferred | G2 precision/recall tests | None |
| 9 | Export write mode (ADR 0005) | Rule 1 wording approved; design only for now | Design only; levels 1 and 1.5 first | Level 3 implementation | None |
| 10 | ADR 0007: allow read-only Log Analytics workspace queries (docs/decisions/0007) | OK to allow POST to api.loganalytics.azure.com `/v1/workspaces/{id}/query` only | NOT allowed; no code uses it | Usage-based monitoring/security checks (tier B in docs/MODULE-MONITORING-SECURITY.md) | None yet |
| 11 | Cost governance layer scope (docs/COST-GOVERNANCE.md section 8) | Answers to 5 questions: layer shape, tag standard precedence, privacy rule, first build phases, cost-weighted coverage timing | Phase 1 only (tag discovery and policy tag checks), findings plus posture view, values stored for low-cardinality keys only | Building any TAG, POL, BUD, ALR, EXP check | Low: all Reader-only, cheap to reshape |

## Closed
- 2026-10-17: ADR 0004 hybrid (option C). Backlog approved. PLAN v0.1 approved (2026-10-18).
- 2026-10-18: Human audit sample size (10 or 10%, cap 30) accepted by owner. Rule 1 wording approved. Questionnaire to be split and simplified (done in v0.2). Unanswered capabilities show as "needs input".

- 2026-10-20: #3 ADR 0006 approved in two stages. Stage 1 (Cost Management Query and Forecast POST, GET reads) built into the allowlist with tests. Stage 2 (Cost Details report and blob download) remains pending verification of side effects in the REST reference; reopen as #3b.
