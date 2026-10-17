# Development principles: continuity, audit, recovery
Status: PROPOSAL for the user's approval, 17 Oct 2026. Items marked UNVERIFIED rest on my general knowledge, not on a source I read this session.

## 1. The problem to solve
A chat can end without warning (token limit, lost GitHub connection, a fault that forces a new chat). The cloud container I work in is ephemeral and is reclaimed after inactivity (stated in my environment notes), so anything not pushed to GitHub can be lost. A new chat starts with no memory. It only has what is in the repo (and the attached claude.ai Project, currently empty).
Consequence: the repo is the single source of truth. Chat is disposable.

## 2. Rules
R1. Push after every work unit, not at the end of a session. A work unit is one coherent change that leaves the repo working.
R2. Update docs/HANDOVER.md before and after every work unit. A unit is not done until HANDOVER reflects it. Handover is overwritten (current state). The log is append-only (history).
R3. If a push fails: write a git bundle or patch to a known path, say so plainly to the user, and record it in HANDOVER. Never claim something is saved when it is not.
R4. Small commits on short-lived branches; main always works. No force pushes. Tag each milestone (v0.1.0 ...). Reverting = git revert of a commit or checkout of a tag; revert steps are written in docs/REVERT.md.
R5. Every non-obvious decision gets a short decision record (docs/decisions/NNNN-title.md): context, options, choice, consequences, date, sources.
R6. Every claim that came from a source is tagged VERIFIED / UNVERIFIED with the URL and the date read. Trust nothing, verify everything (your standing rule) is enforced by this register, not by memory.
R7. Mistakes are recorded in docs/MISTAKES.md (see 5). Any mistake that repeats becomes a rule in CLAUDE.md or an automated test.
R8. Customer data never enters git. Outputs, snapshots, tenant IDs, subscription IDs and names stay in an ignored folder. This matters most if the repo ever becomes public. Add a pre-commit secret/ID scan before the first collector exists (tool choice open; gitleaks is one option, UNVERIFIED for this use).
R9. The tool itself is read-only toward Azure. No write calls. A test asserts that no collector issues anything but GET/POST-for-query calls (POST is used by ARG and Cost Management queries, which do not change state; this needs a per-endpoint allowlist, not a blanket rule).

## 3. File layout for handover (copy from repo-skeleton/)
- CLAUDE.md : short entry point read first by a new session (the session tooling loads a repo's CLAUDE.md, per the add_repo/register_repo_root tool descriptions). Keeps rules, preferences, and pointers. Target well under about 150 lines (my guess, to stay readable).
- docs/HANDOVER.md : where we are, what is next, what is half-done, how to resume, open questions for the user, blockers.
- docs/RESUME_PROMPT.md : the prompt you paste into a new chat.
- docs/PLAN.md, docs/ROADMAP.md : scope and sequence.
- docs/decisions/ : decision records.
- docs/log/YYYY-MM-DD.md : terse append-only session logs.
- docs/MISTAKES.md : lessons learned.
- docs/REVERT.md : how to roll back, per kind of change.
- docs/KB/ : the knowledge base notes and sources/url-register.csv (already built).
- CHANGELOG.md : per release, human readable.

## 4. Audit and logging of the tool (runtime)
Each assessment run writes a run manifest into the output (JSON, also shown in HTML/Excel):
- tool version and git commit, config file used (profiles/toggles), start/end time;
- identity type and tenant/subscription scope assessed (stored only in the customer output, never in git);
- every module and check: ran / skipped / failed, with the reason (missing permission, billing type not applicable, API error, throttled);
- API calls: endpoint family, api-version, status, retry count, row counts (no tokens, no secrets);
- data freshness (the cost data's own latency is noted per source).
Structured JSON log lines with levels and a run id; redaction of tokens. Raw snapshots of collector output are saved so a report can be re-rendered or re-analysed offline.
Rule: a skipped or failed check must appear in the report as "not assessed, because X". Silence must never look like a pass.

## 5. Mistake tracking (docs/MISTAKES.md)
One entry per mistake: ID, date, what happened (symptom), root cause, how found, fix, prevention (rule/test), link to commit or decision, status. Examples already real from this project: miscounted hub queries (22 vs 23), wrong claim that hub recommendations are on by default, overstating that Log Analytics Reader was needed on top of Reader. Include a "claims to re-verify" list for facts that may go stale (versions, preview status, prices).
Troubleshooting aid: docs/TROUBLESHOOTING.md maps symptoms to causes using the run manifest and logs.

## 6. Sanity check: what is too much, what is too early
Do now (cheap, high value, pays back at the first chat loss): R1 to R7, the file layout, CLAUDE.md, HANDOVER, RESUME_PROMPT, decisions, MISTAKES, ignore rules for customer data.
Do when code exists: tests, CHANGELOG and semver tags, run manifest, structured logging, pre-commit scan.
Defer until there are collaborators or a public repo: CI pipelines, branch protection (UNVERIFIED whether available on a private repo on a free plan), PR templates, contributor agreement, signed releases, SBOM.
Real risks of over-doing it: documentation drift (two places saying different things), session logs that nobody reads, ceremony that slows small changes. Mitigations: one home per kind of information, short templates, handover overwritten not appended, and the rule that a stale doc is a bug.
Limit I cannot remove: if a chat ends abruptly mid-step, the last few minutes of work and reasoning can be lost. R1 and R2 shrink that window to one work unit; they do not eliminate it.

## R10 Right-sizing and idle checks use peaks, not averages (owner tip, 2026-10-18)
Before any check recommends a smaller size or shutdown, it must look at historical peaks (for example max and a high percentile over the window), not only the average. Findings state the metric window, the statistic used, and the data coverage (missing samples). A short or sparse window caps confidence at low. Guest-OS metrics only if the customer already collects them. UNVERIFIED: which window length is adequate; to be decided with Learn/Advisor documentation and tenant testing.
