# `fcat doctor` design (draft 1, 2026-10-18; BUILT offline 2026-10-18: src/fcat/doctor.py, tests/test_doctor.py)
Built: `fcat doctor --needs` (access-need list, offline) and `fcat doctor [--config F]` (probes: token, identity, subscriptions, resources, management groups, Advisor via ARG; counts only, writes output/doctor.json). NOT built: the role-assignment (write role) warning probe and the billing-offer probe, because their permission behaviour is UNVERIFIED. Probe semantics are UNVERIFIED live (needs gate G2).
Purpose: before a run, tell the person what the current login can and cannot see, and produce the customer-facing "access we need and why" page from the check catalogue. Read-only like everything else; uses only allowlisted calls.

## Two outputs
1. **Access need list (offline, no login).** Generated from check metadata (`permissions`, `collectors`, `run_cost`). For each permission: which checks need it, what they look at, what is lost without it. Source of truth is the registry, so it cannot drift. A test asserts every check lists permissions.
2. **Access probe (online).** Runs a few cheap read calls and reports pass/fail per capability, using the "not assessed because X" wording.

## Probes (all UNVERIFIED until a live tenant exists)
| Probe | Call | Passes when | Failure means |
|---|---|---|---|
| Token | AzureCliCredential get_token | token returned | not logged in, or conditional access needs interactive step-up (no claims challenge support, per Learn, read 2026-10-17) |
| Tenant and principal | decode token claims | tid present | unknown identity |
| Subscriptions visible | ARG `resourcecontainers` count by type | at least 1 subscription | no Reader anywhere; management groups may still be hidden |
| Resources readable | ARG `resources | summarize count()` per subscription | count returned, compare with total_records and warnings | Reader missing on that subscription |
| Management group tree | ARG management groups query | rows returned | no rights at management group level; hierarchy views limited |
| Advisor | GET Microsoft.Advisor/recommendations (or ARG advisorresources) | 200 | Advisor-based checks are "not assessed" |
| Billing offer | `quotaId` from subscriptions + billing.classify | classify result | cost checks flagged by BILL-OFFER-01 |
| Cost Management read | blocked until ADR 0006 is accepted | n/a | n/a |
| Log Analytics | needs another host (api.loganalytics.io) and a decision record; blocked | n/a | n/a |
| Write roles present | ARM role assignments GET at scope for the signed-in principal (needs permission to read them; may itself fail) | no Owner/Contributor/write role found | WARN only (T-09): tool cannot enforce least privilege, only advise |

## Behaviour rules
- Never fail the whole run because a probe fails; report capability and continue.
- Output is a short table plus a JSON file; no resource names, only counts.
- A probe that errors with 403 is "not allowed", with 429 "throttled, retry later", anything else "unknown" (never guessed as pass).
- Doctor's calls count in the run manifest like any other.

## Open questions (not for the owner yet)
- Whether ARG hides subscriptions where the principal has no role: expected, UNVERIFIED.
- Whether reading role assignments needs more than Reader: UNVERIFIED.
