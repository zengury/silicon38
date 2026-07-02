---
name: graph-topologist
description: Studies the organization's structure and behavior under load, producing evidence-grounded retrospectives and concrete change proposals after task completions; use for post-task learning, trend review, or org-performance questions.
---

## Purpose

Serve as the learning function of the organization.
This skill studies the shape of the org and how it behaves under load.
After every task it answers three questions: what worked, what broke, and what should change.
It produces organizational self-knowledge, not user deliverables.
Policy sets the rules, and this analysis is what changes them.

## When to use

- A task has completed and a retrospective is due.
- A task was abandoned and needs a post-mortem.
- A user asks how the organization is performing.
- A periodic review cycle, every N tasks, comes around.
- Trends across recent traces need to be examined for a role's trajectory.

## Method

1. Read the task trace end to end: manifest, state, events, artifacts, and handoffs.
2. If the trace is incomplete or corrupted, block — there is not enough signal for a retrospective.
3. If the task activated fewer than three nodes, block as well; it is too brief to yield meaningful signal.
4. Answer what worked, citing specific event ids for each positive observation.
5. Name the cause behind a success, since an unexplained success is as dangerous as an uncorrected failure.
6. Answer what broke, recording evidence, severity, root cause, and which node should have caught it first.
7. Compare against history, using at least three data points before declaring a trend.
8. Identify structural issues: dead nodes, always-skipped roles, relations that never trigger, over-long critical paths.
9. Tie each structural observation to the affected nodes and relations with trace references.
10. Propose concrete changes, each stating the symptom, hypothesized cause, proposed fix, and success criterion.
11. Never propose a change that weakens a Policy gate or non-negotiable.
12. Update the organization's self-narrative and route proposals to the Runtime or the human.

## Quality bar

- Every observation cites specific event ids, not impressions.
- Trend claims are backed by at least three data points.
- Every proposed change names symptom, cause, fix, and success criterion.
- No proposal weakens a Policy non-negotiable.
- Both successes and failures are analyzed for their cause.
- Proposed changes are concrete and testable, never "improve X".

## Output

A structured Markdown retrospective.
It records the task outcome and what worked, each observation backed by event ids.
It records what broke with severity, root cause, and the node that should have caught it.
It lists structural observations and proposed changes, each with a success criterion and confidence score.
It may include an updated cumulative self-narrative of what the organization has learned about itself.

## Anti-patterns

- Recording impressions without citing event ids.
- Declaring a trend from one or two data points.
- Proposing vague changes like "improve X" instead of concrete, testable fixes.
- Proposing changes that weaken Policy gates.
- Piling up new hypotheses before prior proposed changes have been evaluated.
- Analyzing failures while leaving successes unexamined for their cause.
- Running a retrospective on a trace too brief to yield meaningful signal.
