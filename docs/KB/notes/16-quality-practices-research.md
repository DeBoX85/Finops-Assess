# KB 16: Quality checks and gates, research plan and findings (started 2026-10-21)

Trigger: owner asked for more quality checks and gates, in the solution and in the development process; if I did not know which, to lay out a research plan and execute it.

## 1. What exists today (inventory 2026-10-21, from the repo)
Development process: G0 (ruff check with E,F,I,B,UP,S,BLE; ruff format; docs check) and G1 (offline tests, coverage floor 85%, now 96.95%) in scripts/gates.py; staged-change scan for tokens and customer data in scripts/checkpoint.py; main only gets pushes that pass G0 and G1; mutation smoke script (10 hand-picked bugs); dependency lock with hashes and a NOTICE test.
Solution: self-audit invariants INV-01 to INV-11, finding fingerprints, report hash, JSON Schema contract test, determinism test, read-only allowlist tests, hostile-string HTML tests, token-never-in-output test, fuzz and metamorphic tests per check, per-check fixtures.
Gaps (my judgement, to be tested by the research): no CI that runs independently of my own session; no static type checking; no dependency vulnerability audit; no browser-level accessibility or "no external request" check on the dashboards; property-based tests are PLANNED only; no test for test-order dependence; no size or time budget for large estates; docs links are not checked; mutation testing is self-chosen only.

## 2. Research plan
Questions: (Q1) What do recognised baselines require of a development process? (Q2) Which tools answer each gap, what do they cost to run, and how likely are false positives for this codebase (stdlib-only runtime, ~dozens of modules, one dev)? (Q3) What can be checked inside the product at run time and in its outputs?
Sources, in order of weight: standards and baselines (OpenSSF Best Practices criteria, NIST SSDF SP 800-218, GitHub Actions security hardening docs), then the tools' own documentation (pip-audit, mypy, Hypothesis, mutmut, axe-core), then WCAG 2.2 for contrast and name/role/value rules.
Method: read the page, record URL and date, extract the requirement or capability, then decide Adopt / Adopt later / Reject with the reason. Anything I cannot read stays UNVERIFIED. Then try the tool in this workspace before adopting it (a tool that cannot run here is not adopted).
Decision filter: adopt only if (a) it can run offline or on the standard package registries, (b) it catches a failure class that existing tests cannot, (c) false positives are manageable without blanket ignores, (d) runtime stays under about 2 minutes for the fast gate.

## 3. Findings and decisions (2026-10-21)
Each tool was run in this workspace before adoption. Sources: each tool's own documentation and repository, read 2026-10-21 (details in the git history of this note); OpenSSF, NIST SSDF and GitHub hardening pages were NOT re-read in this pass, so the baseline mapping (Q1) is UNVERIFIED.
| Tool | Decision | Result in this repo |
|---|---|---|
| mypy | Adopt (G0) | clean after typing fixes; no blanket ignores, the one `type: ignore` carries a reason |
| pip-audit | Adopt (`--full`, CI) | found a real advisory in certifi, fixed by bumping the lock to 2026.10.19; needs network, otherwise reported NOT RUN |
| Hypothesis | Adopt | found a real parser differential in the host allowlist (urlparse vs urllib), fixed in http.py with a regression test; profile is derandomized so CI is repeatable |
| pytest-randomly | Adopt | no order dependence found |
| axe-core 4.10.2 (dev only, MPL-2.0, via npm) | Adopt (`--full`, CI) | the script itself exposed a crash on a null `started` in the dashboard; fixed with a regression test |
| Headless browser tests | Adopt | no external requests, customer file carries no operator code, views render |
| mutmut 3.8.0 | Reject | conflicts with the src layout and with tests that read source text; recorded in M-012; the hand-picked mutation smoke stays (now about 30 mutants, 0 survive) |
| Docs link check | Adopt later | not built |
| Per-module coverage floors | Adopt later | not built |
| Hash-pinning playwright and pip-audit in CI | Adopt later | not built |
