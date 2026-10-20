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
| T-01 | Customer data committed to git | output/, snapshots/, *.xlsx, *.pdf, .env ignored; secret/GUID scan script exists and runs in checkpoint (exemption: public tag policy id table only, ADR 0009). But `--out` can point anywhere, e.g. a folder inside the repo that is not ignored | MITIGATED 2026-10-18: `fcat` refuses an unignored output folder inside a git work tree unless `--allow-unignored-out` (manifest.out_dir_problem, tests/test_hardening.py). Limits: only git is considered; a synced cloud folder is not detected | Consider a warning for common sync folders (OneDrive, Dropbox), UNVERIFIED how to detect |
| T-02 | Token leakage | Token lives in memory only; not written to snapshot, manifest or logs (code read). Exception messages from azure-identity are reduced to the exception type name | MITIGATED: test runs the CLI with a stub token and scans every output file and stdout/stderr (tests/test_hardening.py) | None |
| T-03 | A bug or a dependency makes the tool write to Azure | Allowlist in http.py: GET to management.azure.com, POST only to the Resource Graph query path; tests for PUT, DELETE, action POST, foreign hosts, http. Architecture test confines network libraries to http.py. Azure CLI invoked only by azure-identity | MITIGATED for our own code. A dependency using its own HTTP is not covered by the allowlist | Pin dependencies; review azure-identity behaviour (it shells out to az) |
| T-04 | Spreadsheet formula injection: a resource name or tag like `=HYPERLINK(...)` becomes a formula when the customer opens the xlsx | Found 2026-10-18: not handled. Fixed the same day in render_xlsx (forced literal text) with a test | MITIGATED | Check CSV export if one is ever added |
| T-05 | HTML injection / XSS in the dashboard via resource names or tags | All values pass html.escape in render_html (code read). No test with hostile strings yet | MITIGATED: parametrized hostile-string test, mutation-checked (removing escape fails 4 cases) | Extend when new HTML sections are added |
| T-06 | Prompt injection: resource names, tags and descriptions are attacker-influenced text. If a report or snapshot is pasted into or read by an AI session, instructions hidden in a tag could steer that session | Not addressed. The cloud development session may read live-test output later (backlog 25) | OPEN | Rule: treat all snapshot and report content as untrusted data in any AI session; never auto-act on it; decide in backlog 25 what may enter a Claude session |
| T-07 | Report shared with the wrong people, or kept too long | Outputs contain tenant and subscription IDs and names | PARTIAL 2026-10-18: `--redact` pseudonymises tenant, subscription, resource group and resource names in report files (src/fcat/redact.py, salted, not reversible); `fcat purge` deletes our own output files (dry run by default). Gaps: snapshot is never redacted; free text copied from customer data is only scrubbed when it equals a name in the resource id; no retention timer | Decide retention default with the owner later (not urgent) |
| T-08 | Misleading report (wrong finding presented as fact) | Self-audit, confidence per check, offline-only labelling until G2, "not assessed because X" | PARTIAL: no check has run on a real tenant | G2 and the human audit sample (docs/AUDIT.md) |
| T-09 | Over-privileged identity used for the run | Tool asks for Reader. It cannot enforce what the identity has | OPEN | `fcat doctor` should warn if the identity has write roles at the scope (design in docs/DOCTOR.md) |
| T-10 | Supply chain: malicious or compromised Python package | Dependencies not pinned or hash-checked | PARTIAL: hash-pinned requirements/runtime.txt (pip-compile, 2026-10-18) with a test that it matches pyproject; manifest records Python and package versions. Dev tools not pinned | Install with `pip install --require-hashes -r requirements/runtime.txt` for customer runs; pin dev tools later |
| T-11 | The git repo or cloud session credentials leak | Private repo; push access granted per session | OUT OF SCOPE here | Owner's account hygiene |

## Added 2026-10-18: tailoring inputs
Branding text, accent and logo come from the owner's own config, not from the tenant, but are still validated: text is escaped, accent must be #RRGGBB, logo is content-checked, size-limited and shown only through `<img>` (tests/test_tailoring.py). A per-run branding file cannot change checks, scope or write anything.

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

## Added 2026-10-20: tag values are stored (cost governance phase 1)
- Owner decision: ALL tag values are stored in the snapshot (collector `tag_inventory`, `container_tags`). Tag values are plain text and can hold people's names or e-mail addresses (Learn tag-resources page, read 2026-10-20: do not put sensitive data in tags). The snapshot and any unredacted report are therefore customer data. They stay in the ignored output folder (hard rule 2).
- `--redact` replaces tag values in finding details (`variants`) with case-sensitive pseudonyms (`val-xxxxxxxx`, per-run salt). Case-sensitive on purpose: `Prod` and `prod` must stay distinguishable, because that difference is the finding. Counts and key names are not masked. Tag KEY names can still appear in messages (for example `Tag name 'env' is written 2 ways`); a key that itself contains customer data would not be masked. Not assessed as a risk beyond this note.
- Policy assignment parameters are stored (they hold tag names). Budget and alert e-mail addresses and storage account ids are NOT stored (phase 2 will project them away).

## Added 2026-10-20: governance REST collectors (phase 2)
- `[run] governance_apis` adds three GET calls per enabled subscription (budgets, scheduled actions, exports). Allowlist unchanged (GET on management.azure.com); a test proves PUT and DELETE to these endpoints are still blocked.
- Responses contain e-mail addresses (budgets, anomaly rules) and storage account ids, containers and folders (exports). `govcost.project_*` keeps only booleans, counts, names of the cost objects and run status. Export names, budget names and budget ids ARE stored (they identify customer objects), so the snapshot remains customer data and `--redact` pseudonymises the ids in findings.
- Residual: a budget or export NAME could itself contain a person's name; not assessed.
