# 0002 ARG access: REST, explicit paging, throttling
Date 2026-10-17. Status: accepted.
Decision: call POST https://management.azure.com/providers/Microsoft.ResourceGraph/resources?api-version=2022-10-01 directly; do not shell out to `az graph query`.
Rules (all from Learn, read 2026-10-17):
- Max 1000 rows per page; follow $skipToken with the same query/scope; each page uses one quota unit.
- No $skipToken if the query uses limit/take/sample or all output columns are dynamic/null; keep `id` in the output. A truncated result without a token raises IncompleteResult; never accept silently.
- Honour x-ms-user-quota-remaining / x-ms-user-quota-resets-after, and 429 Retry-After. ARM throttling is separate and wins.
- Use `order by` so paging is repeatable (the client warns otherwise).
- subscriptions and managementGroups cannot be combined; tenant scope = omit both. At most 10,000 subscriptions per response (header x-ms-tenant-subscription-limit-hit).
UNVERIFIED: JSON names resultFormat/allowPartialScopes (not used yet); behaviour with Lighthouse-delegated scopes; live behaviour of any query (no tenant tested).
Auth: azure-identity AzureCliCredential: no claims-challenge support, no token cache (we cache), 10 s default timeout (we use 30). Conditional-access step-up tenants may need another sign-in method (untested).
Sources: https://learn.microsoft.com/azure/governance/resource-graph/concepts/work-with-data ; .../guidance-for-throttled-requests ; .../first-query-rest-api ; https://learn.microsoft.com/python/api/azure-identity/azure.identity.azureclicredential
