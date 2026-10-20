# Front-end design notes (owner feedback 2026-10-20)
Status: design only. Mock-ups in docs/mockups/frontend (round 1) and docs/mockups/frontend2 (round 2, scripts/make_frontend_v2.py). Nothing here is built into the real report yet.

## Owner requirements captured
1. Base: the "workbench" layout (filters, ranked queue, detail panel), plus an at-a-glance summary and some of the atlas map's visual interactivity.
2. Adjustable branding slot, upper left (company name, tagline, logo, accent colour).
3. Notes and small detail fields where relevant (per check and per resource).
4. Read Azure tags and show them.
5. Audience is a mix of CIO, CTO and engineers.
6. PDF export button for ad-hoc reports (owner open to postponing).

## What each needs in the real tool
| Need | Approach | Open question or risk |
|---|---|---|
| Branding | `[report]` config already has title, accent, logo, footer (docs/TAILORING.md). Add company name and tagline; logo is a file path embedded as a data URI. In-page editing is a convenience for demos only | None |
| Notes | A sidecar `notes.json` next to the report, keyed by finding fingerprint (stable across runs, see audit design) plus check id. Report loads it when present. The page cannot write files, so the browser version offers "download notes" and the CLI merges them | Notes may hold customer-sensitive text; sidecar stays in the ignored output folder |
| Tags | 31 of 36 collectors already project `tags` (not the subscription, management group, Defender pricing, Advisor and backup item collectors). Add `tags` to each finding's details from the row. Advisor and backup findings need a join to the target resource. Needs only Reader. UNVERIFIED live: ARG returns tags as a dynamic object, empty or null for untagged | Which tags matter (required tag names) is the owner's or customer's choice: `required_tags = [...]` in config |
| Tag hygiene checks | New checks: required tag missing, inconsistent spelling or case of tag names, tag values outside an allowed list. Need a whole-inventory collector, not only flagged resources | Maps to FinOps capability Allocation; scoring waits on the questionnaire decision |
| PDF | Mock-ups use the browser print dialog with a print stylesheet (works offline, no dependency, prints the current view, brand header included). A built-in PDF writer would add a dependency; headless Chromium is possible but heavy | Print output depends on the browser; acceptable for ad-hoc reports. Variant C adds a report basket that decides what prints |
| Summary at a glance | Computed from the report JSON only: headline sentence, counts, coverage ring, area bars, severity split, review progress. No cost numbers until cost data exists | Review progress depends on notes and status being saved (sidecar) |
| Map | Treemap of subscription by area, filter-on-click. Uses sqrt-damped areas so small tiles stay readable (the area is not strictly proportional, which the legend says) | None |

## Rules kept
Recommend only. No savings figures without cost data. "Not assessed" is always shown separately from "no findings". Synthetic data is labelled in every mock-up.
