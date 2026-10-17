# Language and licence: evidence and recommendation (17 Oct 2026)

## What was checked (OPENED unless stated)
| Fact | Source |
|---|---|
| azure-mgmt-resourcegraph (Python) 8.0.1, 24 Nov 2025, "Production/Stable", Python 3.9+; a 8.1.0b4 beta dated 2 Jun 2026 exists | https://pypi.org/project/azure-mgmt-resourcegraph/ |
| azure-mgmt-costmanagement (Python) 5.0.0, 8 Jul 2026, "Production/Stable", Python 3.10+ (lists 3.10 to 3.14); targeted REST api-version not stated on the page | https://pypi.org/project/azure-mgmt-costmanagement/ |
| Go armresourcegraph shown at v0.10.0 (26 May 2026), NOT stable (below v1) | https://pkg.go.dev/github.com/Azure/azure-sdk-for-go/sdk/resourcemanager/resourcegraph/armresourcegraph |
| Go armcostmanagement page showed v1.1.1 (14 Apr 2023) with a notice that it is not the module's latest version (a v3 exists); I did not open the v3 page, so its status is UNVERIFIED | https://pkg.go.dev/github.com/Azure/azure-sdk-for-go/sdk/resourcemanager/costmanagement/armcostmanagement |
| Shipping a Python CLI: for technical users, publish to PyPI and run with uvx / uv tool install / pipx; PyApp is a middle ground (needs network on first run); PyInstaller-style bundles are large, can trigger antivirus false positives and need code signing | https://pydevtools.com/handbook/explanation/how-do-i-ship-a-python-application-to-end-users/ |
| azqr is Go (single binary), MIT | note 01 |

## What could NOT be checked
- Reddit sentiment, which you asked for: the fetch tool blocks reddit.com (SITE_BLOCKED) and the web search returned only links without usable snippets. I did not substitute vendor blogs for it. So there is NO community-sentiment evidence in this recommendation.
- Package download counts, maintenance cadence beyond release dates, and whether the Python cost SDK covers the 2025-03-01 Cost Management api-version.

## Reasoning (my judgement, not sourced)
- The tool is mostly REST and ARG calls, JSON shaping, tabular aggregation, and rendering HTML and Excel. Python is strongest for the shaping and rendering parts; Go's advantage is a single static binary.
- Both Python Azure SDKs we need are marked stable, the Go resource graph SDK is not. Either way, calling REST directly (requests/httpx plus azure-identity tokens) removes SDK lag risk for new api-versions, which matters given the retired Consumption price sheet versions and the 2025-03-01 Cost Management api-version churn.
- Authentication: azure-identity AzureCliCredential reuses `az login`, matching the "run from my laptop via az CLI" intent.
- Distribution cost of Python is real: users need uv or pipx. For a consultant's own laptop and trusted customers' admin machines this is acceptable; for locked-down customer machines a PyApp or PyInstaller build would be needed, with antivirus and signing issues. A Go port stays an option later, which is easier if checks are data (YAML/JSON) and the report JSON schema is fixed.
- PowerShell: the toolkit's PowerShell module and Az.ResourceGraph exist, but HTML and Excel generation would depend on third-party modules (my assessment, not verified here), and the module requires PowerShell 7 and Az on the target machine.

## Recommendation (preliminary, pending your answer on licence intent)
1. Python 3.11+ CLI, REST-first with azure-identity, distributed through uv/pipx. Keep the checks and report schema language-neutral so a Go port is possible.
2. Licence: MIT, if the repo will be public or shared. Reason: the sources we reuse are MIT (azqr, finops-toolkit incl. query files, dolevshor orphan resources) or Apache-2.0 (Cloud Custodian, OptScale); both can be incorporated with notices kept. Keep a NOTICE / THIRD_PARTY file. FinOps Framework text is CC BY 4.0: attribution required if we reproduce capability names/text.
3. Do NOT copy code from: Komiser (Elastic License 2.0), Steampipe and Powerpipe (AGPL-3.0), or repos with no licence stated (several community repos in note 06). Ideas are fine; code is not.
4. If the tool will be a proprietary consulting asset, keep the repo private with no public licence and still keep NOTICE for the MIT/Apache parts. Apache-2.0 would add an explicit patent grant if it is later open-sourced (general licence knowledge, not checked against a source here).
