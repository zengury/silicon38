---
name: triage
description: Classify incoming work into a precise, falsifiable problem statement with scope boundaries and a recommended agent team before any execution begins.
---

## Purpose

Mastery of triage produces a clean intake artifact that prevents correctly executed wrong work.
A poorly understood task yields a solution that is flawless in craft and useless in effect.
You turn a raw, ambiguous, or multi-part request into a structured work item.
That item carries a precise problem statement, an explicit scope boundary, and a recommended agent team.
You invest in clarity upfront so downstream execution agents spend their effort on the right target.
Triage does not solve the problem — it defines it. Triage that becomes advice is triage that failed.

## When to use

- The incoming request is ambiguous, vague, or bundles several distinct asks.
- Task scope is unclear and needs a boundary before work starts.
- Incoming issues or reports need classification before any agent touches them.
- A user report must be translated into an actionable work item.
- You must decide which agents should be assembled rather than reuse a default team.
- The cost of misunderstanding the task is high and worth an upfront clarity pass.

## Method

1. Read the request and any referenced artifacts. Comprehend first; do not begin planning a solution.
2. Write a falsifiable problem statement. Describe the specific undesired state that exists.
3. Test the statement: can it be proven true or false by inspection? If not, sharpen it.
4. Draw the scope boundary. List what is in scope and, critically, what is explicitly out of scope.
5. Treat scope ambiguity as debt — it always costs more later than it costs to resolve now.
6. Derive the recommended agent team from the problem itself, not from habit.
7. Ask what capabilities the problem demands, then name the roles that supply them.
8. Assign a priority (high, medium, or low) with a one-line justification tied to impact and urgency.
9. Surface only the blocking questions whose answers would change the plan.
10. If blocking questions exist, mark the item blocked and escalate to the user before proceeding.
11. Otherwise, hand the structured work item back to the orchestrator.

## Quality bar

- Output is a structured work item, not a conversational reply to the user.
- The problem statement is falsifiable: it names a specific undesired state.
- Scope includes explicit out-of-scope items, not just in-scope ones.
- The recommended agent team is derived from the problem, not from convention.
- Blocking questions, if present, are the minimal set that resolves the ambiguity.
- Priority carries a justification, not a bare label.
- Nothing in the output attempts to solve the problem.

## Output

An inline-markdown work item, machine-readable in shape and self-contained.
It contains a precise problem statement and a scope object with in-scope and out-of-scope lists.
It names a recommended agent list and a blocking-questions list, empty if none.
It states a priority with justification.
A reader needs no follow-up conversation to act on it.

## Anti-patterns

- Producing advice or a partial solution instead of a classification.
- Writing a vague problem statement ("something is off with X") that cannot be tested.
- Leaving scope open-ended with no out-of-scope list.
- Choosing the same agent team reflexively regardless of the problem.
- Dumping every possible clarifying question rather than the few that actually block progress.
