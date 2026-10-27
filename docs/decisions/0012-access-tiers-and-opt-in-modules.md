# 0012 Access tiers: each extra permission is an opt-in module
Date 2026-10-27. Status: ACCEPTED (owner direction, 2026-10-27: "run what it can run based on Reader permissions; whatever needs explicit cost reader or billing reader, I trigger as a module").
Context: commitment discount utilisation, coverage and savings need cost data at a billing scope, possibly billing roles (Cost Management Reader, billing account or profile readers; which role is needed on which agreement type is UNVERIFIED until a live tenant exists). The default operator model is Reader only.
Decision:
1. Three tiers. Tier 0: Reader (default, always runs). Tier 1: Cost Management Reader at subscription or management group scope (existing `cost_apis`, `governance_apis`). Tier 2: billing roles at billing account or billing profile scope (future switch `billing_apis`, NOT built, default off).
2. A tier is entered only by an explicit switch in `[run]`. Without the switch the tool does not call the endpoints, and the checks that need them report "not assessed, because X, switch Y" (existing OPT_IN_SWITCH mechanism). A missing role with the switch on gives "not assessed, because HTTP 403", never an empty pass (hard rule 6).
3. Every check keeps its `permissions` metadata; `fcat doctor --needs` already groups checks by permission, so the access request for a customer can be written per tier. The doctor probe table will gain one row per tier when tier 2 exists.
4. Tier 2 checks are core features of the product when the customer grants the role, and invisible noise when not: they appear in the "not assessed" list with the one-line reason, not as errors.
5. The write-nothing rule (hard rule 1) is unchanged by any tier.
Consequences: commitment utilisation and coverage are built as a tier 2 module after the live-test decisions (LIVE-TESTING.md section 0). Advisor-based commitment recommendations need only Reader and are built now (RATE-ADVCOM-01).
UNVERIFIED: which billing role each agreement type (EA, MCA, CSP, pay-as-you-go) needs for reservation utilisation and cost data. First live-session item.
