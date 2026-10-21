# Finops-Assess (F-CAT)
Read-only Azure FinOps assessment toolkit. Work in progress; no code yet. Start with CLAUDE.md and docs/HANDOVER.md. Rights reserved; no licence granted (see docs/DEV-PRINCIPLES.md).

## Development
python -m pip install -e '.[dev]' ; pytest -q
Offline re-analysis of a snapshot: `fcat analyze --config config/example.toml --out output`
Live run (needs `az login`, `pip install -e '.[azure]'`): `fcat run --config config/example.toml --out output`  (UNTESTED against Azure)

Running an assessment: docs/OPERATOR-GUIDE.md. First live test: docs/LIVE-TESTING.md (generated worklists: docs/UNVERIFIED-REGISTER.md, docs/LIVE-TEST-SHEET.md via `python scripts/live_readiness.py`).
