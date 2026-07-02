---
name: hrbp
description: Scouts the ecosystem for the best new agent skills and tools, runs them through a Hire/Absorb/Reject/Watch funnel, and produces an actionable talent evaluation report; use for scheduled recruiting runs or when a candidate is proposed.
---

## Purpose

Grow the organization by hiring.
This skill sources the ecosystem's strongest new skills and tools and screens each through a structured funnel.
It produces a talent evaluation report the org can act on.
It scouts, screens, and recommends with enough specificity that a hire can be executed in one session.
It does not write harness files itself; it delivers the plan, not the implementation.

## When to use

- A scheduled daily or weekly recruiting run is due, where one run equals one batch.
- A candidate skill or tool has been proposed for hire.
- The org feels gaps in its role coverage that new talent might fill.
- A new agent collection, repository, or paper has surfaced worth screening.

## Method

1. Source candidates in order and stop at five to ten credible ones.
2. Open the watch list first, since those candidates have priority.
3. Scan community agent collections, GitHub trending for claude-code and ai-agent topics, the Anthropic changelog, and recent arXiv cs.AI or cs.SE papers.
4. Put any candidate named in the task at the top of the queue regardless of source.
5. Run each candidate down the six-question hire ladder in order, taking the first "No" as the verdict.
6. Apply the ladder: gap test, absorb test, evidence test, license test, integration-cost test, and layer fit.
7. Assign a verdict of HIRE, ABSORB, REJECT, or WATCH.
8. For each HIRE, produce a full hire spec: role id, title, layer, domain, source, license, and evidence.
9. Include the gap filled, trigger conditions, edges to add, files to create, and estimated effort.
10. For each ABSORB, name the target role and a ready-to-paste constraint block.
11. Rewrite the watch list with each candidate's missing evidence, added date, and recheck trigger.
12. Auto-downgrade watch entries older than 90 days without a triggered recheck to REJECT.
13. Assemble the talent evaluation report and hand off to the graph-topologist when HIRE verdicts exist.

## Quality bar

- Every sourced candidate ends with an explicit verdict.
- The hire ladder is run in order; the first "No" fixes the verdict.
- Every HIRE carries a hire spec executable in one session without more research.
- Every ABSORB names a target role and a ready-to-paste constraint block.
- The watch list is rewritten each run with recheck triggers and stale entries downgraded.
- Only permissive licenses (MIT, Apache-2.0, BSD, or equivalent) pass the license gate.

## Output

A Markdown talent evaluation report.
It opens with a batch summary and a candidate table of candidate, source, verdict, and rationale.
It includes one hire spec block per HIRE verdict.
It lists ABSORB actions with the target role and constraint block, plus the active watch list.
The watch-list file is rewritten as a companion artifact so a future run can resume without re-sourcing.

## Anti-patterns

- Writing harness files for a new hire instead of scouting and recommending.
- Continuing down the ladder after a "No" instead of taking that verdict.
- Recommending a HIRE without a spec detailed enough to execute in one session.
- Letting the watch list rot with no recheck triggers or stale-entry cleanup.
- Recommending a non-permissive license past the license gate.
- Sourcing dozens of candidates instead of stopping at five to ten credible ones.
- Leaving a sourced candidate without an explicit verdict at the end of the run.
