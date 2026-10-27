# Customer view: what may the customer see? (tick list for the owner, backlog 48, prepared 2026-10-27; ANSWERED 2026-10-27, answers in docs/DECISIONS-PENDING.md, implementation is backlog 53)

How to use: for each row choose one of **Show / Hide / Ask me per customer**. Today's behaviour is in the middle column (from reading src/fcat/dash.py and tests/test_dash.py on 2026-10-27; "not checked" means I did not confirm it in code). Your answers become the default for `dashboard-customer.html`, and the per-customer override goes in the `[report]` config. Findings and the self-audit result can never be hidden (existing rule, docs/TAILORING.md).

| # | Item | Shown to the customer today | Why you might hide it | Your choice |
|---|---|---|---|---|
| 1 | Full resource ids (they contain subscription id, resource group, resource name) | Shown | Ids reveal naming and structure; some customers treat names as confidential | |
| 2 | Resource names only (last part of the id) | Shown | Names can reveal projects, people, product names | |
| 3 | Subscription ids and names in the map and filter | Shown | Names can reveal business units | |
| 4 | Resource group names | Shown (inside ids) | As above | |
| 5 | Tag values (Tags tab and finding details) | Shown; you chose to store ALL tag values (2026-10-20) | Values may hold names, cost centres, ticket numbers | |
| 6 | Cost figures on findings (last-month cost on disk findings, when `cost_apis` data exists) | Shown in details when present | Only meant for the customer's own finance? Rate and discount info is sensitive | |
| 7 | Advisor savings figures (pass-through) | Shown | They are Microsoft's estimates, not ours; may be mistaken for our claim | |
| 8 | Raw finding details ("What we saw": sizes, SKUs, dates, locations) | Shown | Technical detail the customer may not need | |
| 9 | Confidence label with its note ("medium: precision not yet measured") | Shown | Honest, but may undermine the report in a first meeting | |
| 10 | Validation state ("offline-only, not yet tested on a real tenant") | Shown in "How sure we are" | Required by hard rule 8; hiding it would break the rule. I recommend: always show | |
| 11 | Check coverage and "not assessed" list with plain reasons | Shown, with plain reasons (no collector names) | Customers may read gaps as failures | |
| 12 | Tool version and report fingerprint | Shown | Fingerprint helps reproducibility; version is harmless | |
| 13 | Run time and scope line (counts of subscriptions, resources, types, regions) | Shown | Counts reveal estate size | |
| 14 | Self-audit: result, fingerprint, limits in plain words | Shown (you chose this 2026-10-27) | n/a | Decided |
| 15 | Self-audit full table | Operator only unless left unhidden | Technical | |
| 16 | Maturity scores and "needs input" items | Shown if a maturity file was supplied (not checked in code) | Scores are my screening level, not an audit | |
| 17 | Governance posture and tag compliance numbers | Shown (not checked in code) | Could embarrass individual teams | |
| 18 | Collector errors | Operator only | Technical | Decided (never shown) |
| 19 | Evidence (logic hash, data digests) | Operator only | Technical | Decided (never shown) |
| 20 | Operator notes box | Operator only | Private | Decided (never shown) |
| 21 | Branding: your name, logo, "prepared by" line | Optional via branding file (not checked in code) | n/a | |

Notes for deciding
- Rows 1 to 6 interact with `--redact`: redaction masks ids and tag values in the JSON report, but the customer HTML is built from the full report. If you want a customer file with names masked, say so; I would build it as a render option, not a new data path.
- Rows 9 and 10: your own rules (hard rule 8, the confidence policy) say these must be shown honestly. I would not offer a way to hide row 10.
- A per-customer sheet is probably better than one global default: you could keep this table as a checklist in the engagement file.
