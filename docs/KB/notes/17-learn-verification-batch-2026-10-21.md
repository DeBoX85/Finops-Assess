# KB 17: Learn verification batch (read 2026-10-21)

Goal: shrink the UNVERIFIED list with facts that Microsoft Learn can settle without a tenant. Tags: VERIFIED = stated on the page named, read 2026-10-21 through the Learn search tool (excerpts, not whole pages unless said). Anything not stated stays UNVERIFIED.

| # | Question | Answer | Tag | Source | Effect on the tool |
|---|---|---|---|---|---|
| 1 | Activity Log retention | 90 days, then deleted; longer needs a diagnostic setting | VERIFIED | https://learn.microsoft.com/azure/azure-monitor/fundamentals/activity-log | IDLE-VMDEAL-01 never infers age from a missing entry |
| 2 | Does a missing PowerOff entry prove a VM is stopped for over 90 days? | No (Microsoft Q&A accepted answer; guest shutdown and host events are not always logged; the log is capped at 90 days) | VERIFIED as a statement on that page; it is a community answer, so medium reliability | https://learn.microsoft.com/answers/a/12255469 | same |
| 3 | Is deallocated billed? | Compute not billed; disks and networking continue to incur charges | VERIFIED | https://learn.microsoft.com/azure/virtual-machines/states-billing | wording of IDLE-VMDEAL-01 |
| 4 | Does the instance view status have a time? | The SDK model InstanceViewStatus has `time` ("The time of the status"). Whether the PowerState status carries it, and whether Resource Graph returns it in properties.extended.instanceView.powerState, is not stated | model field VERIFIED; the power-state value UNVERIFIED | https://learn.microsoft.com/javascript/api/@azure/arm-compute/instanceviewstatus | collector projects `powerTime`; the check refuses to decide without it |
| 5 | Is `microsoft.devtestlab/schedules` in Resource Graph? | Listed in the `resources` table reference (item 489 in the list read) | VERIFIED (type listed); property names (status, targetResourceId, taskType) still UNVERIFIED | https://learn.microsoft.com/azure/governance/resource-graph/reference/supported-tables-resources | IDLE-VMSHUT-01 premise supported |
| 6 | Is `microsoft.storage/storageaccounts/managementpolicies` in Resource Graph? | NOT seen. The sorted `resources` list around Storage shows StorageAccounts, storageaccounts/connectors, storagetasks and no managementpolicies. Inference from an excerpt of a sorted list, so likely but not certain; other tables not checked | UNVERIFIED, leaning NO | same page as 5 | OPT-STORLC-01 probably returns "not assessed" on every tenant. See backlog 44 |
| 7 | Policy exemption properties | exemptionCategory (Waiver or Mitigated), expiresOn (optional, UTC ISO 8601), policyAssignmentId, policyDefinitionReferenceIds, displayName, description, metadata. An expired exemption is not deleted but no longer honoured | VERIFIED | https://learn.microsoft.com/azure/governance/policy/concepts/exemption-structure ; https://learn.microsoft.com/azure/templates/microsoft.authorization/2022-07-01-preview/policyexemptions | POL-EXEMPT-01 property names confirmed (REST list shape still UNVERIFIED) |
| 8 | Budget notification properties | enabled, operator (EqualTo, GreaterThan, GreaterThanOrEqualTo), threshold (percent, 0 to 1000), contactEmails (required array), contactRoles, contactGroups | VERIFIED (API 2018-01-31 template reference; our collector uses 2026-06-01, not compared) | https://learn.microsoft.com/azure/templates/microsoft.consumption/2018-01-31/budgets | projection in govcost.py matches; `currentSpend` presence still UNVERIFIED |

## Honest limits
- Search returns excerpts. Items 5 and 6 rest on an excerpt of a very long list.
- No call was made to Azure. Nothing here upgrades a check from `offline-only`.

## Follow-ups
- Backlog 44: OPT-STORLC-01 needs a per-account ARM read (GET .../storageAccounts/{name}/managementPolicies/default) if item 6 is confirmed; that is N extra calls and needs an ADR for the allowlist.
- On the first G2 session: confirm 4, 5 and 6 first (they decide whether three checks work at all).
