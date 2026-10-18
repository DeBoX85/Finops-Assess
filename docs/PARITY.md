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
| Idle backups (last backup > 90 days) | PLANNED | backlog 7 batch 4 | recoveryservicesresources |
| Recovery vault replication GRS vs LRS | PLANNED | backlog 9 | Judgement call; needs customer context, report as info |
| Disk last modified date (ARM createdTime/changedTime) | PLANNED | backlog 7 | Needs ARM call beyond ARG |
| Empty App Service plans | DONE-OFFLINE | ORPH-ASP-01 | |
| Empty SQL elastic pools | DONE-OFFLINE | ORPH-EPOOL-01 | |
| Unassociated DDoS plans | DONE-OFFLINE | ORPH-DDOS-01 | |
| Databases "idle over 30 days" | DIFFERENT | none yet | The workbook query matches names containing old/Dev/test and measures no activity. Not copied. Replacement needs Azure Monitor metrics and peak-aware rules (DEV-PRINCIPLES R10) |
| Idle SQL pool / unused Synapse workspaces | PLANNED | backlog 7 batch 4 | |
| Cosmos DB RU reduction, throughput mode, continuous backup | PLANNED | backlog 7 | Via Advisor in ARG; value is Advisor's own figure |
| Azure Hybrid Benefit (Windows, Linux, SQL, VMSS, Coverage summary) | PLANNED | backlog 7 / hub AHB queries | Needs Microsoft.Compute/skus call for vCPU; savings need list price |
| Azure Firewall Premium unused features | PLANNED | backlog 9 | |
| Reservation and savings plan recommendations (Advisor route) | PLANNED | backlog 7 | Reader is enough via advisorresources |
| Commitment discount utilisation, billing-scope recommendations | PLANNED | backlog 26 | Needs billing permissions and Cost endpoints (ADR 0006 pending) |
| Advisor cost recommendations (compute, monitoring) | PLANNED | backlog 7 | Passed through with Advisor's own savings, labelled as such |
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

## Beyond the workbooks (F-CAT only, today)
Monitoring and security tier A (docs/MODULE-MONITORING-SECURITY.md): MON-LAWCAP-01, MON-AICLS-01, SEC-DEFDEV-01 (all informational, confidence low). Billing-offer awareness (BILL-OFFER-01), self-audit of every report, evidence and fingerprint per finding, confidence per check, "not assessed because X" reporting, maturity questionnaire (design v0.2).

## Honest summary
Of the Optimization items listed here, the orphan and idle group is largely implemented offline. The big-value groups are not: Hybrid Benefit, commitments, tagging and cost allocation, monitoring cost. None of the implemented checks has run on a real tenant, so "parity" is a claim about coverage of predicates, not about proven results.
