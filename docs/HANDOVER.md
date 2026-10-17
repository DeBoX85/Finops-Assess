# HANDOVER (overwrite this file; do not append)
Last updated: 2026-10-17 22:55 UTC
<!-- auto:start -->
Last checkpoint (UTC): 2026-10-17 22:55
Base commit: 2ab8621
Gates: pass
Files changed in this checkpoint: 2
narrative_hash: 1444eb6bc034
stale_count: 0
<!-- auto:end -->

## State
Phase 1 skeleton plus checkpoint tooling. src/fcat: read-only http client, ARG paging, az CLI auth, snapshot, config toggles, check registry (ORPH-DISK-01, now hybrid per ADR 0004), collectors, JSON/HTML/Excel renderers from one document. 42 offline tests pass. NOTHING has run against real Azure.
## Done
KB notes 01-09, plan v0.1, ADR 0001-0004 (0004 accepted), NOTICE, Phase 1 code, checkpoint tooling and heartbeat, quality gates, ORPH-DISK-01 refactor (Python exclusions + 5 new fixtures). Owner approved the backlog (revisit later).
## Owner decisions 2026-10-17 (chat)
- ADR 0004: C hybrid. Backlog approved, may be revisited.
- Test tenants: one CSP, one MCA (Azure for Startups type). MFA on both, so az login style auth. AzureCliCredential has no claims-challenge support: test conditional access/MFA step-up early (UNVERIFIED). Canary resource creation: decide later.
- Maturity: owner answers the organisational questions, may forward discovery questions. Granularity: subscription and management group; tenant roll-up optional and skewed for 1-2 subscription customers, so report scope levels separately.
- Tailoring: flexible logo/branding (own company or ad-hoc external collaborators); which modules run, and module weight/ranking, set by owner per report; this changes report length and style.
## Owner answers 2026-10-18
- PLAN v0.1 approved. Canary resources stay deferred until there is something to test on.
- Maturity questionnaire: owner wants to review the draft before anything is built on it.
- Dashboard: Claude has creative freedom, will make a few mock-ups; branding, scoping and parts of the layout must be adjustable/editable.
- Cost data: owner asked whether a time-limited permission could let the tool trigger a Cost Management export and import the result. Researched; options and recommendation given in chat (read existing exports and import a customer-provided file; Cost Details/Query read APIs; opt-in write mode only by ADR, off by default). Awaiting owner decision on the write-mode question. Rule 1 stays absolute until then.
- Audit sampling and confidence labels: clarified in chat that these are validation-phase measures, not per-tenant requirements. Awaiting confirmation.
- 2026-10-18 later: owner wants export write mode as a toggleable opt-in; ADR 0005 drafted (proposed). Asked owner to approve rule 1 wording and how far to go (design only vs implement). Owner also asked for more built-in output-accuracy tests; suggestions given in chat, to be added to docs/AUDIT.md and BACKLOG.
- 2026-10-18: owner said start work. Maturity questionnaire DRAFT v0.1 written (docs/maturity/QUESTIONNAIRE-DRAFT.md), awaiting owner review. Workbook queries are already in docs/KB/sources/workbook-queries-raw.json (extracted from the toolkit repo); owner offered to upload workbook JSON if needed (not needed unless a newer version is wanted).
## In progress
Nothing half-done.
## Next step
Owner review of maturity questionnaire, then docs/BACKLOG.md item 2: output audit Layer A (finding fingerprints/evidence, invariants checker, Audit section), then synthetic estate + golden report, cost collectors research. Add branding/module-weighting config to the plan.
## Open questions for the user
Audit sample size and confidence thresholds (explained in chat, awaiting agreement); maturity scope wording; Approve PLAN v0.1 formally.
## Blockers
Test tenant not guaranteed early, so initial checks are fixture-based and untested.
## Resume: read CLAUDE.md, this file, docs/PLAN.md, newest docs/log entry, docs/MISTAKES.md
