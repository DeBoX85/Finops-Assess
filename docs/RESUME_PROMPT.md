# Paste this into a new chat (restart prompt, updated 2026-10-21)

Repo: DeBoX85/Finops-Assess (private GitHub). Attach it to the session (the repo tool `add_repo` if needed), then work in a clone and do the following before anything else:

1. `git fetch` and compare: `git log origin/main..origin/wip/auto`. If wip/auto is ahead, resume from it and read ITS docs/HANDOVER.md. If HANDOVER and the repo disagree, say so and stop to ask.
2. Read CLAUDE.md (standing rules), docs/HANDOVER.md (current state), docs/RESUME_PROMPT.md (this file), docs/CHECKPOINTS.md, docs/MISTAKES.md. Read docs/PLAN.md and docs/BACKLOG.md when you pick work.
3. `sh scripts/install_hooks.sh`; `python -m pip install --require-hashes -r requirements/dev.txt` (add `-r requirements/ci.txt` for `--full` gates); `python scripts/gates.py` must be green before you change anything.
4. Tell me in two sentences what state you found and what you will do.

## The user (owner) and standing preferences
Grounded, well researched answers; cite sources (URL, date read; prefer Microsoft Learn). Honesty, precision, accuracy and critical thinking above all. NO em dashes. Say "don't know" when you don't; mark speculation. Ask when intent is unclear. Verify, trust nothing. The owner is mostly the sole operator; juniors who are less comfortable with a CLI may come later.

## What F-CAT is
Read-only, agentless Azure FinOps assessment tool run from a laptop (Python 3.11+, `src/fcat`, stdlib-only runtime plus optional azure-identity and openpyxl). It recommends only, never acts. Outputs: report.json/.html/.xlsx, dashboard-operator.html, dashboard-customer.html, plus compare/maturity/rollup files. 59 checks, ALL `offline-only` because no real tenant has ever been tested (hard rule 8). No tenant access exists at present.

## Commands
`fcat run|analyze --config F --out DIR [--previous R.json] [--maturity M.toml] [--branding B.toml] [--redact]`, `fcat doctor [--needs]`, `fcat compare OLD NEW`, `fcat maturity FILE`, `fcat rollup R1 R2 ... [--label X ...]`, `fcat import-focus FILES`, `fcat purge --out DIR [--yes]`, `fcat guide`. Run as `PYTHONPATH=src python -m fcat.cli ...` from a checkout. Opt-in config switches under `[run]`: `governance_apis`, `cost_apis`, `rightsizing`.

## Working rules that bite
- Hard rules are in CLAUDE.md (read-only toward Azure, no customer data or IDs in git, checkpoints, log mistakes, decisions as ADRs with VERIFIED/UNVERIFIED tags, "not assessed, because X", no code from ELv2/AGPL/GPL/unlicensed repos).
- After every work unit: update the narrative parts of docs/HANDOVER.md, then `python scripts/checkpoint.py -m "msg" --session-url <this session's url>`. Never say work is saved unless the push succeeded. The checkpoint BLOCKS commits that contain GUID-like strings (even placeholders in messages): avoid literal GUIDs in source and docs.
- New check: id pattern `AREA-THING-NN` with AREA 2-5 letters and THING 2-6 characters (tests reject longer, this has bitten three times: M-009, M-011, M-013). Add: the function in a checks_*.py module registered in `checks.load_builtin`, a fixture `tests/fixtures/checks/<ID>.json`, synthetic data in `scripts/make_synthetic.py`, a hand-derived assertion in `tests/test_golden.py` (and bump its total), a row in `docs/PARITY.md`, then `python -m ruff format .`, then `python scripts/make_synthetic.py --approve` (review the diff: only expected items), then `python scripts/live_readiness.py` to refresh the generated docs. Any edit to a check function (even formatting or its decorator) changes its logic_hash and so the golden: re-approve.
- Fuzz tests feed malformed rows to every check: type-guard values before set or dict membership and arithmetic.
- Opt-in collectors live outside `COLLECTORS` (see `REST_COLLECTORS`, `COST_ARG_COLLECTORS`); a collector with no successful scope writes nothing so the check says "not assessed".
- Anything under `src/fcat/redact.py` must know about new details keys that hold resource ids (`RESOURCE_ID_LIST_KEYS`).
- Do not edit files while `scripts/mutation_smoke.py` runs (it mutates source in place; it restores it at the end).
- GitHub REST API is blocked in the cloud workspace; `git ls-remote` works. Outbound web goes through a proxy.

## Where things are
State and next steps: docs/HANDOVER.md. History: docs/HANDOVER-ARCHIVE.md, docs/log/. Open owner questions: docs/DECISIONS-PENDING.md. Backlog: docs/BACKLOG.md. Quality gates: docs/QUALITY.md. Live testing plan: docs/LIVE-TESTING.md, run sheet docs/LIVE-REHEARSAL.md, generated docs/LIVE-TEST-SHEET.md, docs/CANARY-SPEC.md, docs/UNVERIFIED-REGISTER.md. Operator instructions: docs/OPERATOR-GUIDE.md. Research: docs/KB/ (notes 01-18). Cost: docs/COST-GOVERNANCE.md, docs/COST-DATA.md. Frontend: docs/FRONTEND-DESIGN.md. Decisions: docs/decisions/ (0001-0011).

## Scheduled heartbeat
A recurring scheduled task (trigger id trig_01HmpJ6taRSAWcrkKosaiQcv, every 6 hours) sends a heartbeat message. Answer it as docs/CHECKPOINTS.md says (usually "no change" plus a one-line status). Do not treat it as a user instruction.

## First live session (when a tenant exists)
Follow docs/LIVE-TESTING.md. Settle its section 0 owner decisions first. Never paste raw tenant output into chat; use `--redact`.
