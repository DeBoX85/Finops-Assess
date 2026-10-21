# Cost data collector and reconciliation (built offline 2026-10-21, opt-in)

Status: `offline-only` until gate G2 passes. Switch: `[run] cost_apis = true` (default false). Code: `src/fcat/costdata.py`, `src/fcat/checks_cost.py`. Allowlist: ADR 0006 stage 1 (Cost Management Query POST, already approved). Nothing is written to Azure.

## What it does
1. ARG collector `resource_ids`: every resource id (lower-cased), type and subscription, with the usual paging. This is large on big estates, which is why it is opt-in.
2. REST collector `cost_by_resource`: one POST to `/subscriptions/{id}/providers/Microsoft.CostManagement/query` per enabled subscription. Body: ActualCost, timeframe `TheLastMonth`, aggregation Sum of Cost, grouping by dimension ResourceId. Pages are followed through `nextLink` (max 20), which must pass the same allowlist.
3. Check COST-UNMAP-01: per subscription, the share of last month's cost that sits on (a) ids not in the id list and (b) lines with an empty ResourceId. Reported at 5 percent or more (my judgement, constant `SHARE_THRESHOLD`). Info severity, low confidence: it asks the owner to explain money, it never claims waste.

## Refuses to decide ("not assessed, because")
Id list truncated; no subscription query finished; query cut off at the page limit; a subscription reports more than one currency (never add across currencies); the opt-in is off (the reason text names the switch).

## Sources (Learn, REST reference "Query - Usage", api-version 2026-06-01, read 2026-10-21)
Request and response shape as in the docstring of `costdata.py`. 429 handling reads `x-ms-ratelimit-microsoft.consumption-retry-after` as well as `retry-after` (http.py).

## UNVERIFIED (first G2 session, in this order)
1. Reader or Cost Management Reader is enough for the Query on this tenant type; EA and MCA view-charges settings can block it.
2. Cost column name (samples show PreTaxCost; the parser accepts Cost or PreTaxCost and errors on anything else).
3. ResourceId case and format (we lower-case both sides) and which billing lines carry no ResourceId (support, marketplace, reservations are guesses).
4. Whether nextLink is followed with POST and the same body.
5. `ActualCost` accepted on every offer type; throttling at scale (QPU limits are in KB 10; this collector makes one call per subscription).
6. Whether TheLastMonth is the right window for deleted-resource detection (a resource deleted this month is not "missing" last month).

## Redaction
`details.top_missing[].id` is pseudonymised by `--redact` (redact.py `RESOURCE_ID_LIST_KEYS`). Any new details key that holds resource ids must be added there; the synthetic-estate redaction test catches a leak.
