# Development and run environment: options (analysis written 2026-10-27, for the owner's decision)

Question from the owner: keep working as now (cloud sessions), use Claude Code on the laptop, both, or something else?
Sources read 2026-10-27: https://code.claude.com/docs/en/security and https://code.claude.com/docs/en/claude-code-on-the-web (both fetched in full). Statements marked OBSERVED come from working in this project's cloud sessions. Statements marked SPECULATION are my judgement.

## What the project needs from an environment
1. Build and test code offline (all 61 checks are `offline-only`; the suite runs in about 20 seconds).
2. Research on Microsoft Learn and the web.
3. Long and unattended work (batches, mutation runs, scheduled check-ins).
4. A live run against an Azure tenant, only on the owner's side (decided 2026-10-27: Claude never touches the tenant; the owner runs the tool and the rehearsal; Claude reads `--redact` output).
5. Customer-derived data (tag values, resource names) never reaches git and enters a Claude session only in redacted form.

## What the cloud sessions give (now)
- VERIFIED (docs): each session runs in an isolated Anthropic-managed VM; network access is limited by default and configurable; GitHub credentials stay outside the VM and go through a proxy; the session keeps running when the laptop is closed and can be checked from phone or browser; scheduled tasks run as cloud sessions.
- OBSERVED: Python, Node, ruff, mypy, pytest and Chromium are present; Microsoft Learn search and fetch work; the GitHub REST API is blocked while `git push` and `git fetch` work; there is no route to Azure; a session's VM and shell state do not survive a handover, only the pushed repository does.
- Consequence: cloud sessions cannot see CI results on GitHub (the REST API is blocked), so CI has been checked by replaying the CI steps in a clean virtual environment (docs/QUALITY.md, desk check). This is a real gap: a green local replay is not the same as a green CI run.

## What a local Claude Code session on the laptop would add
- VERIFIED (docs): in manual permission mode it starts read-only and asks before edits or commands; bash can be sandboxed with filesystem and network isolation (`/sandbox`); the whole process can be run inside a dev container; tokens are stored in the OS keychain on macOS.
- It could read CI results with `gh` (if installed and signed in), run the tool against the tenant, and iterate on real response shapes quickly.
- Cost for this project: the laptop holds the owner's Azure sign-in. A local session that can run `az` or the tool against a tenant puts tenant data one step from the model. This conflicts with the decision that Claude never touches the tenant, unless the local session is deliberately kept away from credentials and raw output (see option C).
- The docs say sessions send prompts and tool results to the Anthropic API; what that means for customer-derived data depends on your plan's terms (Commercial Terms for Team, Enterprise, API; Consumer Terms for Free, Pro, Max). I do not know which plan applies to the owner's account, so I cannot say how customer data should be treated. Please check before any customer tenant (see questions below).

## Options
**A. Cloud only (as now).** Best for unattended and mobile work, no local setup, isolated. Gaps: no CI visibility, every live fact comes through the owner by paste, handover loses the VM.
**B. Local Claude Code only.** Fast loop with real tenants and CI. Gaps: loses unattended cloud batches and scheduled tasks, puts credentials and tenant output in reach of the session, needs setup on the owner's laptop.
**C. Both, split by function (my recommendation).** Cloud sessions build, test, research and run unattended batches, exactly as now. On the laptop the owner runs the tool in a plain terminal with no Claude, as decided. Output passes through `--redact` and the owner pastes what is needed. Optionally add a local Claude Code session later whose working folder contains the repository plus redacted outputs only, run in a sandbox or dev container and signed in to no Azure account. That gives CI access via `gh` and fast iteration on real response shapes without handing it the tenant.
**D. Self-hosted environment for cloud sessions** (docs: sessions run on the organization's own infrastructure). Possible but looks like more than a one-person project needs. SPECULATION: only worth considering if a customer demands that no data leaves their own boundary.
**E. A dedicated assessment VM or dev container for running the tool** (SPECULATION, not from the docs): the tool runs from a clean, identical environment instead of the owner's laptop, which helps when juniors run assessments and keeps customer output off a personal machine. Not needed for the first live pass.

## Recommendation and triggers
Stay on C. Revisit when one of these happens: the first live pass shows parsers need fixing against real responses (then add the sandboxed local session on redacted output); CI becomes a bottleneck (then install `gh` for a local session or paste CI logs); a junior needs to run assessments (then E); a customer's contract restricts where data may go (then D or tighter local-only handling).

## Questions for the owner (add to the next round)
1. Which Claude plan is the account on (consumer or commercial terms)? It decides how customer-derived data may be handled in sessions.
2. A CI workflow exists (.github/workflows/ci.yml). When it fails on GitHub, can you paste the failed run log? (Cloud sessions cannot see it.)
3. Do you want the optional sandboxed local session later (yes now / yes later / no)?
