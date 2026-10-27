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

## M-010 (2026-10-20) Governance phase 1 and 2 slips (all caught before commit or push)
(1) A check used `x in BAD_RUNS` on a value that could be a list, which crashed under the fuzz test (unhashable); guard with an isinstance check. (2) A paging test handler matched on the URL fragment 'budgets' first and never served the next page; test bug, not code. (3) The customer data guard blocked the public Microsoft policy ids; resolved by ADR 0009. (4) Reformatting source after approving the golden file changed the logic hash and invalidated the golden; approve the golden last, after ruff format.
Prevention: run `ruff format` before `make_synthetic.py --approve`; type-guard before set or dict membership on snapshot values.

## M-011 (2026-10-21) Batch 7 and round 4 slips (all caught by tests or the screenshot check before commit)
(1) A new check id had an area part longer than 6 characters (OPT-DEVOFFER-01), rejected by the id-pattern test. (2) A check read a numeric field with int() on fuzzed input and crashed under the fuzz test; guard with an isinstance check, as in M-010. (3) The first draft of OPT-DTSTOR-01 listed the subscriptions collector first, which breaks the "removing primary rows" test; the collector that holds the reported resources goes first. (4) Three tests hard-coded the finding total (121); adding synthetic rows changed it. (5) The round 4 view switch grew to five buttons and overflowed at 390 px; found only by measuring scrollWidth in a headless browser, not by the unit tests.
Prevention: derive expected counts by hand and update them in the same edit as the estate; after any change to the top bar run the mobile overflow check (scrollWidth versus clientWidth at 390 px) on every view.

## M-012 (2026-10-21) Found by the new quality gates, not by earlier tests
1. **Dashboard crashed on a report without a start time.** `changes()` called `.slice` on a null `started`. Golden and older reports have none, so the whole page stayed empty. Found by the axe-core gate script (0 views rendered). Fixed with a tolerant `day()` helper and a regression test that runs the page script in node with stubbed DOM. Lesson: render every dashboard path with the golden report in a browser, not only with fields a real run happens to fill.
2. **Allowlist and transport read URLs differently.** `https://evil.example\@management.azure.com/...` passed `_check` (urlparse hostname) while urllib.request would use the whole string as host. It failed closed in practice (name does not resolve), so not exploitable today, but a safety check must never approve what the sender reads differently. Fixed: network location must equal an allowed host exactly, no backslash or control characters. Found by the parser-differential property test. Lesson: for safety checks, test the checker against the sender, not against itself.
3. **Dependency with a critical advisory in the lock** (certifi 2026.7.22, PYSEC-2026-4320, fixed 2026.10.19). Found by pip-audit; nothing in the old gates looked at advisories. Fixed in both lock files and NOTICE.

## M-013 (2026-10-21) Slips during the eight-task batch (all caught by tests or tools before push, except the last)
(1) A check id was too long again (IDLE-VMDEALLOC-01, third time after M-009 and M-011); the id-pattern test caught it. Prevention: count the THING part (max 6 characters) when naming. (2) Three tests held the literal finding total (golden formula, redaction test, tailoring test), so every new check needed edits in three places; the redaction and tailoring tests now read the total from the golden file, and only the independent hand derivation in test_golden.py keeps a literal. (3) A test passed the whole page script to `node -e`, which hit the 128 KB single-argument limit once the estate grew; it now writes a file. (4) `--redact` would have leaked resource ids held inside a details list (found by the existing synthetic-estate redaction test); new details keys with resource ids must be listed in redact.RESOURCE_ID_LIST_KEYS. (5) The checkpoint guard blocked a placeholder GUID in a user-facing message; reworded, no literal GUIDs anywhere. (6) I first tried the GitHub REST API from the cloud workspace to read action SHAs; it is blocked there, `git ls-remote` works.
Prevention: derive counts from data, not literals; when adding a details key that carries identifiers, add it to redaction in the same edit.


## M-014 (2026-10-21) Defects found by the independent-style review pass (scheduled batch, unit 2)
1. **`--redact` left GUID-shaped ids in free text.** Collector error text (`subscription <id>: HTTP 403`, from costdata.py and govcost.py) and failed-check reasons went into the redacted report.json/html unchanged. Fixed centrally in `cli._finish` (redact.errors, redact.scrub_text) with a regression test. Lesson: redaction covered structured fields (finding ids, details) but not free text; any new place that formats an id into a string needs the central scrub, not a per-collector fix.
2. **`fcat rollup` copied not-run reasons verbatim** although its docstring promises no ids. Now scrubbed, with a regression test.
3. **costdata silently dropped malformed rows**, so a subscription total and every unmapped-cost share could be built on partial data. Now any malformed row fails that subscription ("cannot be trusted"), so COST-UNMAP-01 says not assessed. Regression test added.
Known and not changed: names (resource group, resource) inside free text cannot be recognised and are not scrubbed; negative cost lines (credits) can make an unmapped share odd (not decided, noted for the first G2 session).
Prevention: when adding free-text output (errors, reasons, messages) assume it can carry ids, and route it through redact.scrub_text.

## M-015 (2026-10-21) Wrong claim about what a fix needed
In KB 17, backlog 44 and my summary I said the per-account read for OPT-STORLC-01 "needs an allowlist ADR". The allowlist already permits any GET on management.azure.com, so it did not. I found this when about to draft the ADR, by reading http.py before writing. Prevention: before saying a change needs a decision record, read the code that enforces the rule.

## M-016 (2026-10-27): `pgrep -f` and `pkill -f` match the caller's own shell
A monitor loop `while pgrep -f mutation_smoke` reported "running" long after the run ended, because the monitor's command line contains the pattern; three monitors expired for nothing and a commit was delayed. A later `pkill -f` with a similar pattern killed my own shell (exit 144). Match a full script path and exclude the shell (`pgrep -af "scripts/mutation_smoke.py" | grep -v pgrep`), or check the output file for its final line ("0 survived"), or wait for the background task's own completion notice. Never use `pkill -f` with text that appears in the command being run.
