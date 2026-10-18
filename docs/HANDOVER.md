# HANDOVER (overwrite this file; do not append)
Last updated: 2026-10-18 14:35 UTC
<!-- auto:start -->
Last checkpoint (UTC): 2026-10-18 14:35
Base commit: 21111a6
Gates: FAIL
Files changed in this checkpoint: 14
narrative_hash: 47bf99c64eee
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
- 2026-10-18 later: owner asked for a shorter, plainer questionnaire split by "visible in portal/CLI" (owner, Part 1) vs customer (Part 2). Done as v0.2 in docs/maturity/ (13 questions, 3 plain-language answers). Numeric cut-offs dropped (no official source). Owner confirmed: unanswered capabilities show as pending/needs input. Awaiting owner review of v0.2.
- 2026-10-18 later: owner asked whether the cloud app is the right place to work. Answer: fine for the no-tenant phase; for live (G2) testing run the tool on the owner's laptop (az login) and decide how customer output is shared with Claude (confidentiality). Same repo and CLAUDE.md work on every Claude Code surface (docs read 2026-10-18). Owner decision pending on the live-testing setup.
- 2026-10-18: Output audit Layer A BUILT (src/fcat/audit.py, 11 invariants, evidence + fingerprint per finding, report fingerprint, HTML/Excel/JSON audit section, CLI exit 3). Metamorphic tests added (row order, exclusions). Tests 54 pass.
- 2026-10-18: Synthetic estate + golden report BUILT (scripts/make_synthetic.py, tests/test_golden.py). Formatting-only edits to a check change its logic hash and therefore the golden; re-approve with --approve and review the diff.
- (Earlier checkpoint of this unit pushed to wip/auto only because one test needed a quotaId in its fixture; fixed in the next commit.)
- 2026-10-18: Backlog 18 research done (KB note 10). Added src/fcat/billing.py, check BILL-OFFER-01, quotaId in subscriptions collector, golden updated (diff reviewed: only BILL additions). Key finding: CSP customers see RETAIL cost only and zero for reservation usage; Sponsorship and classic CSP have no Cost Management data. Open questions for owner in note 10 (not blocking).
- 2026-10-18: OWNER AWAY for the next few steps. Work unattended. All pending owner items are parked in docs/DECISIONS-PENDING.md with defaults; follow its rules (do not ask, use defaults marked provisional, no customer use, do not widen the allowlist).
- 2026-10-18: backlog 19 built: `fcat import-focus <file|folder>` aggregates a FOCUS CSV(.gz) into snapshot cost_focus.json. Refuses mixed currencies and non-FOCUS files, reports missing cost columns. Column names from Learn FOCUS schema page (read 2026-10-18). UNVERIFIED against a real export. Next unattended: item 7 (more orphan/idle checks), then 8 (parity matrix).
- 2026-10-18: backlog 7 first batch: ORPH-PIP-01, ORPH-NIC-01, ORPH-NSG-01, ORPH-ASP-01 (hybrid: KQL projects raw fields, rules in Python). Property paths from my knowledge of ARM schemas, NOT re-read from the hub query files (clone gone after reset): UNVERIFIED, offline-only. Golden updated (73 findings, diff reviewed by counts). No cost estimates yet. Next: re-fetch hub query files from GitHub to verify predicates, then stopped VMs, backendless LBs/App Gateways, empty elastic pools, idle VNet/NAT gateways; then item 8 parity matrix.
## In progress
Nothing half-done.
## Next step
Owner review of maturity questionnaire and confidence-label rule (reminder due next stopping point). Backlog item 2 Layer A part 1 DONE; items 2, 3, 18 DONE; next 4 (cost collectors + allowlist ADR), 5, 7, 8. Old text: output audit Layer A (finding fingerprints/evidence, invariants checker, Audit section), then synthetic estate + golden report, cost collectors research. Add branding/module-weighting config to the plan.
## Open questions for the user
Audit sample size and confidence thresholds (explained in chat, awaiting agreement); maturity scope wording; Approve PLAN v0.1 formally.
## Blockers
Test tenant not guaranteed early, so initial checks are fixture-based and untested.
## Resume: read CLAUDE.md, this file, docs/PLAN.md, newest docs/log entry, docs/MISTAKES.md
