# Threat model and privacy review (draft 1, 2026-10-18)
Scope: the F-CAT tool as it exists in the repo, run from a laptop with `az login`. Method: list assets, then threats, then what the code does today. Status words: MITIGATED (code and test), PARTIAL, OPEN. Nothing here has been reviewed by an independent person (see docs/AUDIT.md layer D). Statements about code were checked in the source on 2026-10-18; statements about Azure behaviour are UNVERIFIED unless a source is given.

## Assets
1. Azure credentials: the az CLI token cache (outside our control) and the access token held in memory.
2. Customer data we collect: subscription IDs, tenant ID, resource IDs and names, resource group names, tags, SKUs, regions, sizes, later also cost data, which can be commercially sensitive.
3. Reports and snapshots derived from 2: output/ folder, report.json, report.html, report.xlsx, snapshot/*.json.
4. The repo: must never contain 2 or 3 (hard rule 2).
5. Integrity of the findings: a wrong or tampered report misleads the customer.

## What is collected, stored, retained
- Collected only through read calls: Resource Graph queries today. Cost, Advisor and Log Analytics calls are not implemented; Cost endpoints need ADR 0006.
- Stored on disk in the output folder, unencrypted JSON/HTML/XLSX. Retention: none enforced; the tool never deletes. UNDECIDED whether to offer a purge command.
- The run manifest records endpoints with GUIDs redacted and the principal type. It does not record tokens.
- Sent anywhere else: nothing. No telemetry. All network access is confined to fcat/http.py (architecture test in tests/test_quality.py).

## Threats
| ID | Threat | Today | Status | Next action |
|---|---|---|---|---|
| T-01 | Customer data committed to git | output/, snapshots/, *.xlsx, *.pdf, .env ignored; secret/GUID scan script exists and runs in checkpoint. But `--out` can point anywhere, e.g. a folder inside the repo that is not ignored | MITIGATED 2026-10-18: `fcat` refuses an unignored output folder inside a git work tree unless `--allow-unignored-out` (manifest.out_dir_problem, tests/test_hardening.py). Limits: only git is considered; a synced cloud folder is not detected | Consider a warning for common sync folders (OneDrive, Dropbox), UNVERIFIED how to detect |
| T-02 | Token leakage | Token lives in memory only; not written to snapshot, manifest or logs (code read). Exception messages from azure-identity are reduced to the exception type name | MITIGATED: test runs the CLI with a stub token and scans every output file and stdout/stderr (tests/test_hardening.py) | None |
| T-03 | A bug or a dependency makes the tool write to Azure | Allowlist in http.py: GET to management.azure.com, POST only to the Resource Graph query path; tests for PUT, DELETE, action POST, foreign hosts, http. Architecture test confines network libraries to http.py. Azure CLI invoked only by azure-identity | MITIGATED for our own code. A dependency using its own HTTP is not covered by the allowlist | Pin dependencies; review azure-identity behaviour (it shells out to az) |
| T-04 | Spreadsheet formula injection: a resource name or tag like `=HYPERLINK(...)` becomes a formula when the customer opens the xlsx | Found 2026-10-18: not handled. Fixed the same day in render_xlsx (forced literal text) with a test | MITIGATED | Check CSV export if one is ever added |
| T-05 | HTML injection / XSS in the dashboard via resource names or tags | All values pass html.escape in render_html (code read). No test with hostile strings yet | MITIGATED: parametrized hostile-string test, mutation-checked (removing escape fails 4 cases) | Extend when new HTML sections are added |
| T-06 | Prompt injection: resource names, tags and descriptions are attacker-influenced text. If a report or snapshot is pasted into or read by an AI session, instructions hidden in a tag could steer that session | Not addressed. The cloud development session may read live-test output later (backlog 25) | OPEN | Rule: treat all snapshot and report content as untrusted data in any AI session; never auto-act on it; decide in backlog 25 what may enter a Claude session |
| T-07 | Report shared with the wrong people, or kept too long | Outputs contain tenant and subscription IDs and names | OPEN | Branding/scope config can hide names (backlog 16); add "redacted" export mode and a purge command |
| T-08 | Misleading report (wrong finding presented as fact) | Self-audit, confidence per check, offline-only labelling until G2, "not assessed because X" | PARTIAL: no check has run on a real tenant | G2 and the human audit sample (docs/AUDIT.md) |
| T-09 | Over-privileged identity used for the run | Tool asks for Reader. It cannot enforce what the identity has | OPEN | `fcat doctor` should warn if the identity has write roles at the scope (design in docs/DOCTOR.md) |
| T-10 | Supply chain: malicious or compromised Python package | Dependencies not pinned or hash-checked | PARTIAL: hash-pinned requirements/runtime.txt (pip-compile, 2026-10-18) with a test that it matches pyproject; manifest records Python and package versions. Dev tools not pinned | Install with `pip install --require-hashes -r requirements/runtime.txt` for customer runs; pin dev tools later |
| T-11 | The git repo or cloud session credentials leak | Private repo; push access granted per session | OUT OF SCOPE here | Owner's account hygiene |

## Privacy notes
- Resource names and tags may contain personal data (a person's name in a VM name, an email in a tag). The tool does not classify them. The customer should be told the report can contain such strings.
- Cost data (later) is commercially sensitive; treat the output folder as confidential and say so in the report footer (UNDECIDED wording).
- GDPR roles (who is controller or processor when a consultant runs this) are a legal question. DON'T KNOW; needs the owner or counsel, not assumed here.

## New backlog items from this review
27. Refuse or warn when --out is inside a git work tree and not ignored (T-01).
28. Test that no token string reaches any output (T-02).
29. Hostile-string test for HTML (T-05).
30. Redacted export mode and purge command (T-07).
31. Dependency pinning and SBOM in manifest (T-10).
