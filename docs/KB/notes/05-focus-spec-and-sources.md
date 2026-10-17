# FOCUS: verified facts from file entries 23-40 (17 Oct 2026)

Fetch summaries come from a small model reading the page; re-open before quoting numbers in a deliverable.

## Version history (source: https://focus.finops.org/what-is-focus/, OPENED)
| Version | Ratified | Notes |
|---|---|---|
| 1.0 | GA announced 20 Jun 2024 (finops.org insight, OPENED) | 43 columns in the Cost and Usage dataset (spec v1-0 page TOC) |
| 1.1 | 7 Nov 2024 | 50 columns (spec v1-1 TOC) |
| 1.2 | 29 May 2025 | virtual currency (credits, tokens), multi-currency, unit-cost metrics; 57 columns (v1-2 TOC) |
| 1.3 | 5 Dec 2025 (finops.org insight published 11 Dec 2025) | Contract Commitment dataset, split cost allocation columns, Service/Host Provider, recency metadata; Provider and Publisher deprecated, removed from 1.4 |
| 1.4 | 4 Jun 2026 | latest; 4 datasets: Cost and Usage 65 cols, Billing Period 6, Contract Commitment 30, Invoice Detail 22. what-is-focus page says 1.4 adds 2 datasets (Invoice Detail, Billing Period), 47 columns, 6 attributes, 17 glossary entries, 2 features; focus on invoice reconciliation, commitment comparison, consistent cost recognition |
Consistency check: 65+6+30+22 = 123 matches the spec page. Earlier-session research (4 Jun 2026) is now CONFIRMED by a second source (what-is-focus page).
FOCUS Validator: supports 1.3 conformance testing; 1.4 support "expected later in Q3 2026" (as stated, status after that unknown).
Stale pages: finops.org/topic/focus says "now at version 1.3" (newest item there 13 Oct 2026), so that page lags the spec site.

## Claims in the user's file contradicted or unconfirmed
- "FOCUS 1.4 adds AI/ML cost columns": NOT supported. Sources describe invoice reconciliation, commitment comparison, Invoice Detail and Billing Period datasets. (Not seen in 1.4 column list either, but I did not read the 1.4 column list itself.) Mark UNCONFIRMED/likely wrong.
- Spec v1.2 TOC says 57 columns; Microsoft's 1.2-preview dataset has 105 columns because it carries x_ extension columns.

## Azure position
- Azure data-generator page and Microsoft schema page: 1.2 / 1.2-preview. Microsoft conformance: 94 percent against 1.2 (ms.date 04/01/2026).
- focus.finops.org home lists Microsoft (Azure) under v1.2 generators; v1.3 generators listed: MongoDB, Vercel, Snowflake, Databricks; AWS and Google also v1.2.
- So Azure is two spec versions behind 1.4. Implication: any FOCUS "conformance assessment" feature of our tool should target what Azure actually emits (1.2-preview, 105 cols, known gaps), and treat 1.3/1.4 as a forward mapping layer only.
- Linux Foundation release (11 Dec 2025, OPENED) lists Microsoft among providers supporting FOCUS but does not name its version. AWS GA 1.2 stated there.

## Entry-by-entry status (file numbering, HTML)
| # | URL | Status |
|---|---|---|
| 23 | learn .../focus/what-is-focus | OPENED. ms.date 2025-06-16; no spec version named; claims 49% fewer rows, 30% smaller (unverifiable); InvoiceId "not available for EA today" is time-bound. Known limits: ServiceName gaps, AKS resource group heuristic false positives |
| 24 | learn .../dataset-schema/cost-usage-details-focus | OPENED (see note 04) |
| 25 | azure.com blog FOCUS new spec | OPENED, STALE (Oct 2023) |
| 26 | azure.com blog democratizing FinOps | OPENED, STALE (Nov 2023) |
| 27 | focus.finops.org | OPENED. Promotes 1.4 |
| 28 | focus.finops.org/focus-specification/ | OPENED. v1.4 latest, no dates |
| 29 | .../v1-2/ | OPENED, loads |
| 30 | .../v1-1/ | OPENED, loads (truncated at 100k chars) |
| 31 | .../v1-0/ | OPENED, loads (truncated at 100k chars) |
| 32 | focus.finops.org/what-is-focus/ | OPENED, source of the ratification dates |
| 33 | github.com/FinOps-Open-Cost-and-Usage-Spec | OPENED. 10 repos: FOCUS_Spec, FOCUS-Sample-Data, focus_requirements_model_analyzer, etc. No validator or converter repo in this org |
| 34 | .../FOCUS_Spec | OPENED. 323 stars (the org page said 312, so numbers differ between fetches), 720 commits on working_draft, licence not named on page |
| 35 | finops.org/wg/adopting-focus... | OPENED. updated 10 Dec 2025; 5 stages Decide, Design, Build, Test, Launch; no version named; no Azure mention |
| 36 | finops.org/insights/focus-1-0-available | OPENED. 20 Jun 2024; 43 columns; 1.1 was then slated for Nov 2024 (it was ratified 7 Nov 2024); mentions converter and validator |
| 37 | finops.org/insights/introducing-focus-1-3 | OPENED. 11 Dec 2025 |
| 38 | linuxfoundation.org press release | OPENED. 11 Dec 2025 |
| 39 | finops.org/topic/focus/ | OPENED. lags (says 1.3) |
| 40 | focus.finops.org data generator Azure | OPENED (note 04) |
