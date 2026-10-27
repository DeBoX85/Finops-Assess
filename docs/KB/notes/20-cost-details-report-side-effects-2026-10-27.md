# KB 20: Cost Details report API, side effects and fit (backlog 49, ADR 0006 stage 2). Read 2026-10-27

Question from the owner: does `generateCostDetailsReport` have side effects beyond a temporary report, and is it worth stage 2? No code was written.

## Sources (whole pages fetched or search excerpts, read 2026-10-27)
- REST reference, Create Operation (api-version 2026-06-01): https://learn.microsoft.com/en-us/rest/api/cost-management/generate-cost-details-report/create-operation (fetched in full)
- https://learn.microsoft.com/azure/cost-management-billing/costs/manage-automation (fetched in full)
- https://learn.microsoft.com/azure/cost-management-billing/automate/get-small-usage-datasets-on-demand (search excerpt: permissions, EA/MCA only)
- https://learn.microsoft.com/azure/cost-management-billing/automate/usage-details-best-practices (search excerpt)
- https://learn.microsoft.com/azure/cost-management-billing/costs/understand-work-scopes (search excerpt: roles table)
- https://learn.microsoft.com/azure/cost-management-billing/cost-management-billing-faq (search excerpt: API is free)

## What Learn states (VERIFIED, on the pages above)
1. It is a POST to `{scope}/providers/Microsoft.CostManagement/generateCostDetailsReport`. Request: `metric` (ActualCost or AmortizedCost) plus ONE of `timePeriod`, `billingPeriod` (EA only) or `invoiceId` (MCA, billing profile or customer scope only). Responses: 202 with `Location` and `Retry-After`, 200 with the result, 204 no content.
2. Asynchronous: poll the `Location` URL; on completion the body has `manifest.blobs[].blobLink`, `byteCount`, `status` (Completed, NoDataFound, Failed) and `validTill`. The sample blob host is a Microsoft-owned storage account name of the form `ccmreportstorage<region>.blob.core.windows.net`, with a SAS query string. The page says the link expires; the automation article says "typically one hour".
3. Limits: one month or less per request; no data older than 13 months; 429 when throttled (honour `Retry-After`); 503 possible. Best practice: at most once per day per scope and date range, because data refreshes every four hours.
4. Supported scopes: subscription and billing scopes are shown in the reference examples. Resource group and management group are NOT supported ("Currently Resource Group and Management Group are not supported").
5. Account types: the API is "only supported for Enterprise Agreement (EA) or Microsoft Customer Agreement (MCA) scopes" (manage-automation) and "not available" for pay-as-you-go, MSDN and Visual Studio subscriptions (usage-details-best-practices). For those, Learn points to Exports or the Consumption Usage Details API.
6. Permissions: "read only permissions for supported features and scopes" (get-small-usage-datasets-on-demand); at subscription scope Cost Management Reader is the minimum role to see cost data (assign-access-acm-data); EA additionally needs the "AO view charges" setting. Cost Management Reader can view cost data and cost configuration but cannot create budgets or exports (understand-work-scopes table).
7. Cost: the Cost Details API is free (FAQ), subject to rate limits.
8. Size: about 1 GB is roughly 1 million rows; Learn advises Exports above about 2 GB per month.

## Side effects: what I can and cannot say
- VERIFIED on the pages: the call "generates a report" that is downloaded from a time-limited link on Microsoft-hosted storage. No page says it creates anything in the customer's subscription, and the Cost Management Reader role cannot create exports or budgets, which is consistent with that.
- NOT stated either way (UNVERIFIED, I found no sentence): how long Microsoft keeps the generated blob after `validTill`, and whether the request is visible in the customer's Activity Log. I would expect a POST to be logged as a management operation, but that is speculation.
- Consequence for rule 1 ("read-only toward Azure"): the POST is a write in HTTP terms but not a change to the customer's configuration. It would need an explicit, narrow allowlist entry (POST to this one path only) and a plain statement to the customer, same pattern as the Query and Forecast POSTs in ADR 0006 stage 1.

## What stage 2 would add that stage 1 cannot (my assessment, partly speculation)
- Needs a SECOND new network permission: GET of the blob link on a Microsoft storage host. This host is not management.azure.com, so the allowlist would need a host rule scoped to the host pattern seen above, to GET only, and to links returned by the API. The exact host pattern across regions is UNVERIFIED (only one sample host seen).
- More customer data on the laptop: unaggregated rows with resource names and ids, and tags. The owner already decided to store all tag values (2026-10-20), so snapshots are customer data; this makes them larger.
- Records show `PricingModel` (OnDemand, Reservation, SavingsPlan, Spot) and `ChargeType` (Usage, Purchase, Refund, UnusedReservation, UnusedSavingsPlan) per the Learn field reference. Share of spend by pricing model is a commitment coverage proxy that needs Cost Management Reader only, not a billing role. SPECULATION to test: the Query API (stage 1) may be able to group by those dimensions already, which would avoid stage 2. I did not confirm the Query API's dimension names on Learn today.
- Does not work for pay-as-you-go or Visual Studio (Startups credits are often not EA or MCA: UNVERIFIED for the owner's tenant).

## Recommendation (mine, for the owner to overrule)
Do not build stage 2 yet. First test on a real tenant whether the Query API can group by PricingModel and ChargeType; if yes, that covers the commitment coverage proxy with no new allowlist rule. Build stage 2 only if a customer on EA or MCA needs per-charge detail the Query API cannot give.
