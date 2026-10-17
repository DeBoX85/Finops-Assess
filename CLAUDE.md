# F-CAT (Finops Cloud Assessment Toolkit): instructions for any Claude session
READ FIRST: docs/HANDOVER.md, then docs/PLAN.md. Then continue from "Next step".

## Goal
Read-only, agentless Azure FinOps assessment tool run from a laptop. Outputs: HTML dashboard (PDF exportable), Excel, JSON, same data. Gives recommendations, never acts. Assesses FinOps maturity per tenant/MG/subscription. Includes monitoring/security cost (Log Analytics, App Insights, Sentinel, Defender).

## User preferences (standing)
- Grounded, well researched. Cite sources (URL, date read). Prefer Microsoft Learn.
- Honesty, precision, accuracy, critical thinking above all. Trust nothing; verify.
- No em dashes. Say "don't know" when you don't. Flag speculation explicitly.
- If intent or goals are unclear, ask before building.

## Hard rules
1. Tool is read-only toward Azure. No write calls to customer environments.
2. Never commit customer data, tenant/subscription IDs, tokens. Outputs go to the ignored output/ folder.
3. Follow docs/CHECKPOINTS.md: after every work unit and before any long/risky step, update the HANDOVER narrative and run scripts/checkpoint.py. Answer a heartbeat message per that file. Never claim work is saved unless the push succeeded.
4. Log mistakes in docs/MISTAKES.md; check it before starting similar work.
5. Record decisions in docs/decisions/. Tag claims VERIFIED/UNVERIFIED with source and date.
6. A skipped or failed check must be reported as "not assessed, because X".
8. Quality: follow docs/QUALITY.md. A check is `offline-only` until gate G2 passes on a real tenant; never describe it as verified before. Main must always pass G0 and G1.
7. Do not copy code from ELv2 or AGPL projects (Komiser, Steampipe, Powerpipe); MIT/Apache reuse needs notices in NOTICE.
