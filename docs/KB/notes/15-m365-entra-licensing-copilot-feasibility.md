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
