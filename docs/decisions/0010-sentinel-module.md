# 0010 Sentinel FinOps assessment as an opt-in module of F-CAT
Date 2026-10-21. Status: ACCEPTED 2026-10-27 by the owner (read-only module; tier A plus opt-in rule scan that reads analytic rule query text). Build waits for live testing; tier A may be built offline. No code yet.
Context: customers want to "cost proof" Sentinel environments; the work is manual today. Owner direction (2026-10-21): usable internally and customer facing; scoped multi-tenant/MSSP runs allowed; cost optimisation without losing monitoring coverage or quality is the focus; SOC effectiveness is nice to have; help customers who lost control see what is stored and watched. Research: KB 12, KB 13.
Options considered:
A. Separate tool or separate run. Rejected: duplicates collectors, checks, renderers, redaction and audit; splits the Log Analytics cost story.
B. Fold into the default run. Rejected: different access (tier B/C, possibly rule reading), applies only where Sentinel exists, different reader (SecOps/CISO), and ADR 0007 is undecided.
C. Opt-in module inside F-CAT (chosen): same collectors, check framework, snapshot, renderers, self-audit, gates; selected by `[sentinel] enabled = true` and per workspace opt-ins; its own report section and an Excel sheet set that can be handed over on its own.
Decision (proposed): build module C as specified in docs/MODULE-SENTINEL.md. Extends, not replaces, docs/MODULE-MONITORING-SECURITY.md (tiers A/B/C stay the access model).
Hard constraints carried over: read-only (no PATCH/PUT/POST on tables, rules, DCRs, recommendations), recommendations never say "remove" (they say "review" with the evidence and the unknowns), "no consumer found by text match" is never worded as "unused", all price maths shows actual and list separately, prices never hardcoded, one stated GB definition.
Consequences: ADR 0007 becomes the gate for the core tier B checks (raise priority); the rule-reading scan needs its own owner decision (#14); tier A checks can be built offline now.
Reuse: ideas from Microsoft's MIT workbooks (KB 13) with NOTICE entries if any query text is adapted; nothing from GPL/unlicensed projects (rule 7).
UNVERIFIED until gate G2: every API shape and ARG property named in the module doc.
