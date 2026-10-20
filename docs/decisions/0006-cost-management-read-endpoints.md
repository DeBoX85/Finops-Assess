# 0006 Allowlist for Cost Management read endpoints (ACCEPTED IN TWO STAGES 2026-10-20)
Date 2026-10-18. Status: owner approved a two-stage rollout on 2026-10-20.
- Stage 1 (implemented in src/fcat/http.py with tests): POST `{scope}/providers/Microsoft.CostManagement/query` and `/forecast`, scope = subscription, resource group or management group (billing scopes later, after the test-tenant facts), dated non-preview api-version required. GET already allowed on management.azure.com, so budgets, exports (list only), dimensions and settings need no change.
- Stage 2 (NOT allowed yet): generateCostDetailsReport and the blob download. Waits for confirmation in the REST reference that report generation has no side effect beyond a temporary report. Learn (read 2026-10-20) describes it as an asynchronous report-generation call returning 202 with a Location header, polled until a blobLink appears, with the download URL expiring after about an hour; it does not state side effects either way, so this stays UNVERIFIED.
Original proposal follows.

Why: cost checks need Query, Forecast and Cost Details. These are read operations but use POST (Learn: manage-automation, read 2026-10-18), and Cost Details returns a short-lived blob download link on a different host. Rule 1 stays: nothing changes in the tenant.
Proposed additions (each a path regex, per method, scope-prefixed, api-version pinned):
- POST {scope}/providers/Microsoft.CostManagement/query (cost and usage aggregates)
- POST {scope}/providers/Microsoft.CostManagement/forecast
- POST {scope}/providers/Microsoft.CostManagement/generateCostDetailsReport, then GET its operation URL (report generation is asynchronous; it creates a temporary report, not a tenant resource; UNVERIFIED that it has no side effects beyond that, confirm in the REST reference before accepting)
- GET budgets, exports (list only), scheduledActions, dimensions, settings
- Download: GET only to the blobLink returned by the API, HTTPS, host ending .blob.core.windows.net, no other blob hosts, never user-supplied
Explicitly still blocked: PUT, PATCH, DELETE, POST .../exports/{name}/run, any other POST. Export write mode stays under ADR 0005 and a separate client.
Required tests: each allowed path matches and a near-miss path is refused; PUT/DELETE/PATCH on the same paths refused; /run refused in the default client; blob host check refuses lookalike hosts (e.g. evil-blob.core.windows.net.example.com); architecture test that only http.py contains verbs.
Rate limits to honour: QPU 12 per 10 s, 60 per minute, 600 per hour per tenant, 1 QPU per month queried; read x-ms-ratelimit-microsoft.costmanagement-qpu-* headers; call at most once per day per scope in normal use (KB note 10).
Owner decision needed: OK to widen the allowlist as listed?
