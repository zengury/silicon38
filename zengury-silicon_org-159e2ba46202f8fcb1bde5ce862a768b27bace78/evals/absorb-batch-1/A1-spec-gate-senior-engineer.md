# Eval A1 — Specification Gate in `senior-engineer`

**Absorb action**: Add a Specification Gate before the Minimalism Gate.
A specification is: expected inputs, expected outputs, edge cases handled,
edge cases out of scope, and the acceptance criterion that proves it works.

**Hypothesis**: After absorb, senior-engineer will refuse to write code for
underspecified tasks and will instead produce a formal spec first — reducing
"confident drift" (plausible but incorrectly specified output).

---

## Pre-absorb baseline (current harness behavior)

`senior-engineer.md` as of 2026-06-23 has:
- **Minimalism Gate** (6 questions): checks necessity, std-lib coverage, etc.
- No requirement to write a spec before coding.
- Quality criterion "Code does exactly what the specification says" — but no
  gate that *enforces* a spec exists before coding begins.

**Expected pre-absorb behavior**: role proceeds to the Minimalism Gate then
writes code, inferring or assuming missing spec details. Ambiguous requirements
are resolved by the implementer's judgment, silently.

---

## Rubric (apply to both pre and post outputs)

Score 1 point for each criterion met. Max score: 6.

| # | Criterion | Signal to look for |
|---|---|---|
| R1 | Detects that no formal specification exists | Output acknowledges the spec is missing before proceeding |
| R2 | Writes a specification before writing any code | A spec artifact appears in the output before code |
| R3 | Spec names expected inputs and outputs | Both input shape and output shape are described |
| R4 | Spec names edge cases in scope | At least 2 handled edge cases listed |
| R5 | Spec names edge cases explicitly out of scope | At least 1 explicit out-of-scope boundary stated |
| R6 | Spec contains a falsifiable acceptance criterion | "Done when X" stated in terms testable by a third party |

**Expected pre-absorb scores**: R1: FAIL, R2: FAIL, R3: partial, R4: FAIL, R5: FAIL, R6: FAIL → ~1/6  
**Expected post-absorb scores**: R1–R6 all PASS → 6/6

---

## Scenario S1 — Rate limiter (common feature, deliberately vague)

**Task input to submit:**
```
Implement rate limiting for the API. We're getting too many requests and
need to protect the service.
```

**Why this probes the gate**: No rate specified. No window (per-second? per-minute?
per-hour?). No scoping (per IP? per user token? per endpoint?). No response code
specified. No header format. A model following confident drift will pick reasonable
defaults and implement; a model with the Specification Gate will stop and write a spec.

**Pre-absorb expected output**: Code implementing rate limiting with assumed defaults
(e.g. 100 req/min per IP, 429 response, X-RateLimit headers). Minimalism Gate
questions answered silently. No spec written.

**Post-absorb expected output**: Execution blocked at Specification Gate. Spec
written covering: input (request with IP/token), output (allowed/blocked decision
+ response code), edge cases in scope (burst allowance, auth vs unauth users),
edge cases out of scope (rate limit storage across multiple nodes), acceptance
criterion (e.g. "load test at 150% rated limit shows < 1% requests above limit
receive 200").

---

## Scenario S2 — Security fix (action-oriented, underspecified scope)

**Task input to submit:**
```
Fix the bug where users can see each other's data. This is a security
issue and needs to be resolved before the next release.
```

**Why this probes the gate**: Completely underspecified. Which users? Which data?
Under what access path (direct URL, API call, shared link, export)? What is the
correct behavior (redirect, 403, filtered response)? Implementing without a spec
risks fixing one path while leaving others open.

**Pre-absorb expected output**: Code adding authorization checks around data
access, probably in a route handler or service layer. Implementer infers scope.

**Post-absorb expected output**: Spec written before code. Edge cases in scope
(direct DB query path, API response serialization, exported file content). Out
of scope boundary stated (admin views, audit logs). Acceptance criterion: "User A
authenticated session cannot receive any resource owned by User B via any listed
path."

---

## Scenario S3 — Dashboard search (product feature, very broad)

**Task input to submit:**
```
Add search functionality to the dashboard so users can find things faster.
```

**Why this probes the gate**: "Search" is a whole product domain. Full-text vs.
filtered? Which entities are searchable? Which fields? What is the performance
expectation? Is real-time search or submit-on-enter required? Does it search
across all users' data or just the current user's?

**Pre-absorb expected output**: A search input component wired to a backend
query. Implementer picks an approach (probably full-text LIKE query or simple
filter). Missing constraints not surfaced.

**Post-absorb expected output**: Spec gate fires. Spec covers: input (search
query string, optional filter params), output (list of matching items with
highlighted match context), edge cases in scope (empty query, special
characters, multi-word phrases), out of scope (cross-user search, saved searches,
search analytics), acceptance criterion (search results for "invoice" return all
items whose name or description contains "invoice" within 200ms for datasets < 10k
items).
