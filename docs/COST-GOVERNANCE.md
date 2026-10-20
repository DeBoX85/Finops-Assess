# Cost governance layer and tag hygiene: design (v0.2, 2026-10-20, owner decided scope: see section 9)
Evidence base: docs/KB/notes/11-cost-governance-azure.md (every fact tagged VERIFIED or UNVERIFIED with source and date). Nothing here is built yet. Everything built from this design stays `offline-only` until gate G2 passes on a real tenant.

## 1. What the owner asked for (2026-10-20)
1. A tag hygiene check where the tags come from the customer's own environment, depending on how (or whether) they tag. No hard-coded required-tag list.
2. "Another layer" of assessment covering cost governance, researched in depth with a heavy Azure emphasis.

## 2. Proposed shape of the layer
Findings stay the unit of evidence. The new layer adds a domain `governance` (check id prefixes TAG, POL, BUD, ALR, EXP, STR) and a per-scope **governance posture** view that aggregates those findings and passes. Posture uses three states only, never a number (owner rule: maturity is scored only from technical evidence plus "needs input"):

| State | Meaning |
|---|---|
| Evidenced | The control exists and the tool saw it working at that scope |
| Partial | The control exists but with a gap the tool can name (for example, budget without alerts) |
| Not evidenced | The tool looked and found nothing, or could not see (shown as "not assessed, because X" when it could not see) |

Rows (capabilities) map to the existing maturity table (docs/maturity/PART1): Allocation (cap 2), Budgeting (7), Forecasting (6), Anomaly management (4), Data ingestion (1), Policy and governance (16), Unit economics readiness (9, tags only). Columns are tenant, management group, subscription. The posture feeds the maturity evidence; it does not replace Part 2 (practice questions for the customer).

## 3. Tag discovery: the customer's scheme, not ours
Order of evidence for "what is this customer's tag standard" (highest first, each source labelled in the report):
1. **Declared by policy**: tag names found in parameters of assigned tag policies (for example `tagName` on Require a tag on resources). Strongest signal because the customer wrote it down in enforceable form. Custom definitions and initiatives are reported as "unclassified policy", never guessed.
2. **Configured by the owner** in the F-CAT config (`[tags] required = [...]`, `aliases`), for a customer who gives us their standard in a document.
3. **Inferred from the estate**: keys carried by at least X percent of taggable resources (X is our proposal, default 50, labelled "our judgement"). An inferred scheme is shown as "what most resources already use", not as a standard.
Everything below measures consistency against whichever scheme source applies. If none exists (no policy, no config, no key above X), the finding is "no tagging scheme evident" with the raw key list, which is itself the answer to "if at all".

Role hints (owner, cost center, environment, application...) are a small word list used only to say "this key looks like an owner tag". They are heuristics, labelled as such, never used to require a key. The CAF categories (functional, classification, accounting, purpose, ownership) are the reference vocabulary; they are examples in Microsoft's text, not a mandate.

### Collectors (new, GET/ARG only)
| Collector | What | Notes |
|---|---|---|
| `tag_inventory` | ARG `resources` grouped by subscription x type: total count; count with any tag; per tag key (lower-cased) count; set of casings seen | Server-side summarize keeps volume small and keeps tag values off the laptop. `mv-expand` on the tags bag in ARG is UNVERIFIED live |
| `tag_values` | Per key: distinct value count, and the values themselves only when distinct count <= N (proposal 20), with counts | High-cardinality keys (owner emails) store the count only |
| `rg_tags` | `resourcecontainers` resource groups and subscriptions: tag keys, count untagged | Tags exist on RGs and subscriptions, not on management groups |
| `policy_assignments` | ARG `policyresources`: assignments, with definition id, scope, enforcementMode, parameters; plus `policyexemptions` | Needs an ARG request option `authorizationScopeFilter=AtScopeAndAbove` (API 2021-06-01-preview or later) or policies assigned at management group are missed. Small change in src/fcat/arg.py plus tests |
| `policy_states` | ARG `policystates` counts by assignment and complianceState | Counts only |
| `budgets` | GET Consumption budgets per subscription and management group (version 2026-06-01, fallback to be decided at doctor time) | Keep amounts and booleans; drop email addresses |
| `anomaly_rules` | GET scheduledActions per subscription, kind InsightAlert | Visibility of shared vs private rules UNVERIFIED, so low confidence |
| `cost_exports` | GET exports per subscription and management group, `$expand=runHistory` | Redact storage account ids |

Allowlist impact: none for GETs (management.azure.com GET is already allowed). The ARG option is a body field on an already allowed POST. No ADR needed. Record in docs/decisions as a note when built.

### Tag-hygiene checks
| Id | Finds | Confidence cap | Notes |
|---|---|---|---|
| TAG-DISC-01 | Info: the discovered scheme, its source, key list with coverage and distinct value counts | medium | Always runs. "No tags at all" is reported here as the headline, not as thousands of findings |
| TAG-COV-01 | Subscription (or resource group) whose share of taggable resources lacking the scheme keys is above a threshold | medium | Denominator excludes types that never carry a tag in this estate when others do ("evidently untaggable"), pending the tag-support table. Threshold is our proposal, echoed in the finding |
| TAG-CASE-01 | Same tag name in different casings across resources | medium | Learn: names are case-insensitive for operations but casing shows in cost reports. Whether Cost Management merges them is UNVERIFIED, so wording is "may split reporting" |
| TAG-VAL-01 | Same key, values equal ignoring case, whitespace or trailing punctuation (`Prod`, `prod`, `prod `) | medium | Learn: values are case-sensitive and appear as separate rows in cost reports. Synonyms (`prod` vs `production`) are NOT claimed, only listed as "possible" when edit distance is tiny |
| TAG-RG-01 | Resource groups carrying scheme tags that are absent on most of their resources, with no inheritance policy and no known Cost Management inheritance | low | Cost Management inheritance setting cannot be read yet (path UNVERIFIED), so the finding says "no inheritance policy found; Cost Management inheritance not assessed, because the setting is not yet readable" |
| TAG-SENS-01 | (considered, NOT proposed) values that look like secrets | n/a | High false positive risk and the tool would have to read values; skipped on purpose |

## 4. Governance checks (Reader, GET or ARG only)
| Id | Finds | Cap | Source facts |
|---|---|---|---|
| POL-TAG-01 | No tag enforcement policy visible; or only audit / DoNotEnforce | medium | FinOps says start with audit and expand, so audit-only is Partial, not a defect |
| POL-TAGMODE-01 | Tag policies use deny only, no modify or inherit (existing resources unaffected) | low | tag-policies page: append does not touch existing resources; modify needs a remediation task |
| POL-EXEMPT-01 | Policy exemptions with no expiry or already expired | low | Property names UNVERIFIED |
| POL-COMPL-01 | Non-compliance share for tag policies, per assignment | medium | Counts from policystates |
| POL-GUARD-01 | Info: cost guardrail policies present (allowed locations, SKUs, resource types) | low | Built-in GUIDs must be read from Learn first (UNVERIFIED now) |
| BUD-COVER-01 | Subscription with no budget at subscription scope, management group scope above it, or resource group | medium | CAF: budget and alerts on each subscription. Whether a management group budget covers its children is UNVERIFIED; shown as "covered by MG budget" separately |
| BUD-ALERT-01 | Budget with no enabled notification, or none with a recipient | high-ish, capped medium | Fields verified in the list REST page |
| BUD-FCST-01 | No forecast-type threshold on a subscription's budgets | low | FinOps budgeting: alert on actual and forecast |
| BUD-EXP-01 | Budget whose end date has passed | medium | Learn: a budget monitors only while valid |
| BUD-OVER-01 | Info: current spend above the budget amount | low | `currentSpend` presence UNVERIFIED live |
| ALR-ANOM-01 | Subscription with no visible anomaly alert rule | low | Public cloud only; shared vs private visibility UNVERIFIED; wording "not visible to this identity" |
| EXP-CFG-01 | No cost export visible at any scope, or last run Failed / DataNotAvailable | low to medium | Exports list with runHistory verified |
| STR-MG-01 | Subscriptions directly under tenant root, or policy assigned per subscription instead of management group | low | CAF landing zone guidance; Reader visibility of hierarchy is partial |

Not built in this layer, on purpose: cost allocation rules (billing account scope, a Reader on subscriptions cannot see them: "not assessed, because the allocation rules live on the billing account"), locks (not in ARG, low cost value), reservation and savings plan governance (own area, other roles), untagged cost share (needs Cost Management Query, see phase 2).

## 5. Phases
| Phase | Scope | Needs |
|---|---|---|
| 1 | Tag discovery and hygiene (TAG-*), policy tag checks (POL-TAG-01, POL-TAGMODE-01, POL-COMPL-01), ARG scope filter option | Reader only, no new ADR |
| 2 | Budgets, anomaly alert visibility, exports (BUD-*, ALR-*, EXP-*), governance posture view in the dashboard (the section in mock-up A) | Reader, GET only, no new ADR |
| 3 | Cost-weighted measures: untagged cost share, cost by scheme key, via Cost Management Query (ADR 0006 stage 1 already approved). Needs the grouping-by-tag request shape verified first | Cost Management Reader |
| 4 | Tag inheritance setting, locks, reservation governance | Each needs its own read path verified first |

## 6. Privacy and safety rules specific to this layer
- Budget and scheduled-action responses contain email addresses; export responses contain storage account ids; tag values may contain people's names. Collectors project only counts, booleans and shapes. Values are stored only for keys with at most N distinct values. `--redact` must cover anything that slips through. Add to docs/THREAT-MODEL.md when built.
- Tag values are not shown in findings except as variant shapes (for example `prod` / `Prod`) for low-cardinality keys.
- All thresholds (50 percent scheme share, 20 distinct values, coverage cut-offs) are our proposals and are echoed in the finding detail so the reader can disagree.
- Every governance check declares `NotAssessed` when its collector returns 401/403/404 (for example no budget read rights, or a subscription type with no Cost Management data), never an empty pass (lesson M-008).

## 7. Test plan (same bar as existing checks)
Per-check fixtures with a positive and a negative case; synthetic estate gains tagged and untagged resources, two casings of one key, a budget without alerts, an expired budget, a subscription with an anomaly rule; golden report regenerated with hand-derived assertions; PARITY row per check; KQL column contract test for the new collectors; fuzz and metamorphic tests apply automatically. One extra metamorphic property for tags: relabelling a key's casing in every resource must not change coverage.

## 8. Open questions for the owner (answers change what gets built)
1. Layer shape: findings plus the three-state posture view (recommended), or findings only for now?
2. Tag standard precedence: policy-declared, then config, then inferred. Agree? And is it acceptable that with no evidence the tool says "no scheme evident" instead of judging against a default list?
3. Privacy: store tag values only for low-cardinality keys, never emails or storage ids. Agree?
4. First build: phase 1 only, or phases 1 and 2 together (both are Reader-only, GET and ARG)?
5. Phase 3 (cost-weighted tag coverage) is the more meaningful measure for a CIO, since it asks how much money is unallocated, but it needs Cost Management Reader and a verified request shape. Plan it now or later?

## 9. Owner decisions (2026-10-20)
1. Findings plus posture view. 2. Tag standard precedence policy, then config, then inferred. 3. Phase 1 only first. 4. Store ALL tag values (owner overrode my recommendation to keep values only for low-cardinality keys). Consequences: `tag_values` has no distinct-value cap; the snapshot and any report showing values are customer data; `--redact` must mask tag values; findings may show value variants. Emails and storage ids in phase 2 payloads are still not stored.

## 10. Build status (2026-10-20)
Phase 1 built offline: TAG-DISC-01, TAG-COV-01, TAG-CASE-01, TAG-VAL-01, TAG-RG-01, POL-TAG-01, POL-TAGMOD-01 (renamed from POL-TAGMODE-01, id pattern), POL-COMPL-01. All `offline-only`, never run on a real tenant. Differences from the design: (1) the `[tags] required` config override is NOT built, so scheme precedence is policy, then inferred; (2) `tag_values` is folded into `tag_inventory` (all values stored); (3) POL-EXEMPT-01 and POL-GUARD-01 not built. Thresholds in src/fcat/tags.py (50 percent scheme share, 25 percent gap, 10 resource minimum, resource group 3 and 50 percent) are our proposals and are echoed in findings. See ADR 0008 and the THREAT-MODEL entry for tag values.
