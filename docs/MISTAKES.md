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
