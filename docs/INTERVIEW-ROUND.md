# Interview round: questions for the owner (prepared 2026-10-27)

How to use: answer with a letter per question. Option X is always "write your own". "My lean" is my judgement, not a fact; the reason is given so you can overrule it. Sources for each item are in docs/DECISIONS-PENDING.md (DP #), docs/LIVE-TESTING.md section 0 (LT) and the backlog (BL). Suggested order: part A first, because it decides whether the tool ever meets a real tenant. Parts B to E are independent of each other.

## A. Live testing (blocks gate G2, so blocks every "verified" claim)

**A1. Which tenant for the first live pass? (LT 1, DP 4)**
- A. A tenant you fully control with nothing sensitive in it (a personal or lab tenant)
- B. The CSP tenant
- C. The Startups subscription tenant
- D. None yet, wait until a customer engagement exists
- X. Own answer
My lean: A or C. No customer data, no third party involved, and any Azure tenant is also an Entra tenant (KB 15). B adds partner-billing questions that would confuse the first pass.

**A2. Where does Claude work during a live session? (LT 2, DP 5)**
- A. Claude never touches the tenant. You run the tool on your laptop and paste `--redact` output
- B. Claude Code runs on your laptop with your read-only sign-in and sees live results
- C. A at first, B after the first clean pass
- X. Own answer
My lean: C. A is the safest start; B is faster once you trust the redaction.

**A3. What output may enter a Claude session? (LT 3)**
- A. Only `--redact` reports and manifests
- B. A plus raw snapshots, for tenants you own
- C. Anything, for tenants you own; only A for any customer tenant
- X. Own answer (including any NDA limit that applies to future customers)
My lean: A for now, C later. Snapshots hold all tag values (your decision of 2026-10-20), so they count as customer data.

**A4. Monthly cap for canary resources (a small unattached disk, a public IP, similar)? (LT 4, DP 8)**
- A. Up to 5 USD
- B. Up to 20 USD
- C. No canaries; test only on what already exists
- X. Own cap
My lean: A. Canaries are what let us measure precision and recall; without them G2 proves only that calls succeed.

**A5. Test tenant facts (DP 4). Please look up and tell me:**
- CSP tenant: classic CSP or Azure plan (MCA via partner), and is cost visibility enabled for the customer?
- Startups subscription: offer or quota ID shown in the portal.
- A. I will look these up before the session
- B. Skip; the tool classifies by quota ID and says "depends"
- X. Own answer

**A6. Rehearsal (docs/LIVE-REHEARSAL.md): do you want to run it yourself once, with me on call?**
- A. Yes, I run it, you read the result
- B. Yes, but later; I want a shorter version first
- C. I want the junior-friendly runbook first (see C3)
- X. Own answer

## B. Product scope (what the tool is allowed to read or promise)

**B1. Billing-role module: commitment utilisation and coverage (ADR 0012, DP 2026-10-27)**
- A. Build it as an opt-in `billing_apis` module after the first live pass shows what billing-scope access looks like
- B. Never; stay at Reader and Cost Management Reader
- C. Design only (an ADR and a mock-up), no code until a customer grants the role
- X. Own answer
My lean: A or C. It is the largest gap against the Power BI reports (KB 19), but it is guesswork until we see a real billing scope.

**B2. Cost Details report and blob download (ADR 0006 stage 2, DP 3b). Unlocks row-level cost, which would let me replace the per-resource cost lookup with real data.**
- A. Approve, after I check the REST reference for side effects and show you the result
- B. Not approved; keep stage 1 (Query and Forecast only)
- X. Own answer
My lean: A, with the side-effect check first.

**B3. Read-only Log Analytics queries (ADR 0007, DP 10). Unlocks usage-based monitoring and security cost checks.**
- A. Approve the single endpoint (POST to the workspace query path only)
- B. Approve for workspaces in tenants you own, not customers
- C. Not approved
- X. Own answer
My lean: B for the first pass. It is the only POST to a data plane, so I would prove it on your own workspace first.

**B4. Sentinel module (ADR 0010, DP 13 and 14)**
- A. Approve build order: tier A offline only; rule scan OFF
- B. A, and also approve the rule scan as opt-in (reads alert rule query text, stores a derived map only)
- C. Park the whole module until G2 passes
- X. Own answer
My lean: A. B adds redaction work and customer trust questions for a smaller gain.

**B5. Governance "pass records" (DP 12). Checks would also record what they saw working, so a posture view can say "Evidenced". This changes the check interface and touches every check.**
- A. Yes, add pass records now
- B. Yes, but only for governance and tagging checks
- C. No; keep posture as a mock-up
- X. Own answer
My lean: B. Same benefit where it matters, far less churn.

**B6. Export write mode (ADR 0005, DP 9). Currently design only.**
- A. Keep design only
- B. Drop it from the roadmap; the tool stays strictly read-only
- C. Build level 1 (write to a storage account you approve)
- X. Own answer
My lean: A. Hard rule 1 allows it, but nothing needs it yet.

**B7. M365 Copilot licensing module (BL 40, my proposal 2026-10-21)**
- A. Agree the proposal: park until core checks pass G2, then SKU inventory only, then opt-in per-user usage
- B. Build the SKU inventory now
- C. Drop it
- X. Own answer
My lean: A.

## C. Customer-facing output

**C1. Never-show list for the customer HTML (BL 39). Candidates to hide from the customer version: resource names, subscription names, tag values, cost figures, raw findings JSON, self-audit table, tool and commit version.**
- A. Show everything except config controls (today's default)
- B. Hide tag values and resource names; show counts and finding text
- C. You choose per item (I will send a tick list)
- X. Own answer
My lean: C. Only you know the customers.

**C2. How much of the self-audit the customer sees (my proposal)**
- A. Result, fingerprint and limits in plain words; full table operator only; a failure is always shown
- B. Everything
- C. Only pass/fail
- X. Own answer
My lean: A.

**C3. Interface (BL 43). `fcat guide` is a terminal wizard today. A local web UI would help juniors.**
- A. Terminal wizard is enough, write a runbook for juniors
- B. Build the local web UI before the first junior runs an assessment
- C. Decide after the first live pass
- X. Own answer
My lean: C. We do not yet know which steps are painful.

**C4. Roll-up across tenants (BL 41, 37). Built as `fcat rollup` over finished reports.**
- A. Good enough; leave it
- B. Add a dashboard view of the roll-up
- C. Add a batch run over a list of scopes
- X. Own answer
My lean: A until you have more than one real tenant.

**C5. Dashboard mock-up taste review (DP 6, BL 20).**
- A. I send 2 to 3 screenshots and you pick
- B. Defer until after the first live pass
- X. Own answer

## D. Method and quality

**D1. Confidence labels (DP 2). "High" needs 90 percent correct on at least 30 audited findings across at least 2 environments; otherwise capped at "medium".**
- A. Agree
- B. Looser (say 80 percent on 20 findings)
- C. Stricter
- X. Own answer
My lean: A. With a single test tenant, nothing can reach "high" for a long time; that is intended.

**D2. Maturity questionnaire v0.2 (DP 1, 7).**
- A. I review the 13 questions myself and send changes
- B. Accept as written for now
- C. Walk through them together in the interview
- X. Own answer
Also: reassessment interval of 6 months for small customers (my judgement): A. fine, B. 12 months, X. own.

**D3. "Why it matters" wording per check (marked REVISIT).**
- A. Keep per FinOps domain
- B. Write per check
- X. Own answer
My lean: A until real findings show where it reads wrong.

## E. Working agreement

**E1. What should I do between rounds?**
- A. Stand by; only answer questions
- B. Small safe items only (guide questions for the two new switches, SQL and NSG inventory counts, Learn re-checks)
- C. Prepare the offline groundwork for whatever you approve in part B
- X. Own answer

**E2. The 6-hourly heartbeat I answer with "no change" (scheduled task).**
- A. Keep
- B. Make it daily
- C. Remove it
- X. Own answer
My lean: B or C. It adds little while nothing is running.

**E3. Anything the tool does that surprised you, or any claim in the reports you do not trust?** Free text. I would rather hear this than assume the checks are right.
