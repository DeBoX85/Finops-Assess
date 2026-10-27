# KB 19: FinOps toolkit Power BI reports compared with F-CAT (read 2026-10-27)

Sources (VERIFIED = stated on the page, read 2026-10-27, whole page fetched):
- https://learn.microsoft.com/en-us/cloud-computing/finops/toolkit/power-bi/reports (overview)
- https://learn.microsoft.com/en-us/cloud-computing/finops/toolkit/power-bi/workload-optimization
- Read in addition because the overview links to them: .../power-bi/governance and .../power-bi/rate-optimization. NOT read: cost-summary, invoicing, data-ingestion pages (so nothing is claimed about them).

Design difference (my assessment, not a Microsoft statement): the toolkit reports are spend reporting on exported cost data (FOCUS cost and usage, price sheet, reservation datasets) plus Resource Graph. F-CAT is an agentless assessment that reads configuration and produces findings; it has no cost-export pipeline. So "include everything" is neither possible nor wanted; the table shows what overlaps.

| Report page (Learn) | F-CAT | Status |
|---|---|---|
| Workload optimization: Recommendations (Advisor cost recommendations; page has no detail yet) | ADV-COST-01 (pass-through with Advisor's own savings figure) | Covered, with more detail than the report |
| Workload optimization: Unattached disks sorted by cost, cost over time, billed and effective cost, days available | ORPH-DISK-01 finds unattached disks. Cost per disk over time is NOT attached | Partly. Gap: cost on each finding. Possible via the `cost_apis` data (last month by ResourceId, backlog 33) |
| Governance: Summary (counts of subscriptions, resource types, resources, regions) | Subscription and resource counts exist in the manifest; type and region counts are not shown | Gap, small (PARITY: inventory counts planned) |
| Governance: Policy compliance | POL-TAG-01, POL-TAGMOD-01, POL-COMPL-01 (tag policy focus) | Partly: cost and tag related policy only, not a full compliance list |
| Governance: Virtual machines (with right-sizing recommendations), managed disks | RIGHT-VMCPU-01 (opt-in), ORPH-DISK-01, IDLE-VM* checks | Covered as findings, not as inventory lists |
| Governance: SQL databases | ORPH-EPOOL-01 only | Gap: no SQL database inventory or check |
| Governance: Network security groups and rules | ORPH-NSG-01 (empty NSGs) | Gap: rules are not read (security posture is outside the cost focus) |
| Rate optimization: Hybrid Benefit (VMs using AHB with fewer than 8 vCPUs, 8+ vCPU VMs without AHB, vCPU counts) | LIC-AHBWIN-01, LIC-AHBSQL-01 flag missing AHB. No vCPU count, so the under-8-vCPU case is not detected | Partly (needs a Compute SKU call, PARITY item) |
| Rate optimization: commitment utilisation, coverage, savings (list vs contracted vs effective), ESR | None | NOT built (PARITY: PLANNED, backlog 26). Needs cost data at billing scope or exports; ADR 0006 stage 2 pending |
| Rate optimization: reservation recommendations (VM), purchases, prices, chargeback by commitment | None (Advisor route planned, backlog 7) | NOT built |
| Rate optimization: data quality page (missing prices and costs) | None | NOT built |
| Overview: Cost summary, Invoicing and chargeback, Data ingestion reports | Not compared | Not read |

## Conclusion
The Workload optimization report is fully covered in substance (its two pages are Advisor recommendations and unattached disks). The wider toolkit set is not: the biggest missing area is commitment discounts (reservations and savings plans: utilisation, coverage, recommendations, effective savings rate). Smaller gaps: cost attached to orphan findings, inventory counts, vCPU-aware Hybrid Benefit, SQL and NSG inventories.
