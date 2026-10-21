# Live session rehearsal (first G2 session), prepared offline 2026-10-21

Purpose: turn docs/LIVE-TESTING.md into a run sheet that can be followed in order, with a stop rule at each step. Nothing here has been run against Azure. Every number below that is not marked with a source is a plan, not a measured value.

Read first: docs/LIVE-TESTING.md section 0 (four owner decisions are still open: which tenant, where the tool runs, what output may enter a Claude session, the canary cost cap). Do not start before they are answered.

## A. Before the session (about 30 minutes, owner)
1. Test tenant and subscription exist; the identity you will sign in with has Reader on the subscription. Note the role names you hold in a private place, not in chat.
2. Canary resources created per docs/CANARY-SPEC.md, each named `fcat-canary-<kind>`, with its known-good twin. Start with the families that need no opt-in switch (orphaned disks, public IPs, NICs, NSGs, snapshots, availability sets, legacy SKUs).
3. A second identity with no roles at all, for the "not assessed" paths.
4. On the laptop: `python -m venv .venv`, install from the hash-locked requirements (`pip install --require-hashes -r requirements/runtime.txt`, then `pip install --no-deps -e .`), `az --version`, `az login` with the first identity.
5. Output folder is ignored by git (the tool refuses otherwise). Choose it outside the repo if in doubt.

## B. Session order (stop at the first failure, log it, do not improvise past it)
| Step | Command | Expect | Stop and log if |
|---|---|---|---|
| 1 | `fcat doctor --needs` | list of access needs, no login, no network | any error (offline bug) |
| 2 | `fcat doctor --config <cfg>` | table of probes, `output/doctor.json` | a probe says pass when you know the role is missing (false pass); an unknown status is acceptable |
| 3 | `FCAT_LIVE=1 pytest -m live` | every collector query accepted | a KQL syntax or column error: fix the query first, everything else depends on it |
| 4 | `fcat run --config <cfg> --out <out>` (default switches only) | report, two dashboards, self-audit pass | self-audit fail (stop, do not hand the report on); a collector error in the manifest |
| 5 | Compare counts with the portal for 3 resource types (QUALITY.md section 3, item 4) | equal | counts differ: find out whether the tool or the portal scope is wrong before trusting any finding |
| 6 | Fill the live test sheet row by row (docs/LIVE-TEST-SHEET.md): canary found, twin not flagged | per check | a false positive or false negative: that check stays `offline-only` and gets a MISTAKES entry |
| 7 | Second identity with no roles: `fcat run` | most checks say "not assessed, because X" | any check passes silently or reports zero findings (rule 6 violation) |
| 8 | Opt-in switches, one at a time, in this order: `storage_apis`, `governance_apis`, `cost_apis`, `rightsizing` | see section C | see section C |
| 9 | `fcat run --redact` and read the HTML and JSON | no subscription id, tenant id, resource group or resource name | any identifier visible (privacy defect, highest priority) |
| 10 | `fcat purge --out <out>` then `--yes` | only files fcat created are listed and removed | it lists a file you did not expect |

## C. Opt-in switches: what to confirm and how many calls to expect
Throttling facts from Learn (read 2026-10-21, https://learn.microsoft.com/azure/azure-resource-manager/management/request-limits-and-throttling): Resource Manager reads use a token bucket of 250 with 25 tokens per second per subscription; storage management reads are limited to 800 per 5 minutes per subscription per region; Azure Resource Graph and Cost Management have their own limits. The manifest lists every call the tool made, so count them there afterwards.

| Switch | Calls | Confirm | Known UNVERIFIED items it settles |
|---|---|---|---|
| `storage_apis` | one GET per StorageV2 or BlockBlobStorage account | an account WITH a policy returns 200 and a rules list; an account WITHOUT one returns what? Record status and error code exactly | the "no policy" reply (assumed 404 ManagementPolicyNotFound). If different, fix `NO_POLICY_CODE` in src/fcat/storagedata.py |
| `governance_apis` | 3 per subscription | budgets with `currentSpend`; anomaly rules visible to Reader; exports with run history | docs/COST-GOVERNANCE.md UNVERIFIED lines |
| `cost_apis` | 1 Cost Management Query (plus pages) per subscription, one Resource Graph id list | column names (`Cost` or `PreTaxCost`), ResourceId case, whether nextLink needs POST with the same body, credits as negative lines | docs/COST-DATA.md "UNVERIFIED (first G2 session)" |
| `rightsizing` | many (metrics per VM, capped by `rightsizing_max_vms`) | metric names, 429 behaviour | docs/RIGHTSIZING.md |

Stop rule for any switch: if a 429 persists after the tool's retries, stop that switch and record the header values; do not raise caps in the middle of a session.

## D. Specific facts to capture on the first successful run (each settles a register line)
1. Does `properties.extended.instanceView.powerState` contain a `time` field? (decides IDLE-VMDEAL-01)
2. Are `microsoft.devtestlab/schedules` rows returned, and with which property names? (IDLE-VMSHUT-01, OPT-DTSTOR-01)
3. Is Advisor `savingsAmount` per month or per year for a known recommendation? Compare with the portal. (ADV-COST-01 wording)
4. `tags`: null or empty object on an untagged resource? (tag checks)
5. As Reader only: which collectors fail? (ADR 0008)
6. A sanitised copy of each distinct response shape goes to tests/fixtures/recorded (no ids, no names).

## E. After the session
1. For each passed row: set `validation` to live in the check metadata, edit the matching source lines to VERIFIED with date and source, run `python scripts/live_readiness.py`, then `python scripts/gates.py --full`.
2. For each failure: MISTAKES entry, KB note, fix, re-run.
3. `python scripts/checkpoint.py` and update docs/HANDOVER.md.
4. Share only `--redact` output in any chat. Never paste a snapshot.

## F. What this sheet does not cover
Customer tenants, sovereign clouds, billing-scope cost data, Sentinel (ADR 0010 is still PROPOSED), and Windows laptops (nothing here was run on Windows; UNVERIFIED).
