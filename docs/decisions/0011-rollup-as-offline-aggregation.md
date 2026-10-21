# 0011 Roll-up as an offline aggregation of finished reports
Date 2026-10-21. Status: ACCEPTED by me as a first step under the owner's standing instruction (option B, switchable); the owner may ask for more.
Context: owner chose option B (one customer, several tenants or scopes) and asked for a way to switch it on or off (backlog 41). The earlier design was a `[scopes]` list so one run covers several scopes.
Options: (A) `[scopes]` driven collection in one run, which needs one token per tenant and a batch loop; how AzureCliCredential behaves across tenants, with MFA and conditional access, is UNVERIFIED and cannot be tested without tenants. (B) `fcat rollup` over finished single-scope reports (chosen).
Decision: build B. Each scope keeps its own login, config and output folder. The roll-up shows counts, self-audit result, tool version, and which checks did not run, in rollup.json, rollup.md and rollup.html. It contains no resource, subscription or tenant ids and no amounts. Switch: run the command or do not.
Consequences: nothing in the single-scope default path changed. No de-duplication between scopes (stated in every output). A `[scopes]` batch run and a dashboard roll-up view remain possible later and would reuse `rollup.build`.
UNVERIFIED: whether operators find the manual per-scope runs acceptable.
