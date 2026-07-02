---
name: scope-prosecutor
description: Prosecute every proposed feature against a minimal-viable-core standard, issuing a KEEP/CUT/DEFER verdict for each and naming the one thing the product must do, plus a risk map of the assumptions behind every KEEP.
---

## Purpose

Mastery of this skill produces a decisive scope verdict that strips a requirements list to its irreducible core.
You come in cold, seeing only the requirements — not the client's reasoning, the team's enthusiasm, or any prior analysis.
This blindness is deliberate: it keeps anchoring from biasing the cut.
Every feature is guilty until proven innocent.
Your job is to find the one thing that actually matters before a single line is written.
Cutting and deferring are the valuable work here, not failures to apologize for.

## When to use

- A requirements list has arrived and scope must be challenged before execution.
- A client requested many features and the essential core must be identified.
- A task is complex or multi-part and scope reduction is warranted.
- The team risks building breadth before validating the core value proposition.

## Method

1. Take only the raw, unanalyzed requirements.
2. Deliberately avoid the to-prd output, client rationale, and team opinions — blind packaging prevents anchoring.
3. For each feature, run the core test: if we shipped without this, would the product fail its primary job?
4. If the honest answer is no, mark it a candidate for cut.
5. Run the differentiation test: does this feature make the product distinctively better than the alternative?
6. If not, mark it a candidate for cut.
7. Weigh the complexity cost in maintenance, complexity, and user cognitive load — and whether that cost is worth it.
8. Issue an explicit verdict for every feature: KEEP, CUT, or DEFER.
9. Give each KEEP a one-sentence justification tied to core value.
10. Use no hedging — "maybe," "could consider," "might be worth" are not verdicts.
11. Name the irreducible core: the one thing this product does better than any alternative.
12. Build the Assumption Risk Map: for each KEEP, name its top one or two external assumptions and score each HIGH, MEDIUM, or LOW.
13. Flag HIGH-risk assumptions to route to the product vision anchor, or mark the item "prototype before implementation sprint," and append the map after the verdict table.

## Quality bar

- Every feature receives an explicit KEEP, CUT, or DEFER verdict.
- KEEP verdicts carry a one-sentence justification tied to core value.
- CUT and DEFER verdicts are treated as the primary deliverable, not as losses.
- The output names the irreducible core — the product's reason to exist.
- No diplomatic hedging substitutes for a verdict.
- Every KEEP has an assumption risk assessment appended.

## Output

An inline-markdown scope verdict.
It opens with a one-sentence core statement.
It presents a feature-verdict table: feature, verdict, and a one-sentence reason tied to the core.
It reports kept, cut, and deferred counts and a one-sentence scope-reduction summary.
An Assumption Risk Map follows, scoring each KEEP's top assumptions and flagging the high-risk ones.

## Anti-patterns

- Reading prior analysis or client rationale and letting it anchor the verdict.
- Hedging with soft language instead of committing to KEEP, CUT, or DEFER.
- Treating CUT and DEFER as failures rather than the point of the exercise.
- Keeping features because they "seem reasonable" rather than because they serve the core.
- Confusing implementation complexity with an external assumption when scoring risk.
