# Manual sampling plan (backlog 47, written 2026-10-27)

Why this exists. You decided (interview round, 2026-10-27) that there are no canary resources and that Claude never touches the tenant. So the only way to learn how often a check is right is for you to open flagged resources in the Azure portal and judge them. This is layer C of docs/AUDIT.md. Its numbers feed the confidence rule: a check may show "high" only after 85 percent correct on at least 20 audited findings across at least 2 environments (src/fcat/data/confidence_policy.toml; the threshold is not yet confirmed by you).

Honest limits. This measures precision (of what we flagged, how much was right). It cannot measure recall (what we missed) unless you also look for things the tool did not flag; section 5 shows a cheap way. Twenty findings is a small sample: 17 of 20 correct is compatible with a true rate of about 64 to 95 percent (my calculation, 95 percent Wilson interval). Treat "high" as "no problem seen so far".

## 1. When to audit
After every real run you want to rely on. Audit per check, not per report. Order by what you plan to show customers first.

## 2. How many findings per check
Audit every finding if a check has 10 or fewer. Otherwise a random sample of 10 or 10 percent, whichever is larger, capped at 30 (agreed 2026-10-18). To pick randomly without bias: sort the findings in the Excel file by resource id, then take every k-th row, where k is the number of findings divided by the sample size, rounded down; start at a row chosen by dice or the seconds on a clock, not by eye.
Note: the file gives resource ids. Do the lookup in the portal on your own screen. Do not paste ids into Claude.

## 3. How to judge one finding (the three verdicts)
Open the resource in the portal and answer the check's own question, using the "What to check first" text in the report.
- **Correct (true positive):** the condition the check names is really true, and a sensible owner would want to look at it. Example: an "unattached disk" really has no attached VM and no pending ownership reason.
- **Wrong (false positive):** the condition is not true, or there is an obvious reason the tool did not know (the disk is a deliberate restore point, the plan is kept for a reservation). Write the reason in a few words; it becomes a fixture or an exclusion.
- **Unclear:** you cannot tell without asking someone. Unclear findings are NOT counted in the audited number (they neither help nor hurt) but the share of unclear is itself information; if it is over a quarter, the check's wording is the problem.
Judge the finding as stated, not whether the saving is worth the effort.

## 4. Record it (aggregate only, no ids)
Keep the detailed notes OUTSIDE git (your own folder; docs/AUDIT.md section 10). Only totals go into src/fcat/data/precision_records.toml. Template for one audit session, per check:

```
Check id:            ____        Tool version/commit: ____   Report date: ____
Environment label:   ____ (your own code name, not the tenant id)
Findings total:      ____        Audited: ____ (sample rule used: all / random 10 or 10%)
Correct: ____   Wrong: ____   Unclear: ____
Wrong because (one line each, no resource names): ____
Auditor: ____   Date: ____
```
Then update the check's table in precision_records.toml by adding to earlier sessions, for example `audited = 25`, `correct = 22`, `environments = 2`, `last_audit = "2026-11-15"`. `audited` is correct plus wrong; `environments` is how many separate environments the totals came from. Ask Claude to do the arithmetic and the commit if you prefer; give it only the totals.

## 5. Cheap recall check (optional)
For each check you audit, spend five minutes looking for things the check should have flagged but did not: use the portal's own views (for example Advisor, or the resource list filtered by the condition). Write down the count of misses you found. Even one clear miss is worth a fixture. This is not a measured recall; it is a smell test.

## 6. What changes after an audit
- Precision at or above the threshold with enough samples and environments: the check may show "high" (only if its code declares high).
- Below: stays "medium"; each wrong finding's reason goes to the check's fixtures and exclusion logic (docs/MISTAKES.md if it was a real bug).
- Never raise a check's declared label in code to get a "high"; the rule only ever lowers it.

## 7. Effort estimate (my guess, UNVERIFIED)
About 2 minutes per finding in the portal, so 20 findings is under an hour per check. With 61 checks, auditing everything is not realistic. Start with the checks that produce the most findings or that you would show first: the 5 checks that declare "high" (ORPH-DISK-01, ORPH-ASP-01, MOD-LBBAS-01, MOD-PIPBAS-01, MOD-AGWV1-01) are the natural first batch.
