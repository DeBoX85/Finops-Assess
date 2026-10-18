# Report tailoring (design and first build, 2026-10-18)
Backlog 16. Owner-set only (standing decision): tailoring is presentation. It never changes which checks run or what the JSON contains.

## Built now (presentation)
Config table `[report]` in the run config, or a per-run `--branding FILE` containing only a `[report]` table (for an external collaborator; replaces the main config's `[report]` for that run, anything else in the file is rejected).
| Key | Rule |
|---|---|
| title, subtitle, prepared_by, prepared_for, footer | text, length-limited (120/200/120/120/400), no control characters, always HTML-escaped |
| accent | exactly `#RRGGBB` (blocks CSS injection) |
| logo | path relative to the config file; PNG, JPEG or SVG by content check; at most 256 KiB; embedded as a data URI inside an `<img>`; its sha256 prefix, not the path, goes in the manifest |
| hide | any of `coverage`, `collector_errors`, `audit_detail` |

## Integrity rules (why some things cannot be hidden)
- Findings and the self-audit result line (PASS/FAIL) are always shown.
- Hiding `coverage` replaces the table with a one-line statement ("N checks: x ran, y not assessed ...") so a reader never mistakes a missing check for a pass (hard rule 6).
- `audit_detail` is hidden only while the audit passes; a failed audit always shows its detail.
- Every applied option is recorded in the manifest (`report_options`), so a PDF can be traced to how it was tailored. JSON and Excel keep all data; Excel gets title/prepared-by rows only.
- Tests: tests/test_tailoring.py (validation, escaping, hide rules, per-run override, findings unchanged).

## Already available through other settings
Which checks and domains run: `[domains]` and `[checks]` toggles (owner set). Scope: `subscriptions` and `management_groups` in `[run]`. Names hidden: `--redact`.

## Not built (waiting on you, parked as DECISIONS-PENDING #6 with the mock-ups)
- Module weight and ranking (order of sections and of findings by owner priority). Needs the dashboard layout first.
- Colour themes beyond one accent, fonts, cover page, PDF page furniture (print CSS exists; PDF look not reviewed).
- Language/wording variants for non-technical readers (the questionnaire work covers part of this).
- Multi-tenant dashboard (pinned).
