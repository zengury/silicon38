---
name: to-issues
description: Decompose a PRD or feature spec into the smallest independently deliverable, independently testable work items, with explicit blockers and an acyclic dependency graph.
---

## Purpose

Mastery of this skill produces a backlog of clean, independently completable work items.
An issue is done when one engineer can complete it without waiting on another issue to finish.
Dependency chains are acceptable; blocked issues that stall work are not.
Every issue is independently testable.
If you cannot describe what "done" looks like without referencing another issue, it is not yet decomposed enough.

## When to use

- A PRD or feature spec exists and must be broken into work items.
- A large task needs to be split into independently completable units.
- A backlog needs to be populated from a design document.
- Work must be parallelized across multiple engineers without collisions.

## Method

1. Read the input specification.
2. Confirm it has no unresolved open questions; if it does, the work is blocked until they are answered.
3. Identify the distinct deliverables the spec implies.
4. Make each deliverable a candidate issue owned by one person.
5. Slice until each issue is independently deliverable — one engineer can finish it without another completing first.
6. Split anything larger than a single independently deliverable unit.
7. Write a specific title for each issue — "Add user authentication middleware," not "Auth work."
8. Give each issue acceptance criteria that can be verified without running the full system.
9. Estimate size as S, M, or L.
10. If any issue would take more than a day, either split it or state an explicit justification for its size.
11. Map dependencies; where one issue must precede another, label the predecessor as a blocker.
12. Ensure the dependency graph is acyclic and that no issue is blocked by an unspecified dependency.
13. Confirm every feature from the input spec is represented before finishing.

## Quality bar

- Each issue describes one deliverable, completable by one person.
- Every issue has acceptance criteria verifiable without running the full system.
- Issues that must precede others are explicitly labeled as blockers.
- No issue exceeds a day of work without a stated justification.
- Titles are specific and action-oriented, not generic.
- The dependency graph is acyclic and fully specified.

## Output

An inline-markdown issue list.
Each entry has a title, a description, an acceptance-criteria list, an estimated size (S, M, or L), and a blocked-by field naming predecessor issues or none.
Collectively the issues cover the entire input spec.
Together they form a valid, acyclic dependency graph with no hidden blockers.

## Anti-patterns

- Producing issues so coupled that "done" cannot be defined without referencing another issue.
- Vague titles like "Auth work" that hide the actual deliverable.
- Acceptance criteria that require running the whole system to verify.
- Hidden or implicit dependencies that surface only mid-implementation.
- Oversized issues left unsplit and unjustified.
