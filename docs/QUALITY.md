# Quality gates, tests and verification
Status: v0.1, 2026-10-17. Principle: automate what can be automated, but a green automated run is never accepted as proof of something it cannot prove. Section 6 lists what automation cannot prove.

## 1. Gates
| Gate | When | Content | Automated |
|---|---|---|---|
| G0 fast | every checkpoint, pre-push | ruff lint (E,F,I,B,UP,S,BLE), ruff format check, mypy (check_untyped_defs), documentation check (required files, HANDOVER sections, broken relative links in all docs/**/*.md and root md files are errors), customer-data/secret scan on staged changes | yes (scripts/gates.py, scripts/checkpoint.py) |
| G1 offline | every checkpoint | all offline tests (incl. Hypothesis property tests and headless-browser dashboard tests), coverage threshold 85% total (now ~97%) and 90% per module (auth.py 70%, it shells out to az), architecture rules, schema contract, per-check fixtures; with `--full`: pip-audit on the runtime lock and axe-core on both dashboards (light and dark) | yes; the `--full` parts report "NOT RUN, because X" without network or browser, never a pass |
| G2 live | before any check is marked `validation=live`, before every release, after any change to a collector, KQL or API version | read-only smoke tests against the test tenant: every KQL accepted by ARG, canary resources found, reconciliations (section 3) | partly (pytest -m live, FCAT_LIVE=1); needs tenant and owner-created canaries |
| G3 release | before a tag | G0 to G2 pass; verification debt reviewed with the user; independent review of new checks and any savings logic by a reviewer that did not write them; sample report read by a human; CHANGELOG; no unverified claim in customer-facing text | partly (checklist) |
Branch rule: checkpoints always push to `wip/auto`; they push to `main` only if G0 and G1 pass, so main always works.

## 2. Offline test classes (implemented unless marked planned)
- Unit/behaviour: http (retry, Retry-After, quota headers, redaction), ARG paging, truncation, config, checks runner, auth wrapper (fake credential), CLI.
- Safety rules as tests: read-only allowlist (PUT/DELETE/action POST/foreign host/http all blocked), network and subprocess access confined to named modules, no write verbs elsewhere, manifest contains counts not IDs or names.
- Check contract: every check has complete metadata (ID pattern, confidence, savings basis, run cost, framework, permissions, existing collectors, validation level) and a fixture file with at least one positive and one negative case.
- ARG query lint: order by present, `id` kept in output, no take/limit/sample, no anti/semi joins or lookup (rules recorded in KB; to be re-verified live).
- Report contract: JSON Schema (docs/schema/report.schema.json); schema requires a reason for every skipped, not_assessed or failed check; determinism; HTML escaping; HTML, Excel and JSON counts agree; not collected shows as "not assessed", never zero.
- Mutation smoke (scripts/mutation_smoke.py): 10 deliberate bugs in a copy of the code; all were detected on 2026-10-17. The list was written by the same author as the tests, so it proves little beyond the cases it covers. Planned: evaluate a real mutation-testing tool (suitability UNVERIFIED).
- Planned: property-based tests for paging, retry and FOCUS row parsing (hypothesis, availability and fit UNVERIFIED); renderer checks with headless Chromium (PDF print without overflow, no external requests, contrast); permission document generated from the check catalogue and tested against it; claim-lint (every VERIFIED/UNVERIFIED tag has a URL and date; list claims older than 90 days).

## 3. Live tests (G2) to write when the tenant is available
1. Every collector KQL runs without error (done as code, never executed).
2. Canary resources: the OWNER creates a few cheap known-bad resources (for example an unattached disk named fcat-canary-disk); each check must find its canary and must NOT flag a matching known-good resource. The tool never creates anything.
3. Recorded contract fixtures: sanitise real responses into tests/fixtures/recorded; later live runs compare response shape to the recording to detect API drift.
4. Reconciliation: sum of collected cost per subscription equals the Cost Management query total within rounding; resource counts equal the portal's.
5. Cross-tool parity (oracle, not truth): compare our findings with Azure Advisor, azqr and FinOps hubs/toolkit queries on the same tenant; every difference gets an explanation in docs/validation/.
6. Reader-only access: run with Reader only and record exactly which collectors fail (ADR open item on workspace queries).
7. Precision sampling: a human verifies a sample of findings per check; false-positive patterns recorded in the check's docs and fixtures.

## 4. Definition of done for a new check
Metadata complete with source URLs (Learn first); KQL or logic with provenance and licence note; positive, negative and edge fixtures (including known exclusions); savings basis stated (actual vs list never mixed; the basis is shown with the number); permission declared; failure and not-assessed paths tested; entry in the check catalogue; `validation=offline-only` until G2 passes; independent review for anything producing a currency figure.

## 5. Savings numbers (highest risk)
Hand-computed golden cases written before the code; invariants (never negative, never above the cost they come from, currency kept, actual and list reported separately); billing-type rules from the FOCUS conformance notes (ListCost is 0 for reservation usage and Marketplace, so list comparisons must use a price sheet); reconciliation to Cost Management totals at G2.

## 6. What automation cannot prove (read this before trusting a green run)
- Offline tests prove internal consistency under our assumptions. They cannot prove Azure behaves as we assume. No check has run against real Azure yet; every check is labelled `offline-only` in the report.
- Most check logic is KQL inside strings, which no offline test executes. Only G2 validates it.
- Coverage measures executed lines, not correctness. The mutation list is self-chosen.
- Documentation and sources can go stale (preview features, prices, versions). Verification debt is reported by gates.py (currently 7 UNVERIFIED in plan/decisions, 17 in KB notes) and must be reviewed at G3.
- Tests written by the same author as the code share its blind spots. The independent review step in G3 and the user's review are the mitigation.

## 7. Running
`python scripts/gates.py` (full), `--fast`, or `--full` (adds dependency audit and accessibility; CI runs this, .github/workflows/ci.yml); `pytest -m live` with FCAT_LIVE=1 after `az login`; `python scripts/mutation_smoke.py`.
Random test order: pytest-randomly is on by default (a failure prints its seed; reproduce with `pytest --randomly-seed=N`; turn off with `-p no:randomly`). Mutation smoke: 0 of the hand-picked mutants survive (2026-10-21). Why mutmut was rejected and what each tool found: docs/KB/notes/16-quality-practices-research.md.
CI limits (honest): the workflow is untested until it first runs on GitHub; playwright and pip-audit are version-pinned but not hash-pinned; axe-core finds only a share of accessibility problems (its README says about 57% on average), so a human check stays in G3.
CI tool lock: requirements/ci.in/ci.txt (playwright, pip-audit, hash-locked, jointly resolvable with dev.txt, checked by pip --dry-run 2026-10-21).
The roll-up page (rollup.html) is covered by the axe run in `scripts/a11y_check.py`, and a test asserts that no resource, subscription or tenant identifier appears in any roll-up output.
