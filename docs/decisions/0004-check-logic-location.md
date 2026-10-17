# 0004 Where check logic lives (ACCEPTED: option C, hybrid)
Date 2026-10-17. Status: accepted 2026-10-17 by owner ("C Hybrid approach"). Implemented for ORPH-DISK-01 (KQL narrows, Python applies exclusions; fixtures cover exclusions).
Problem: ORPH-DISK-01's real rule (exclusions, state filters) sits in KQL, which no offline test executes. Offline tests only cover thin Python that wraps rows. That undermines the quality case in docs/QUALITY.md section 6.
Options: (A) logic in KQL (compact, efficient, azqr/hubs style); (B) KQL selects broadly and projects raw properties, Python applies the rules (testable, auditable, can explain why a resource was or was not flagged); (C) hybrid: KQL narrows by resource type and obvious conditions, Python owns exclusions and thresholds.
Proposal: C. Consequences: more rows returned (paging cost, quota use per page), Python must be kept in step with the projected columns; every rule gets fixtures including exclusions; the KQL is validated live at G2 for syntax and canaries only.
Open: measure data volume impact on a real tenant (UNVERIFIED).
