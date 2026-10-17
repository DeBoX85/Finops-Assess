# Checkpoint protocol (how work is saved, and what is NOT protected)
Goal: no more than one work unit of progress can be lost when a chat ends, GitHub drops, or the workspace is reclaimed.

## What a checkpoint is
`python scripts/checkpoint.py -m "<what changed>" --log "<one line>" [--session-url URL]`
It: runs the tests; rewrites the auto block in docs/HANDOVER.md (time, base commit, tests, files changed, stale counter); appends to today's docs/log; runs scripts/docs_check.py; scans staged changes for GUIDs and secrets (customer data guard, rule 2) and BLOCKS the commit if it finds any; commits; pushes. If the push fails it writes a git bundle next to the repo and exits 3: tell the user, never claim it is saved.

## Triggers (event-based, because timers cannot help when the chat itself ends)
1. After every work unit (a coherent change that leaves the repo working). Not "at the end".
2. BEFORE any long or risky step: a big fetch, multi-file generation, a refactor, a long research batch.
3. When a decision is made (also write the decision record) or a mistake is found (also write MISTAKES.md).
4. When the user says anything like wrap up, stop, or I will start a new chat.
5. Heartbeat (below).
Work-in-progress is allowed: commit and push half-done work, and say in HANDOVER "In progress" which files are half-done and how to finish or revert.

## What the script cannot do (honest limits)
- It cannot write the narrative parts of HANDOVER (State, Done, In progress, Next step, Open questions). Those need me to update them in the same unit. The script tracks `stale_count`: if code changed in 3 checkpoints without the narrative changing, HANDOVER shows a warning.
- It cannot save work that was never checkpointed. If a chat dies mid-unit, that unit is lost; the next session must start from HANDOVER and the git log and may need to redo it.
- The workspace is ephemeral; git hooks are not cloned. Run scripts/install_hooks.sh at the start of each session (pre-push docs check).

## Heartbeat
A scheduled message is delivered into the session about every 45 minutes (one-shot schedules, each heartbeat schedules the next). Procedure when it arrives:
1. Read docs/HANDOVER.md. 2. Run `git status`. 3. If anything is uncommitted or the narrative is out of date: update it, run the checkpoint. 4. If nothing changed: reply "no change" in one line. 5. Do NOT start new work from a heartbeat. 6. Schedule the next heartbeat unless the user has said to stop.
Limits: it only helps while the session can still take turns. It does not help if the context window is full or the chat is gone, which is why triggers 1 and 2 matter more. Stop it by telling me, or by deleting the scheduled task in your list.

## Starting a session (new chat)
Follow docs/RESUME_PROMPT.md. First actions: git pull; python scripts/install_hooks.sh; python scripts/docs_check.py; read HANDOVER; say what state was found.
