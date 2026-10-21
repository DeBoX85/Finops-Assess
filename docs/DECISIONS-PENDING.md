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
| 12 | Governance posture rules (mock-up round 3, docs/COST-GOVERNANCE.md section 12) | Review the proposed rules for Evidenced / Partial / Not evidenced per capability, and agree that checks should also record what they saw working ("pass" records), which is a change to the check interface | Rules as proposed, mock-up only; nothing in the tool computes posture yet | Posture view in the real report; maturity evidence from governance | Medium: touches every check if pass records are added |
| 13 | ADR 0010 + docs/MODULE-SENTINEL.md: Sentinel FinOps as an opt-in module; also raise ADR 0007 (#10) to the gate for its tier B | Approve the module shape, check catalogue and build order; confirm Log Analytics Reader on target workspaces is acceptable with the fixed query allowlist | Build tier A only, offline | Tier B/C Sentinel checks | Low: module is additive |
| 14 | Sentinel rule scan (read alertRules query text) | Opt-in yes/no; confirm handling (derived map only, hash, names pseudonymised) | OFF; consumer evidence from SOC optimization states only | Event-ID level DCR advice, trustworthy Protected verdicts | Medium: fewer Review verdicts and weaker coverage assurance if OFF; customer trust and redaction work if ON |

## Closed
- 2026-10-17: ADR 0004 hybrid (option C). Backlog approved. PLAN v0.1 approved (2026-10-18).
- 2026-10-18: Human audit sample size (10 or 10%, cap 30) accepted by owner. Rule 1 wording approved. Questionnaire to be split and simplified (done in v0.2). Unanswered capabilities show as "needs input".

- 2026-10-20: #3 ADR 0006 approved in two stages. Stage 1 (Cost Management Query and Forecast POST, GET reads) built into the allowlist with tests. Stage 2 (Cost Details report and blob download) remains pending verification of side effects in the REST reference; reopen as #3b.
- 2026-10-20: #11 cost governance scope decided by owner: findings plus three-state posture view; tag standard precedence policy, then config, then inferred (none evident => say so); build phase 1 only (tag discovery, tag hygiene, tag policy checks); store ALL tag values in the local snapshot (owner chose this over my recommendation of counts only for high-cardinality keys; consequence: snapshot and any report with values are customer data, `--redact` must mask values, output stays in the ignored folder). Budget and alert email addresses and storage ids are still never stored (phase 2).

- 2026-10-21: GitHub gap analysis. Owner agreed G7 (target level per capability, backlog 36). G8 multi-tenant/MSSP batch: owner unsure, chose the option that keeps maximum flexibility (backlog 37: design for a list of scopes, keep single-tenant default, no hard-coded single-tenant assumptions). Not yet chosen to build: G1, G2, G4 to G6 (backlog 33 to 35).
