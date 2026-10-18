# 10 Cost Management data by billing type, APIs, limits (read 2026-10-18)
Sources: Learn "Understand Cost Management data" (understand-cost-mgt-data), "Get started with Cost Management for partners" (get-started-partners), "Manage costs with automation" (manage-automation), "Tutorial: Create and manage exports", "Understand and work with scopes", Exports Execute API reference. All fetched 2026-10-18 via the Microsoft Learn tools. A pasted third-party research report was used only as a checklist; each point below is tagged by what I verified myself.

## Supported and unsupported offers (VERIFIED, understand-cost-mgt-data)
- Supported: EA, Microsoft Customer Agreement (MCA, "Microsoft Azure Plan"), MCA supported by partners (data from Oct 2019), pay-as-you-go, Dev/Test, MSDN/Visual Studio, Free Trial, Azure in Open, Azure Pass.
- NOT supported: classic CSP (CSP_2015-05-01), EA Azure Sponsorship, Microsoft Azure Sponsorship (Sponsored_2016-01-01), Azure for Students, support plans.
- Footnote: quota IDs are the SAME across MCA and classic subscription offers, so a quota ID alone cannot always tell supported from unsupported CSP. Implemented as 'depends' in src/fcat/billing.py (never guessed).
- UNKNOWN: which offer an "Azure for Startups" subscription uses. I believe sponsorship-type offers are used for credit programmes, but I have NOT verified this. If it is Sponsored_2016-01-01, there is no Cost Management data for it. Owner can read the Offer / quota ID in the portal; the tool will read it via ARG (properties.subscriptionPolicies.quotaId, same property the toolkit workbooks use).
## What is and is not in the data (VERIFIED)
Included: Azure usage (incl. deleted resources), Marketplace usage and purchases, commitment discount purchases and amortisation (EA and MCA only), New Commerce products. NOT included: support charges, taxes, credits, free tier. MOSA (pay-as-you-go): no Marketplace or commitment purchases. Costs are estimated until invoiced, and the open month uses the highest tier price. New subscriptions can take up to 48 h. EA/MCA data typically 8 to 24 h, pay-as-you-go up to 72 h. Portal and APIs: last 13 months; older data via Exports API. Query API returns 8 decimals unrounded; Cost analysis rounds for display.
## CSP on MCA (the owner's CSP test tenant, if on an Azure plan) (VERIFIED, get-started-partners)
- Customers see cost only if the partner enables the cost visibility policy (disabled by default). When enabled, subscription users see usage at PAY-AS-YOU-GO RETAIL rates, not the partner's invoiced price, and costs exclude partner discounts and credits.
- Reservation usage shows ZERO actual and amortised cost at the subscription scope; reservation purchases and entitlements are shown.
- Management group exports are not supported for MCA or CSP subscriptions (FinOps hubs doc, as of May 2024; may have changed).
- Design consequence: for CSP customers, "actual cost" is retail, not what the customer pays. Savings figures must say so ("at pay-as-you-go retail rates"). Actual vs list comparison is meaningless there. Reservation coverage cannot be read from cost data.
## APIs and limits
- Query API: read-only POST. Quotas per tenant: 12 QPU/10 s, 60/min, 600/hour; 1 QPU per month of data queried (may change). Headers: x-ms-ratelimit-microsoft.costmanagement-qpu-retry-after / -consumed / -remaining (VERIFIED). Docs recommend calling at most once per day since data refreshes every 4 hours (VERIFIED).
- Cost Details API: POST generateCostDetailsReport (api-version 2025-03-01 in the doc example), poll, download via blobLink (short-lived URL, typically 1 hour). EA and MCA scopes only; other account types use Exports (VERIFIED). Does not need a storage account. The "one month maximum" and "no management group scope" claims in the pasted report: UNVERIFIED by me.
- Exports: creating is a PUT, running is POST /run (Exports_Execute, default api-version 2025-03-01 in the SDK reference). Needs a storage account. See ADR 0005.
- Hard-rule impact: Query and Cost Details are POST requests that read data. The current allowlist (src/fcat/http.py) permits POST only to Resource Graph. Widening it needs its own ADR and tests that PUT/DELETE stay blocked.
## Billing account scopes (partly verified)
Partner tenant billing scopes: billing account, billing profile, customer. Only Admin agent / billing admin in the partner tenant can use them. The owner's access in the CSP customer tenant is subscription RBAC scope only (VERIFIED from the partner doc). EA and MCA direct billing scopes need billing roles (not researched in depth, UNVERIFIED).
## Implemented from this note
src/fcat/billing.py (classify quota IDs), subscriptions collector now projects quotaId, check BILL-OFFER-01 (info finding per subscription whose cost data is unsupported or ambiguous), fixtures, golden report updated.
## Open questions for the owner
1. Is the CSP tenant on an Azure plan (MCA via partner) or classic CSP, and is the cost visibility policy enabled? 2. What Offer / quota ID does the startups subscription show in the portal (Subscription overview)?
