# Mistakes and lessons
| ID | Date | Symptom | Root cause | Fix | Prevention (rule/test) | Status |
|---|---|---|---|---|---|---|
| M-001 | 2026-10-17 | Hub built-in queries said on by default | Misread docs | Corrected after reading configure-recommendations.md | Read the config doc, not the summary | closed |
| M-002 | 2026-10-17 | Hub query count 22 vs actual 23 | Counted from memory | Counted files | Count from source | closed |
| M-003 | 2026-10-17 | Said Log Analytics Reader needed on top of Reader | Assumed without checking */read | Checked manage-access page | Verify role claims on Learn; test on live tenant | open (live test pending) |
| M-004 | 2026-10-17 | Checkpoint script pushed to main even when tests failed; ruff --fix removed an import that registered checks | Script written before quality gates existed; unused-import autofix | Gates now decide: wip/auto always, main only if G0+G1 pass; explicit load_builtin() | Quality gates in docs/QUALITY.md; test that exercises registry | closed |

## Claims to re-verify periodically (versions, preview status, prices)
