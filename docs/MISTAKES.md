# Mistakes and lessons
| ID | Date | Symptom | Root cause | Fix | Prevention (rule/test) | Status |
|---|---|---|---|---|---|---|
| M-001 | 2026-10-17 | Hub built-in queries said on by default | Misread docs | Corrected after reading configure-recommendations.md | Read the config doc, not the summary | closed |
| M-002 | 2026-10-17 | Hub query count 22 vs actual 23 | Counted from memory | Counted files | Count from source | closed |
| M-003 | 2026-10-17 | Said Log Analytics Reader needed on top of Reader | Assumed without checking */read | Checked manage-access page | Verify role claims on Learn; test on live tenant | open (live test pending) |
| M-004 | 2026-10-17 | Checkpoint script pushed to main even when tests failed; ruff --fix removed an import that registered checks | Script written before quality gates existed; unused-import autofix | Gates now decide: wip/auto always, main only if G0+G1 pass; explicit load_builtin() | Quality gates in docs/QUALITY.md; test that exercises registry | closed |
| M-005 | 2026-10-17 | Checkpoint push to wip/auto rejected (stale info) | --force-with-lease needs a local tracking ref, which a single-branch shallow clone lacks | Plain non-force push (history is linear); push main manually | Test new push logic with a dry run before relying on it | closed |
| M-006 | 2026-10-18 | Checkpoint after BILL-OFFER-01 failed G1 and pushed to wip/auto only | I ran the checkpoint without running the full tests first; an older renderer test used a subscription fixture without quotaId, which now (correctly) produces a finding | Added quotaId to that fixture; main updated next commit | Run `python scripts/gates.py` before every checkpoint after a behaviour change; when a check starts producing new findings, grep fixtures that feed it | closed |

## Claims to re-verify periodically (versions, preview status, prices)

## M-007 (2026-10-18) Wrote check predicates from memory before reading the source queries
What happened: ORPH-NSG-01 first treated "both association lists null" as unknown and skipped it. The hub query (microsoft/finops-toolkit commit f12c29e, read 2026-10-18) treats absent as no association, so my version would have missed real orphans. ORPH-PIP-01 also missed public IPs attached only to an unattached NIC.
Caught by: re-reading the hub query files after the first batch was committed (not pushed to main with the wrong rule).
Prevention: read the upstream query/ARM schema first, then write the check. Where upstream semantics are UNVERIFIED live (null versus empty array), say so in the docstring.

## M-008 (2026-10-18) Collector wrote an empty-looking result when its input was missing
What happened: the first rightsizing collector, if the VM inventory (`vms`) had failed to collect, would have saved `vm_cpu` with zero rows, so RIGHT-VMCPU-01 would have reported "ran, 0 findings" instead of "not assessed". Also, metric points outside the requested window were counted toward coverage.
Caught by: QA read-through after the commit (5c9fa21), before any live use; fixed in the QA commit with two tests.
Prevention: a collector that depends on another snapshot must record an error and write nothing when that input is absent; an empty result is only valid when the input was present and really empty. Parse functions must clamp to the requested window.

## M-009 (2026-10-18) Smaller slips while adding 14 checks (all caught by tests before commit)
Check id longer than the 6-character area limit (MOD-LBBASIC-01); a Cosmos fixture with wrong arithmetic; hand-derived finding counts and test counts not updated when the synthetic estate grew; a fixture missing `_meta` for an age rule; mock-up text wrapping on mobile.
Prevention: keep the id pattern in mind when naming; derive expected numbers by hand before reading the code's output; update the count assertions in the same edit as the estate.
