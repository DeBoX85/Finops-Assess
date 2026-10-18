# Output quality audit (design v0.1, 2026-10-17)
Scope: how we check and audit what the tool PRODUCES (reports, numbers, recommendations, maturity scores), as distinct from code quality (docs/QUALITY.md). Status: design; only items marked BUILT exist.
Core principle: a finding is a claim about a customer's environment. It must be true, traceable, scoped and honestly labelled. We measure truth by sampling against the portal and independent tools, not by trusting our own tests.

## 1. What can be wrong with an output (audit questions)
1. Precision: is the finding true (false positives)? 2. Coverage: what was not looked at (false negatives, skipped checks, scope gaps)? 3. Numbers: are costs and savings right, in the right basis (actual vs list), currency and period? 4. Traceability: can a reader see the evidence and reproduce it? 5. Freshness: how old is the data? 6. Language: does text overclaim ("will save") or give advice without risk and verification steps? 7. Safety: does the deliverable leak data it should not (other tenants, internal notes)? 8. Consistency: do HTML, Excel and JSON agree? 9. Maturity scores: are they explainable and repeatable?

## 2. Layer A: automated self-audit on every run (machine-checked, shown in every report)
Planned as `fcat audit` and an "Audit" section/sheet; BUILT items marked.
- Coverage statement: checks ran/skipped/not assessed/failed with reasons, collector errors, scope counts, validation level per check (offline-only vs live). BUILT (manifest, HTML, Excel, schema).
- Evidence trail per finding: check id, rule version hash (hash of the check function source), snapshot digests of the collector files used, finding fingerprint. BUILT 2026-10-18 (src/fcat/checks.py, snapshot.py). Still PLANNED: data timestamp, KQL hash, source URLs of the rule.
- Reproducibility: re-running `analyze` on the stored snapshot must give identical findings (hash compare). Determinism test BUILT; per-run report fingerprint BUILT (audit.report_hash, excludes times; findings sorted for stable order).
- Invariants over the output: no duplicate (check, resource); every finding's check is in the catalogue; every finding's resource is inside the assessed scope; savings are never negative and never exceed the cost they derive from; one currency per figure; actual and list never summed together; per-subscription figures sum to totals; counts equal across JSON, HTML and Excel. BUILT 2026-10-18 in src/fcat/audit.py as INV-01 to INV-11 (duplicates, catalogue membership, ran-only, count match, severity set, fingerprint recompute, non-empty fields, certainty-word lint, no negative savings, no ran-with-collector-error, evidence present). Shown in JSON, HTML (Self-audit) and Excel (Audit sheet); CLI exits 3 on failure. Still PLANNED: resource inside assessed scope, savings not above cost, one currency, actual and list never summed, per-subscription sums equal totals (need cost data first).
- Data-quality flags: cost data period and completeness, known FOCUS gaps hit (ListCost = 0 for reservation usage and Marketplace per Microsoft's conformance summary), missing tags, billing type not supported by a check, data latency notes.
- Language lint on recommendation text: banned certainty words BUILT (INV-08). Required elements (estimated basis, risk, how to verify before acting, source link) PLANNED.

- Generic accuracy tests over every registered check, BUILT 2026-10-18 (tests/test_accuracy.py, backlog 22): seeded fuzzing of row types (found and fixed 5 crashes on malformed rows: ORPH-DISK-01, ORPH-AGW-01, MON-LAWCAP-01, IDLE-VMDISK-01, BILL-OFFER-01), row-order and extra-column invariance, locality (removing a row never changes findings of other rows), and a fixture/synthetic-column versus KQL-projection contract that would have caught the earlier nicCount/nicRefs drift. New checks are covered automatically. Still PLANNED from backlog 22: cross-source reconciliation (needs Advisor/cost data) and recorded-response contract tests (needs a tenant).

## 3. Layer B: independent oracles (not truth, but disagreements must be explained)
On the test tenant and, if permitted, in customer runs: Azure Advisor recommendations, Cost Management totals, azqr results, FinOps toolkit/hubs query results, Learn's Workload optimization guidance. Output: a parity table with every difference explained (our check stricter, different threshold, different data, our bug, their bug). Stored in docs/validation/ (no customer data). Oracles can be wrong too; a disagreement triggers investigation, never an automatic fix.

## 4. Layer C: human sampling audit (the only real precision measurement)
- Per check, per assessment: audit every finding if 10 or fewer, else a random sample (proposal: 10 or 10%, whichever is larger; the user may change this). The auditor opens the resource in the portal and records TP, FP or unclear, with a reason.
- Precision per check = TP / (TP + FP) with the sample size shown (small samples give wide uncertainty; say so). Proposal (user decides): a check may carry confidence "high" only if measured precision is at least 90% on at least 30 audited findings across at least 2 environments; until then confidence is capped at "medium" and the report says "precision not yet measured".
- Recall cannot be measured fully (unknown unknowns). Estimate with canary resources (known positives and known negatives created by the owner) and by looking at what oracles flag that we do not.
- False-positive patterns found go to the check's fixtures, MISTAKES.md and the exclusion logic; precision history is kept per check in docs/validation/<check>.md.

## 5. Layer D: independent review
Before a report goes to a customer: a reviewer that did not build the report reviews it against the rubric in section 7 (a fresh agent session reading only the report, evidence and rubric is one option; the owner is the final reviewer). Review of new checks and any savings logic is mandatory at gate G3 (docs/QUALITY.md).

## 6. Layer E: regression audit
A synthetic estate (offline snapshot set with edge cases: exclusions, empty scopes, many pages, missing data, sovereign-like names, huge numbers) with an approved golden report. Any change that alters the golden report must be explained in CHANGELOG and re-approved by the owner (approval testing). Synthetic data proves stability, not realism. BUILT 2026-10-18 for the one check that exists: scripts/make_synthetic.py generates tests/synthetic/snapshot (no real IDs); tests/golden/report.json is the approved report; tests/test_golden.py compares and also checks the golden against an independent hand derivation. Grows with every new check.

## 7. Report release checklist (human, per customer deliverable)
Scope and period stated; tool version and validation levels shown; limitations and not-assessed list shown; no internal notes or other customers' names; recommendations have basis, risk and verification steps; every number traceable; maturity scores show evidence and "needs input" items; tailoring options applied as intended; PDF rendered and read; sign-off (name, date) recorded with the output, outside git.

## 8. Maturity score audit
Each capability score must list the evidence items used, the evidence that was unavailable ("needs input"), and the rubric version. Repeatability check: two reviewers score the same evidence pack independently; disagreements refine the rubric. Compare against external self-assessments for sanity (Microsoft Learn lists a FinOps review assessment and finops.org has a FinOps Assessment capability; their fit as a reference is UNVERIFIED).

## 9. Metrics kept in the repo (no customer data)
Precision per check (with n), false-positive causes, coverage percentage per run type, reconciliation deltas, defects found at audit by category, time to audit. Reviewed at each release.

## 10. Audit of the audit
Audit records (who, when, method, sample, verdicts) are saved with each output outside git; aggregate metrics only go to the repo. Periodically a different person or fresh reviewer re-audits a sample of past audits.

## 11. Limits
Sampling gives estimates, not guarantees. Oracles share data sources with us (Resource Graph, Cost Management), so shared upstream errors are invisible. Synthetic data is not reality. Until the test tenant exists, none of layers B and C can run.
