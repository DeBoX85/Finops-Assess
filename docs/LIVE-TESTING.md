# Live testing plan (gate G2), prepared offline 2026-10-21

Status: NOT STARTED. No tenant is available (owner, 2026-10-21). Every check is `offline-only` (hard rule 8). This plan makes the first live session short and productive. Backlog 25.

## 0. Decisions needed from the owner BEFORE the first live session (not decided)
1. Which tenant: a tenant the owner controls, not a customer tenant, for the first pass. Any Azure tenant is also an Entra tenant (KB 15).
2. Where the tool runs: the owner's laptop (default). Whether Claude Code runs on that laptop for live sessions, or Claude only sees pasted, redacted output.
3. What output may enter a Claude session: default proposal is `--redact` output only, never raw snapshots, and no customer data at all in the first pass (the test tenant has none). The owner confirms any NDA or confidentiality limit for later customer tenants.
4. Cost: canary resources cost a little (a small unattached disk, a public IP). Owner approves a monthly cap.

## 1. What the owner prepares (the tool never creates or changes anything)
- Test tenant with at least one subscription; the signed-in identity has Reader on it (and on a management group if possible). Keep a second identity with no roles to test "not assessed" paths.
- Canary resources, each named `fcat-canary-<kind>`, one known-bad and one known-good twin per check family. The sheet `docs/LIVE-TEST-SHEET.md` has a column to record each canary; `docs/CANARY-SPEC.md` (generated) says per check which condition the canary must reproduce and which near-identical twin must NOT be flagged.
- Optional extras for opt-in modules: a Log Analytics workspace, a budget, a policy assignment with a tag rule. These exercise governance and monitoring checks.

## 2. Order of work in the session (stop at the first failure and log it)
1. `fcat doctor` (docs/DOCTOR.md): record which permissions are present and which probes fail. Expect some to fail; each failure must read "not assessed, because X", never a silent pass.
2. `FCAT_LIVE=1 pytest -m live`: every collector query accepted by Azure Resource Graph. Fix KQL errors first; they block everything else.
3. Run the tool on the test tenant. Compare resource counts with the portal (QUALITY.md section 3, item 4).
4. For each row of the live test sheet: canary found, known-good twin not flagged, verdict and date.
5. Settle the items in the three UNVERIFIED hot spots below, by experiment.
6. Reader-only run: record exactly which collectors fail (ADR 0008 open item).
7. Record sanitised responses as fixtures (tests/fixtures/recorded) for drift detection.
8. Only after a check passes its row: change its `validation` to `live`, edit the matching source lines to VERIFIED with date and source, re-run `scripts/live_readiness.py`, run the gates.

## 3. Hot spots (claims most likely to change code)
Taken from the register (`docs/UNVERIFIED-REGISTER.md`, generated). Examples already known:
- Whether ARG returns `microsoft.devtestlab/schedules` and `microsoft.storage/storageaccounts/managementpolicies` (OPT-DTSTOR-01, IDLE-VMSHUT-01, OPT-STORLC-01 refuse to decide on an empty result).
- `tags` null versus empty in ARG, policy parameter names other than the require-tag policy, policy compliance timing (tag checks).
- Whether Reader alone can read Log Analytics workspace data and Sentinel alert rules (ADR 0007, 0010).
- Anomaly rule visibility across subscriptions (cost governance).
Work through the register top to bottom after these.

## 4. Safety during live sessions
- Read-only allowlist stays on; the live tests make GET and the allowed read POSTs only. No test creates resources.
- Output goes to the ignored `output/` folder; run `fcat purge` at the end of the session.
- Do not paste tenant or subscription ids, tokens or tag values into chat. Use `--redact`.

## 5. Exit criteria for "G2 passed for check X"
Canary found, known-good twin not flagged, no query error on the least-privileged role named in the check metadata, verdict recorded with date, source lines updated. A check that fails any of these stays `offline-only` and gets a MISTAKES or KB entry.
