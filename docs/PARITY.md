# Parity matrix: FinOps toolkit workbooks vs F-CAT (2026-10-18)

Source of the workbook list: docs/KB/notes/02-finops-toolkit-workbooks.md (microsoft/finops-toolkit commit f12c29e, read 2026-10-17) and the hub recommendation queries (same commit, re-read 2026-10-18, note 07).
Goal from PLAN: at least parity. Status words: DONE-OFFLINE (implemented, fixtures and golden tests pass, never run on a real tenant, so not verified), PLANNED (in backlog), DIFFERENT (done on purpose in another way), NOT-PLANNED (with reason).
"Check IDs" are validated by tests/test_parity.py: every ID named here must exist in the registry.

## Optimization workbook
| Workbook item | Status | Check IDs / backlog | Note |
|---|---|---|---|
| Unattached disks (with tag/state exclusions) | DONE-OFFLINE | ORPH-DISK-01 | Exclusions copied from the workbook logic; adds evidence and fingerprint |
| Unattached public IPs | DONE-OFFLINE | ORPH-PIP-01 | Also covers IPs attached only to an unattached NIC (hub query) |
| App Gateways with empty backend pools | DONE-OFFLINE | ORPH-AGW-01 | |
| Load Balancers with empty backend pools | DONE-OFFLINE | ORPH-LB-01 | Detects zero pools only, like the hub query; a pool that exists but is empty is not detected |
| Idle VNet gateways | DIFFERENT | ORPH-VGW-01 | Skips point-to-site gateways to avoid false positives; confidence low |
| Idle NAT gateways | DONE-OFFLINE | ORPH-NAT-01 | |
| Idle ExpressRoute circuits | DIFFERENT | ORPH-ERC-01 | Hub query checks provisioning state; workbook wording is "idle". Unclear if the workbook checks traffic (UNVERIFIED) |
| Idle private DNS zones (0 VNet links) | DONE-OFFLINE | ORPH-PDNS-01 | |
| Idle private endpoints (Disconnected) | DONE-OFFLINE | ORPH-PE-01 | Only Disconnected is reported, as in the workbook |
| VMs stopped, not deallocated | DONE-OFFLINE | IDLE-VMSTOP-01 | |
| VMs deallocated, processor type lists | PLANNED | backlog 7 | Inventory style; low value alone |
| Premium disks on powered-off VMs | DONE-OFFLINE | IDLE-VMDISK-01 | Also covers data disks (workbook: OS disk only) |
| Snapshots older than 30 days / premium / source disk deleted | DONE-OFFLINE | ORPH-SNAP-01, ORPH-SNAP-02, ORPH-SNAP-03 | Age uses the snapshot's collection time; source-deleted only judged for scanned subscriptions |
| Storage accounts not v2 | DONE-OFFLINE | MOD-STORV1-01 | Hub query LegacyStorageAccounts |
| Idle backups (last backup > 90 days) | DONE-OFFLINE | IDLE-BKP-01 | See batch 6 below |
| Recovery vault replication GRS vs LRS | DIFFERENT | OPT-VAULT-01 | See batch 6 below |
| Disk last modified date (ARM createdTime/changedTime) | PLANNED | backlog 7 | Needs ARM call beyond ARG |
| Empty App Service plans | DONE-OFFLINE | ORPH-ASP-01 | |
| Empty SQL elastic pools | DONE-OFFLINE | ORPH-EPOOL-01 | |
| Unassociated DDoS plans | DONE-OFFLINE | ORPH-DDOS-01 | |
| Databases "idle over 30 days" | DIFFERENT | none yet | The workbook query matches names containing old/Dev/test and measures no activity. Not copied. Replacement needs Azure Monitor metrics and peak-aware rules (DEV-PRINCIPLES R10) |
| Idle SQL pool / unused Synapse workspaces | DIFFERENT | ORPH-SYN-01 | Workspaces only; idle SQL pool needs metrics |
| Cosmos DB RU reduction, throughput mode, continuous backup | DONE-OFFLINE | ADV-COST-01, OPT-COSBKP-01 | Advisor items via pass-through; backup mode check is ours |
| Azure Hybrid Benefit (Windows, Linux, SQL, VMSS, Coverage summary) | PLANNED | backlog 7 / hub AHB queries | Needs Microsoft.Compute/skus call for vCPU; savings need list price |
| Azure Firewall Premium unused features | DIFFERENT | OPT-FWPREM-01 | See batch 6 below |
| Reservation and savings plan recommendations (Advisor route) | PLANNED | backlog 7 | Reader is enough via advisorresources |
| Commitment discount utilisation, billing-scope recommendations | PLANNED | backlog 26 | Needs billing permissions and Cost endpoints (ADR 0006 pending) |
| Advisor cost recommendations (compute, monitoring) | DONE-OFFLINE | ADV-COST-01 | Passed through with Advisor's own savings, labelled as such |
| Log Analytics ingestion trend (Usage table) | PLANNED | backlog 9 | Needs workspace read; module in monitoring cost assessment |
| Sustainability (Advisor carbon) | NOT-PLANNED (this round) | | Not a cost check; revisit |
| Top 10 services, AKS list, resource distribution | DIFFERENT | cost collectors | Cost views come from cost data, not inventory counts |
| Quick-fix links to delete or change resources | NOT-PLANNED | | Violates read-only rule 1 |

## Governance workbook (66 query titles, grouped)
| Group | Status | Note |
|---|---|---|
| Inventory counts and details | PLANNED | Inventory section of the dashboard; uses collectors already needed |
| Power state of VMs | DONE-OFFLINE | IDLE-VMSTOP-01 covers stopped; full state chart planned |
| Networking inventory (NSGs, public IPs, AppGW, LB) | PARTLY | orphan checks above; inventory counts planned |
| Tagging (tag present, empty value, untagged) | PLANNED | backlog 9; central to allocation maturity |
| Resource age, changes, deletions | PLANNED | ARM createdTime/changedTime |
| Cost by tag, overall cost | PLANNED | Cost endpoints (backlog 26) |
| Security: secure score, Defender alerts, recommendations | PLANNED | backlog 9; cost angle for Defender plans |
| Policy compliance | PLANNED | |
| Quota and limits | NOT-PLANNED (this round) | Capacity management domain; revisit |
| Activity log failures, jobs, disk free space | NOT-PLANNED (this round) | Need Log Analytics data that many tenants lack |

## Hub recommendation queries not in the workbooks
| Item | Status | Check IDs | Note |
|---|---|---|---|
| Unattached network interfaces | DONE-OFFLINE | ORPH-NIC-01 | Severity low; NIC has no direct charge (UNVERIFIED) |
| Empty network security groups | DONE-OFFLINE | ORPH-NSG-01 | Severity low, hygiene |

## Hub queries added in batch 5 (2026-10-18, hub commit f12c29e)
| Item | Status | Check IDs | Note |
|---|---|---|---|
| Basic load balancers (retired 2025-09-30, Learn) | DONE-OFFLINE | MOD-LBBAS-01 | Hub query BasicLoadBalancers |
| Basic public IPs (retired 2025-09-30, Learn) | DONE-OFFLINE | MOD-PIPBAS-01 | Hub query BasicPublicIPs; other timelines for IPs on App Gateway v1 or Basic VPN gateways are UNVERIFIED (Q&A only) |
| Application Gateway v1 (retired 2026-04-28, Learn) | DONE-OFFLINE | MOD-AGWV1-01 | Hub query ClassicAppGateways |
| Unmanaged disks (retired 2026-03-31, Learn) | DONE-OFFLINE | MOD-VMUNMG-01 | Hub query UnmanagedDisks tests for null; ours needs a positive VHD URI (DIFFERENT on purpose) |
| Windows VMs and VMSS without Hybrid Benefit | DONE-OFFLINE | LIC-AHBWIN-01 | Hub query VMsWithoutAHB; Dev/Test exclusion broader; no vCPU or saving (needs Compute SKUs call and list price) |
| SQL Server VMs without Hybrid Benefit | DONE-OFFLINE | LIC-AHBSQL-01 | Hub query SQLVMsWithoutAHB; DR licence type and unknown values are not reported |
| AKS autoscaling pools not on Spot | DIFFERENT | OPT-AKSSPT-01 | Hub query NonSpotAKSClusters; ours lists user pools only (Spot cannot be system pools, Learn), info severity, a prompt not a finding |
| Advisor cost recommendations | DONE-OFFLINE | ADV-COST-01 | Hub query AdvisorCost; pass-through, Advisor's own savings figure labelled and never summed |

## Workbook items added in batch 6 (2026-10-18)
| Item | Status | Check IDs | Note |
|---|---|---|---|
| Idle backups (last backup > 90 days) | DONE-OFFLINE | IDLE-BKP-01 | Same 90-day rule; message does not assume the cause (failing backup versus no longer needed) |
| Recovery vault replication GRS vs LRS | DIFFERENT | OPT-VAULT-01 | Only GRS vaults in Dev/Test-looking subscriptions, info; the workbook just lists redundancy |
| Cosmos DB backup modes (continuous likely cheaper) | DIFFERENT | OPT-COSBKP-01 | Workbook thresholds kept; wording is evaluate, not saving (Learn: continuous mode is one-way and changes restore model) |
| Cosmos DB RU reduction and throughput mode | DONE-OFFLINE | ADV-COST-01 | Covered by the Advisor pass-through, not a separate check |
| Unused Synapse workspaces | DIFFERENT | ORPH-SYN-01 | Info only: serverless SQL costs nothing until queried (Learn), so zero pools does not mean zero use |
| Azure Firewall Premium unused features | DIFFERENT | OPT-FWPREM-01 | Checks IDPS and TLS inspection only; URL filtering and web categories are not inspected, so the message says so |

## Added in batch 7 (2026-10-18)
| Item | Status | Check IDs | Note |
|---|---|---|---|
| VM rightsizing from peak CPU (no workbook equivalent; Advisor has its own) | DONE-OFFLINE | RIGHT-VMCPU-01 | Opt-in (`[run] rightsizing = true`), CPU only, hourly maxima over 30 days, same-family half-size only; built from the documented REST schema, never run live (UNVERIFIED) |

## Added in batch 8 (2026-10-20): cost governance, tag hygiene phase 1
| Item | Status | Check IDs | Note |
|---|---|---|---|
| Tagging scheme discovered from the customer (policy, else inferred, else none) | DONE-OFFLINE | TAG-DISC-01 | No hard-coded required tags. Config override (`[tags] required`) is NOT built |
| Tag coverage gap per subscription | DONE-OFFLINE | TAG-COV-01 | Thresholds (25 percent gap, 10 resources minimum) are our proposals, echoed in the finding |
| Tag name casing variants | DONE-OFFLINE | TAG-CASE-01 | Wording "may split cost reports": merging behaviour in Cost Management is UNVERIFIED |
| Tag value variants (case, space, separators) | DONE-OFFLINE | TAG-VAL-01 | Synonyms are not inferred. Values are customer data, masked by `--redact` |
| Resource group tags not carried by resources | DONE-OFFLINE | TAG-RG-01 | Cost Management tag inheritance setting not readable yet, so not assessed |
| Tag policy presence and enforcement | DONE-OFFLINE | POL-TAG-01 | Audit-only is reported as partial, not a defect (FinOps guidance) |
| Tag policies without modify or inherit | DONE-OFFLINE | POL-TAGMOD-01 | Parameter names verified only for the require-tag built-in |
| Tag policy non-compliance share | DONE-OFFLINE | POL-COMPL-01 | Counts from ARG policy states; compliance timing UNVERIFIED live |

## Added in batch 9 (2026-10-20): cost governance phase 2, budgets, anomaly alerts, exports
| Item | Status | Check IDs | Note |
|---|---|---|---|
| Subscriptions without a budget | DONE-OFFLINE | BUD-COVER-01 | Subscription scope only; management group budgets not collected, so wording is "visible at subscription scope". Needs `[run] governance_apis = true` |
| Budgets that cannot alert anyone | DONE-OFFLINE | BUD-ALERT-01 | E-mail addresses are never stored, only whether any exist |
| No forecast alert on budgets | DONE-OFFLINE | BUD-FCST-01 | FinOps budgeting guidance (actual and forecast); confidence low |
| Budgets past their end date | DONE-OFFLINE | BUD-EXP-01 | Judged against collection time, not the wall clock |
| Anomaly alert rule visibility | DONE-OFFLINE | ALR-ANOM-01 | Shared vs private rules UNVERIFIED, so a miss is "not visible to this identity" |
| Cost export missing, paused or failing | DONE-OFFLINE | EXP-CFG-01 | Storage ids, containers and folders are never stored |

## Beyond the workbooks (F-CAT only, today)
Monitoring and security tier A (docs/MODULE-MONITORING-SECURITY.md): MON-LAWCAP-01, MON-AICLS-01, SEC-DEFDEV-01 (all informational, confidence low). Billing-offer awareness (BILL-OFFER-01), self-audit of every report, evidence and fingerprint per finding, confidence per check, "not assessed because X" reporting, maturity questionnaire (design v0.2).

## Honest summary
Of the Optimization items listed here, the orphan and idle group is largely implemented offline. The big-value groups are not: Hybrid Benefit, commitments, tagging and cost allocation, monitoring cost. None of the implemented checks has run on a real tenant, so "parity" is a claim about coverage of predicates, not about proven results.

## Items from the GitHub gap analysis (2026-10-21, KB 14, backlog 35)
These come from the public ACORT README (GPL-3.0, ideas only; its code was not read) and Learn pages cited in each check. Not workbook parity, so listed here to keep the registry and this file in step.
| Item | Status | Check IDs | Note |
|---|---|---|---|
| Non-production subscription not on a Dev/Test offer | DONE-OFFLINE | OPT-DEVOFF-01 | Name-word heuristic, info only; eligibility needs Visual Studio subscribers (Learn) |
| Running VMs in Dev/Test-looking subscriptions without auto-shutdown | DONE-OFFLINE | IDLE-VMSHUT-01 | Refuses to decide when no schedule resources are returned; ARG exposure UNVERIFIED |
| Premium disks and zone or geo redundant storage in Dev/Test-looking subscriptions | DONE-OFFLINE | OPT-DTSTOR-01 | Prompt, not a saving |
| Storage accounts without a lifecycle policy | DONE-OFFLINE | OPT-STORLC-01 | GPv2 and premium block blob only. Needs `[run] storage_apis = true` (one GET per account; Resource Graph does not list the type, KB 18). Refuses to decide unless every eligible account has a definite answer. The reply for an account with no policy (404 ManagementPolicyNotFound) is UNVERIFIED live |
| Empty availability sets | DONE-OFFLINE | ORPH-AVSET-01 | Hygiene, low |
| Deallocated VMs for more than 90 days | DONE-OFFLINE | IDLE-VMDEAL-01 | Only fires on a power-state timestamp; refuses to decide without one (ARG exposure UNVERIFIED). The Activity Log keeps 90 days, so a missing entry is never read as 'over 90 days' |
| Cost on resources missing from the inventory or without a resource id | DONE-OFFLINE | COST-UNMAP-01 | Needs `[run] cost_apis = true`. Reconciliation of the Cost Management Query (last full month, by ResourceId) with the Resource Graph id list. Cost column name, ResourceId case and nextLink paging are UNVERIFIED live |
