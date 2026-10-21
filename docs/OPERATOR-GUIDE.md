# Operator guide (draft 2026-10-21, written offline)

For whoever runs an assessment, including a junior colleague later. Status: the offline path (`analyze`) is tested; the live path (`run`) has NOT been run against Azure yet (docs/LIVE-TESTING.md), so treat live runs as pilots and tell the owner what happens.

## What the tool does and does not do
- It only reads from Azure and recommends. It never changes, stops or deletes anything. Each item is a prompt to check with the customer, not an instruction.
- A check that could not run is listed as "not assessed, because X". That is not a pass. Say so to the customer.
- Check results are labelled `offline-only` until a real-tenant test has passed. Do not describe them as verified.

## Before the run
1. Agree scope with the customer in writing: which subscriptions or management groups, and the time window.
2. Send the customer the access list: `fcat doctor --needs` (no login, no network). It states which access each check needs and why. Reader on the scope is the baseline.
3. Copy `config/example.toml` to a new file outside the code folder, set `subscriptions` (or leave empty for everything the login can read), and fill in `[report]` (title, prepared for, prepared by, footer, optional logo and accent colour; see docs/TAILORING.md).
4. Sign in with `az login` using the identity the customer gave you.
5. Check access: `fcat doctor --config <your config>`. Read every failure. Do not continue past a failure you do not understand; ask the owner.

## The run
- Live: `fcat run --config <config> --out <output folder>`. Add `--previous <older report.json>` for a Changes section, and `--maturity <answers.toml>` for the maturity section (docs/maturity/README.md).
- Offline re-analysis of an existing snapshot: `fcat analyze --config <config> --out <output folder>`.
- The output folder must be inside no git repository, or in an ignored folder. The tool refuses otherwise. Do not override that with `--allow-unignored-out` unless the owner says so.

## What you get (output folder)
| File | Audience | Notes |
|---|---|---|
| dashboard-customer.html | Customer | Read-only, browsable, printable to PDF. Contains no operator notes, rule hashes, data digests, collector errors or API log. |
| dashboard-operator.html | You only | Adds evidence, reasons, collector errors and a notes box that is kept in your browser only. |
| report.html | Customer or you | Plain static page with the same findings, no script. The owner decided to keep it. |
| report.json, report.xlsx | You only until the owner decides | They hold everything. Whether the Excel goes to customers is NOT decided (DECISIONS-PENDING). |
| snapshot/ | You only | Raw collected data, including tag values. Customer data. Never share, never commit. |

## Handing over
1. Open dashboard-customer.html in a browser. Check the title, prepared for, footer and logo. Check that the Summary, Findings, Coverage and Self-audit pages open without errors (Progress appears only if you passed `--previous` or `--maturity`).
2. Print to PDF from the browser ("Print or save as PDF") if the customer wants a fixed copy. Keep the report fingerprint on the page; it shows if the file was altered.
3. If any file leaves your control or goes outside the customer, run again with `--redact` first. Redacted reports cannot be compared with each other (new salt each run).
4. Send only the customer file or its PDF. Never send the operator dashboard, the snapshot or the Excel without asking the owner.

## After the run
- Keep `report.json` from each run if the customer agrees; it is what `--previous` and `fcat compare OLDER NEWER` need next time.
- When finished: `fcat purge --out <folder>` shows what it would delete; add `--yes` to delete. Customer data should not sit on a laptop longer than agreed.

## Never do
- Paste tenant or subscription ids, tokens or tag values into chat tools, tickets or email.
- Edit the tool's code or checks. Report problems to the owner; log them in docs/MISTAKES.md if they are tool mistakes.
- Present "no longer reported" as "fixed". The resource may be gone or the rule may have changed.
- Explain a missing check as "all good". Say "not assessed, because ..." with the reason shown in the report.

## When something looks wrong
Stop, keep the output folder, note the command and the message, and tell the owner. Do not retry in a loop: the tool respects Azure throttling, but repeated runs still cost the customer's API quota.
