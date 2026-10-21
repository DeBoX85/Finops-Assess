# KB 15: Microsoft 365 / Entra licences and Copilot costs, feasibility for F-CAT (2026-10-21)

Trigger: owner asked whether licences (Entra, M365) and Copilot costs can be added, and whether it should be switchable. Method: Microsoft Learn search results read 2026-10-21 (snippets, not every page in full). Nothing was run against a tenant. Everything here is `offline-only` thinking until a live test.

## What is readable (VERIFIED from the Learn pages named, read 2026-10-21)
| Need | Endpoint | Permission (least privileged) | Source |
|---|---|---|---|
| Purchased vs consumed units per SKU | GET /subscribedSkus (has consumedUnits, prepaidUnits) | LicenseAssignment.Read.All, application or delegated | https://learn.microsoft.com/graph/api/subscribedsku-list?view=graph-rest-1.0 |
| Per-user licence assignment | GET /users?$select=assignedLicenses with $filter on assignedLicenses | User.Read.All (as used in the Learn PowerShell page) | https://learn.microsoft.com/microsoft-365/enterprise/view-licensed-and-unlicensed-users-with-microsoft-365-powershell |
| Per-user licence detail incl. group-based | GET /users/{id}/licenseDetails | LicenseAssignment.Read.All, delegated only. Application: not supported | https://learn.microsoft.com/graph/api/user-list-licensedetails?view=graph-rest-1.0 |
| Last sign-in per user (inactive licensed users) | GET /users?$select=signInActivity | AuditLog.Read.All; needs Entra ID P1 or P2 in the tenant; not returned for users who never signed in or last signed in before April 2020. The troubleshooting page says Directory.Read.All is also needed. | https://learn.microsoft.com/graph/api/user-list?view=graph-rest-1.0 and https://learn.microsoft.com/troubleshoot/entra/entra-id/users-groups-entra-apis/b2c-or-tenant-premium-license-sign-in-activities |
| Copilot usage per licensed user (last activity dates, prompts in report v2) | GET /copilot/reports/getMicrosoft365CopilotUsageUserDetail(period=...) | Reports.Read.All; delegated needs a role such as Reports Reader. Global cloud only (not US Gov or China). Only users with a Microsoft 365 Copilot licence; unlicensed Copilot Chat usage is not in this API. | https://learn.microsoft.com/microsoft-365/copilot/extensibility/api/admin-settings/reports/copilotreportroot-getmicrosoft365copilotusageuserdetail |
| Copilot pay-as-you-go cost | Azure Cost Management, filter by meter (Copilot Studio meter) or by the Power Platform account resource | Azure cost read (already planned under ADR 0006) | https://learn.microsoft.com/power-platform/admin/pay-as-you-go-usage-costs , https://learn.microsoft.com/microsoft-365/copilot/pay-as-you-go/pay-as-you-go-meters |

## What is NOT reachable on the path F-CAT already has
- Prepaid Capacity pack consumption is not in Azure Cost Management (Learn says to use the M365 or Power Platform admin center). Source: https://learn.microsoft.com/microsoft-365/copilot/usage-based-billing-compare-dashboard-views
- Copilot Cowork and Work IQ API billing are managed in the Microsoft admin center, not through the Azure meter path (same pages). Whether any API exposes that cost: DON'T KNOW.
- Seat prices: I saw no price field in the SKU objects in what I read (UNVERIFIED that none exists). Saving estimates for seats would need owner-supplied or agreement prices.

## Consequences for the project
1. New host (graph.microsoft.com) and a different token audience: needs a new allowlist ADR (rule 1 stays: GET only).
2. Azure Reader RBAC is not enough. The customer must grant Graph application permissions with admin consent, or a person with a suitable Entra role signs in. This breaks the Reader-first simplicity, so it must be opt-in and have its own `fcat doctor` probe.
3. Per-user data (UPNs, sign-in dates, Copilot activity per person) is personal data. Default must be aggregate counts only; per-user detail opt-in, masked by `--redact`, and never in the customer file unless the owner decides.
4. Possible checks (all `offline-only` until G2): purchased vs assigned units; licensed accounts that are disabled; licensed users with no sign-in for N days (needs P1/P2); Copilot seats with no activity in 30 or 90 days; overlapping SKUs (needs the service plan reference, https://learn.microsoft.com/entra/identity/users/licensing-service-plan-reference); Copilot pay-as-you-go spend present or absent.
5. A live test needs a tenant with M365 licences. DON'T KNOW whether a developer tenant is available to the owner.

## Clarification from owner (2026-10-21)
The Copilot goal is: extract and assess the RUNNING COST when a customer has Copilot enabled (not only seat utilisation). Cost layers, by how F-CAT could see them:
1. Seats (Microsoft 365 Copilot licence): count readable from /subscribedSkus; price NOT readable (owner or agreement input); utilisation from the Copilot usage report.
2. Pay-as-you-go consumption (Copilot Chat agents, SharePoint agents, Studio messages): billed to an Azure subscription, readable in Cost Management by meter or by the Power Platform account resource. Learn lists the Copilot Studio meter at $0.01 per message and the Retrieval API preview at $0.10 per call (read 2026-10-21; prices change, do not hard-code).
3. Not visible via Azure: prepaid Capacity packs, Copilot Cowork, Work IQ API (Microsoft admin center). DON'T KNOW if an API exists.
4. Detecting "enabled": Copilot SKU in subscribedSkus (Graph); a pay-as-you-go billing plan shows as a Power Platform account resource in the Azure subscription (Learn, power-platform/admin/pay-as-you-go-usage-costs). The exact ARG resource type name is UNVERIFIED.
Open: which Copilot products are in scope (M365 Copilot, Copilot Chat PAYG, Copilot Studio, GitHub Copilot, which is billed outside Azure as far as I know: UNVERIFIED).

## Entra licences and usage (Learn pages read 2026-10-21)
- Entitlements: the Entra admin center "License usage" page (Billing > Licenses) rolls up P1, P2, Suite, ID Governance etc. into one count per tier, because several products include each tier. Least privileged role: Reports Reader. Public clouds only. https://learn.microsoft.com/entra/fundamentals/concept-license-usage-insights
- Usage there is one "hero metric" per tier: P1 = unique users with at least one Conditional Access policy evaluated; P2 = users with at least one risk-based Conditional Access policy evaluated; last month, up to 3 days delay. A Graph API for these numbers: NOT FOUND in my reading, so DON'T KNOW. Do not assume it exists.
- Licences are needed per user who benefits from a feature (Learn Q&A answer, not an official page: treat as UNVERIFIED wording); PIM needs P2 or ID Governance for eligible users, approvers and reviewers (https://learn.microsoft.com/entra/id-governance/licensing-fundamentals). So F-CAT must not claim licence compliance, only prompt a check.
- When P1 licences expire, Conditional Access policies are not auto-disabled (https://learn.microsoft.com/entra/identity/conditional-access/overview).
- Any Azure tenant is an Entra tenant, so SKU inventory could be live-tested without M365; P1/P2 sign-in data needs P1 or P2 in the tenant. Trial availability: UNVERIFIED.
- 2026-10-21 owner decisions: licensing and Copilot module PARKED until G2; owner has no M365 test tenant.
