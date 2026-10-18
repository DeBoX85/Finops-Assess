# Third-party notices
docs/KB/sources/hub-recommendation-queries/ and workbook-queries-raw.json contain query text taken from microsoft/finops-toolkit (MIT). The upstream copyright and permission notice must be reproduced here verbatim before any redistribution of those files.
Reference material from Azure/azqr (MIT) is described in docs/KB notes; no azqr code is included.

## microsoft/finops-toolkit (MIT), copied from its LICENSE file on 2026-10-17
```
    MIT License

    Copyright (c) Microsoft Corporation.

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE

```

## Where F-CAT code is derived from microsoft/finops-toolkit (MIT) (audit 2026-10-18)
The check predicates below were written after reading the upstream hub recommendation queries and Optimization workbook queries (commit f12c29e, read 2026-10-18). The KQL is restructured (raw fields projected, rules applied in Python), but the logic is derived, so this notice applies:
- src/fcat/collectors.py: the KQL for unattached disks, public IPs, NICs, NSGs, App Service plans, VMs, load balancers, application gateways, elastic pools and databases, VNet gateways and connections, NAT gateways, DDoS plans, ExpressRoute circuits, snapshots, storage accounts, private DNS zones, private endpoints.
- src/fcat/checks_builtin.py: ORPH-DISK-01, ORPH-PIP-01, ORPH-NIC-01, ORPH-NSG-01, ORPH-ASP-01, IDLE-VMSTOP-01, ORPH-LB-01, ORPH-AGW-01, ORPH-EPOOL-01, ORPH-VGW-01 (with a deliberate deviation), ORPH-NAT-01, ORPH-DDOS-01, ORPH-ERC-01, ORPH-SNAP-01, ORPH-SNAP-02, MOD-STORV1-01, IDLE-VMDISK-01, ORPH-PDNS-01, ORPH-PE-01.
Not derived from it: BILL-OFFER-01, MON-*, SEC-* (Microsoft Learn documentation, cited in docs), the audit, redaction, import and rendering code.

## Python dependencies (runtime lock: requirements/runtime.txt; licences read from each package's own metadata on 2026-10-18)
Dependencies are installed by the user, not bundled in this repository. Licence per package as declared in its metadata (a declared licence is the package's own statement; it was not independently verified against its LICENSE file).
| Package | Version | Declared licence |
|---|---|---|
| azure-core | 1.41.0 | MIT |
| azure-identity | 1.26.0 | MIT |
| certifi | 2026.7.22 | MPL-2.0 (weak copyleft, file level; used unmodified, no obligation beyond keeping its notice if redistributed) |
| cffi | 2.1.1 | MIT-0 |
| charset-normalizer | 3.5.2 | MIT |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause |
| et_xmlfile | 2.0.0 | MIT |
| idna | 3.20 | BSD-3-Clause |
| msal | 1.39.0 | MIT |
| msal-extensions | 1.3.1 | MIT |
| openpyxl | 3.1.5 | MIT |
| pycparser | 3.11 | BSD-3-Clause |
| requests | 2.34.2 | Apache-2.0 |
| typing_extensions | 4.16.0 | PSF-2.0 |
| urllib3 | 2.8.0 | MIT |
Development tools (pytest, pytest-cov, jsonschema, ruff, pip-tools) are MIT or BSD-3-Clause per installed metadata and are not part of a customer run.

## Excluded sources (hard rule 7)
No code or query text from Komiser (ELv2) or Steampipe/Powerpipe (AGPL) is in the repository; a search of src, scripts and tests on 2026-10-18 found no mention of them. Their ideas may appear in research notes only. This is a search for names, not a code-similarity scan: DON'T KNOW whether independent code resembles theirs.

## Other content
- FinOps Framework capability names (finops.org, CC BY 4.0) are used in check metadata and the maturity design; attribution to FinOps Foundation applies if reproduced in a customer deliverable. Dashboard footer wording is not yet written (UNDECIDED).
- Licence of this repository: deferred by the owner; the repository is private.
