# ADR 0009: Narrow exemption in the customer data guard for public tag policy ids (2026-10-20)
Status: accepted by the owner (chose option 1 of 3 after an explicit question about whether quality is maintained).

## Context
`scripts/checkpoint.py` blocks a commit when an added line contains a GUID or secret (hard rule 2, customer data guard). `src/fcat/tags.py` holds a table of 17 Microsoft built-in tag policy definition ids. They are public values, identical for every tenant (Microsoft Learn, "Assign policy definitions for tag compliance", read 2026-10-20), but they look like tenant ids, so the guard blocked the Phase 1 commit. Phase 1 was committed by hand (8d001f0) after reviewing the staged diff.

## Options considered
1. Exempt only the table rows in `src/fcat/tags.py` (chosen).
2. Move the ids into a data file under an already excluded folder: no rule change, but the whole file would go unscanned.
3. Commit by hand each time: no change, but relies on memory and skips the automatic scan.

## Decision
`line_hit()` in `scripts/checkpoint.py` skips a line only when ALL hold: the file is exactly `src/fcat/tags.py`; the line matches `    "<guid>": "require|modify|inherit|append",` with nothing else on it; and it contains no secret pattern. Anything else in that file, and every other file, is scanned as before.

## Safeguards (tests in tests/test_render_scripts.py)
- The same line in another file, with extra text, in another shape, or with another value is still blocked.
- A test pins the exact set of 17 ids in `TAG_DEFINITIONS`. Adding, removing or swapping an id fails the test, so a tenant id cannot ride in unnoticed and a deliberate change is visible in review.

## Residual risk
- A real id that is added together with a matching change to the pinned set in the test passes both. Review of that diff is the control.
- The 17 ids are VERIFIED only as listed on the Learn page on 2026-10-20; the `tagName` parameter is verified for 871b6d14 alone (see tags.py).

## When to revisit
If the table grows past a handful of ids, if another public id table is added elsewhere, or if the guard is ever changed. Prefer option 2 at that point. To revert: delete `PUBLIC_GUID_FILE`, `PUBLIC_GUID_ROW` and the branch in `line_hit`, and the two tests.
