# Eval A3 — Assumption Risk Map in `scope-prosecutor`

**Absorb action**: After KEEP/CUT/DEFER decisions, add an Assumption Risk Map
for each KEEP item. For each KEEP feature: name the top 1-2 assumptions the
team is betting on, score each HIGH/MEDIUM/LOW risk. HIGH-risk assumptions
must be flagged to product-vision-anchor or marked for prototyping before
full implementation.

**Hypothesis**: After absorb, scope-prosecutor outputs will surface hidden
bets embedded in KEEP decisions — making assumption risk visible before
architecture and implementation begin, not after.

---

## Pre-absorb baseline (current harness behavior)

`scope-prosecutor.md` as of 2026-06-23:
- Output is `core_statement` + `feature_verdicts` (KEEP/CUT/DEFER per feature
  with one-sentence reason tied to core).
- Quality criteria: every feature gets a verdict, KEEP requires justification,
  no diplomatic hedging.
- No concept of assumption mapping, risk scoring, or flagging hidden bets.
- Does not produce any output about what assumptions underlie KEEP decisions.

**Expected pre-absorb behavior**: scope-prosecutor produces clean verdicts.
KEEP items are justified by core-value alignment. No assumptions named. No
risk scores. No flags to product-vision-anchor. The output stops at the
verdict table.

---

## Rubric (apply to both pre and post outputs)

Score 1 point for each criterion met. Max score: 6.

| # | Criterion | Signal to look for |
|---|---|---|
| R1 | Assumption Risk Map section appears in output | Output has a distinct section after verdict table addressing assumptions |
| R2 | Each KEEP item has at least one named assumption | No KEEP item left without an associated assumption |
| R3 | Each assumption has a risk score (HIGH/MEDIUM/LOW) | Score present for every assumption named |
| R4 | At least one HIGH-risk assumption identified | Not all assumptions scored MEDIUM or LOW |
| R5 | HIGH-risk assumptions are explicitly flagged | Output names: "flag to product-vision-anchor" or "prototype before implementation" |
| R6 | Assumption risk is distinguished from implementation complexity | Assumptions (bets on external facts) separated from implementation difficulty |

**Expected pre-absorb scores**: R1: FAIL, R2: FAIL, R3: FAIL, R4: FAIL, R5: FAIL, R6: FAIL → 0/6  
**Expected post-absorb scores**: R1–R6 all PASS → 6/6

---

## Scenario S1 — Real-time collaborative document editor

**Task input to submit (requirements list):**
```
1. Real-time collaborative editing (multiple cursors)
2. Rich text formatting (bold, italic, headers, lists)
3. Document version history with restore
4. Comments and inline annotations
5. Offline mode with sync on reconnect
6. Export to PDF and DOCX
7. Mobile app (iOS and Android)
8. Access control (owner, editor, viewer roles)
```

**Why this probes the gate**: Real-time collaboration carries HIGH-risk
assumptions (WebSocket infrastructure, conflict resolution algorithm, server
capacity for live connections). Offline mode carries HIGH-risk assumptions
(CRDT or OT implementation, sync conflict strategy). These are often
discovered as blocked assumptions in sprint 3, not sprint 0.

**Pre-absorb expected output**: Verdicts table. KEEP: real-time editing (core),
access control (security baseline), version history (trust builder). CUT:
mobile (scope), rich formatting detail. DEFER: offline. No assumption map.

**Post-absorb expected output**: Verdicts table PLUS assumption map. Example:
- KEEP "real-time collaborative editing":
  - Assumption A: WebSocket infrastructure is available and scalable to N concurrent editors → HIGH risk (if not, falls back to polling = different UX)
  - Assumption B: a conflict resolution algorithm (OT or CRDT) is already chosen or can be adopted without redesign → HIGH risk → FLAG to product-vision-anchor
- KEEP "access control":
  - Assumption A: existing auth system provides user identity that can be used for RBAC → LOW risk

---

## Scenario S2 — AI-powered code review in PR workflow

**Task input to submit (requirements list):**
```
1. Automatic code review triggered on every PR
2. Language-specific analysis (Python, TypeScript, Go)
3. Security vulnerability detection
4. Style and convention enforcement
5. Natural language explanation of findings
6. One-click suggested fixes
7. Integration with GitHub, GitLab, and Bitbucket
8. Review latency < 30 seconds per PR
```

**Why this probes the gate**: LLM latency assumptions (< 30s for full PR
diff analysis) are HIGH risk. Multi-platform Git hosting integration is
HIGH risk if only one is validated. Style enforcement assumes a shared style
config exists per repo. These assumptions are invisible in KEEP justifications
tied to core-value alignment.

**Pre-absorb expected output**: KEEP: auto review on PR (core), language analysis
(differentiation), natural language explanation (differentiator). CUT: one-click
fixes (complex). DEFER: multi-platform (phase 2). No risk map.

**Post-absorb expected output**: Verdicts PLUS assumption map. Example:
- KEEP "review latency < 30 seconds":
  - Assumption A: LLM API can process average PR diff (~ 500 lines) in < 25s with network overhead → HIGH risk → prototype before implementation sprint
  - Assumption B: compute budget per PR is acceptable at scale → MEDIUM risk
- KEEP "language-specific analysis":
  - Assumption A: language detection from file extension is sufficient (no polyglot files) → LOW risk

---

## Scenario S3 — Multi-tenant SaaS conversion for existing product

**Task input to submit (requirements list):**
```
1. Tenant isolation (each customer sees only their data)
2. Custom subdomain per tenant (acme.ourapp.com)
3. Per-tenant billing integration (usage-based)
4. Tenant admin portal (user management, settings)
5. SSO support (SAML, OAuth2 per tenant)
6. Data export per tenant (GDPR right to portability)
7. White-labeling (custom logo, colors)
8. Migrate existing single-tenant customers to multi-tenant
```

**Why this probes the gate**: "Migrate existing customers" is a HIGH-risk KEEP
because it assumes existing data is migrateable without downtime and customer
consent. Tenant isolation at the database level assumes a schema strategy
(row-level security vs. separate schemas) that hasn't been chosen. These are
architectural bets, not implementation tasks.

**Pre-absorb expected output**: KEEP: tenant isolation (core), billing integration
(commercial viability), migration (can't ship without it). CUT or DEFER:
white-labeling (nice-to-have). No assumption map.

**Post-absorb expected output**: Verdicts PLUS assumption map. Example:
- KEEP "tenant isolation":
  - Assumption A: row-level security (or schema-per-tenant) can be applied to existing DB schema without a full rewrite → HIGH risk → flag to architect before sprint planning
- KEEP "migrate existing customers":
  - Assumption A: existing customer data can be migrated without breaking changes to their integrations → HIGH risk → requires customer communication plan before migration begins → FLAG to product-vision-anchor
  - Assumption B: migration can complete within a maintenance window (< 4h per customer) → MEDIUM risk
