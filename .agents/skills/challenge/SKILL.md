---
name: challenge
description: Adversarially stress-test a design, plan, or output to surface hidden assumptions and failure modes before they ship, ranked by severity.
---

## Purpose

Make an idea stronger by attacking it honestly. This skill finds the assumption
the author did not know they were making, the failure mode the happy path hides,
and the use case that breaks the abstraction. It challenges in service of the
idea, not for the sake of challenge. The result is a set of specific, ranked
concerns — the idea either survives stronger, or a fatal flaw is caught early.

## When to use

- A design or plan has been proposed and needs stress-testing.
- A decision is significant enough that it should not go unchallenged.
- The orchestrator selects a complementary adversarial review.
- An agent's output needs an adversarial pass before integration.

## Method

1. Read the proposal until you can restate it faithfully. You cannot challenge
   what you do not understand, and strawman attacks waste everyone's time.
2. Surface the load-bearing assumptions — especially the implicit ones the
   author treats as settled. Name each one explicitly.
3. For each assumption, construct the concrete condition under which it fails.
   Trace the failure through to its consequence, not just its trigger.
4. Probe the boundaries: the happy path's blind spots, the inputs at the edge of
   the abstraction, the scaling and concurrency cases, the error paths.
5. Rank every challenge by severity — critical, major, or minor. Not all
   concerns are equal, and an unranked list hides the ones that matter.
6. Discard anything purely stylistic or preference-based. Only substantive risks
   survive.
7. Stay willing to be wrong. If the author's response resolves a challenge, mark
   it resolved. A clean grilling with no fatal flaws is as honest a result as one
   that finds them.
8. Render a verdict grounded strictly in the challenges raised.

## Quality bar

- Every challenge names the assumption, the failure condition, and why it matters.
- Challenges are ranked by severity, not presented as a flat list.
- No challenge is purely stylistic or preference-based.
- The challenger concedes when a challenge is genuinely resolved.
- A clean result is reported as clean, not padded with manufactured concerns.

## Output

An inline-markdown analysis listing challenges as {assumption, failure
condition, severity: critical | major | minor}, followed by a verdict of ROBUST,
ISSUES_TO_ADDRESS, or FATAL_FLAW_FOUND. Evidence requires each challenge to name
a specific assumption and the verdict to follow from the challenges.

## Anti-patterns

- Challenging a strawman instead of the actual proposal.
- Producing a flat list where critical and trivial concerns look equal.
- Manufacturing objections to appear rigorous when the idea is sound.
- Dressing up personal style preferences as substantive risks.
- Refusing to concede a point the author has clearly answered.
