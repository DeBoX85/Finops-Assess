# F-CAT plan v0.1 (17 Oct 2026)
Status: DRAFT for approval. Facts come from the knowledge base (notes 01-09); each is VERIFIED or UNVERIFIED there. Items marked (decision) need the user.

## 1. Purpose and constraints
Read-only, agentless Azure FinOps and cost-optimisation assessment run from the user's laptop; answers "is environment X working at peak cost efficiency, and if not, where is the money going and why"; recommends, never acts. Reader-level access preferred; nothing deployed to the target. All billing types where possible (EA, MCA, CSP, PAYG; support level per type to be verified). Outputs: HTML dashboard (PDF export, per-customer tailoring), Excel, JSON, same data. Sovereign clouds: not this round. Multi-tenant dashboard: pinned.
Repo: private to start (decision 1 resolved), no licence file decision until collaborators or publication (see note 08 and DEV-PRINCIPLES). Toggles set by the owner only; customers see only the output.

## 2. Architecture (modular)
Collectors (data to JSON snapshots) -> Checks (findings) -> Renderers (HTML, Excel, JSON). Each check declares: id, domain, required permissions, data sources, billing applicability, run cost, confidence, savings basis (actual and list, clearly marked), FinOps Framework mapping (finops.org names primary, Learn names mapped). Config file with profiles and per-domain/per-check toggles; saved into the output. Permission probe at start; skipped modules reported as "not assessed, because X". Snapshots allow offline re-analysis and re-rendering. Dependencies between modules declared.
Language (preliminary, decision): Python CLI, REST-first with azure-identity (note 08). Reddit sentiment could not be checked.

## 3. Modules
M1 Inventory and scope: tenant, management groups, subscriptions, billing account type detection.
M2 Resource Graph checks: orphaned and idle resources, SKU/config waste (parity with azqr cost rules, AOE and toolkit workbook queries; matrix not yet built).
M3 Cost data: Cost Management Query/Exports, FOCUS handling (Azure emits 1.2-preview; do not assume 1.4 columns), actual vs list (list price via price sheet or Retail Prices API because ListCost is 0 for reservation usage and Marketplace).
M4 Commitments: reservations, savings plans, utilisation, coverage, exchange policy change on 1 Feb 2027.
M5 Advisor: pull and normalise recommendations.
M6 Log Analytics, M7 Application Insights, M8 Sentinel, M9 Defender for Cloud: catalogue in note 09 (24 draft checks). Live-tenant test of Reader-only workspace queries required.
M10 Governance and allocation: tags, budgets, policy, anomaly alerts.
M11 Maturity: see 4.
Roadmap (later): Foundry/AI observability cost, sovereign clouds, multi-tenant dashboard, Copilot status check.

## 4. Maturity assessment (decision needed)
Use the finops.org capabilities (4 domains, 22 capabilities counted from the page) with Crawl/Walk/Run. Critical limit: many capabilities (executive alignment, education, practice operations) are organisational and cannot be read from Azure data. Proposal: score technical evidence per capability, mark organisational capabilities "needs input" with an optional short questionnaire, show coverage next to each score, and never blend modules into one overall number. Scoring rubric not yet designed.

## 5. Phases
P0 Repo and continuity: create skeleton from repo-skeleton/, import the KB, first handover. Needs GitHub access.
P1 Skeleton CLI: auth, scope discovery, snapshot format, run manifest, JSON renderer, test harness with fixtures.
P2 Resource Graph checks and parity matrix.
P3 Cost data and FOCUS, actual vs list.
P4 Excel and HTML renderers, PDF export, customer tailoring.
P5 Monitoring/security modules, with live-tenant test.
P6 Maturity.
P7 Roadmap items.
Each phase ends with a tag, CHANGELOG entry and HANDOVER update.

## 6. Test environment (decision needed)
I cannot test against Azure from here (no verified live ARG/API run yet). Need: a test tenant or subscription with Reader that you control, ideally with some Log Analytics, App Insights and a Defender plan, plus a billing account. Until then, checks are written against documented schemas and fixtures and are marked untested.

## 7. Risks and open items
Azure FOCUS export behind spec; preview APIs may change; cost data latency; ARG limits (no lookup or semi/anti joins); Reader-only query access unconfirmed; reddit sentiment missing; FOCUS 1.4 changelog, conformance full report, azqr rule catalogue, Billing API 2019-10-01-preview and Cost Management api-version status all still open (notes README).
