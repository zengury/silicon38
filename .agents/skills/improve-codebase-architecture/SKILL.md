---
name: improve-codebase-architecture
description: Diagnose specific, addressable architectural problems and produce a prioritized, incremental improvement roadmap — use when coupling, cohesion, or module-boundary problems threaten long-term maintainability.
---

## Purpose

Mastery of this skill produces a precise diagnosis of architectural problems and
a prioritized roadmap to fix them incrementally. The value is specificity: not
"this code is messy" but "module A has twelve callers, four of which reach
directly into its database layer, creating hidden coupling that makes A
impossible to test in isolation." A problem named that precisely makes its fix
obvious. Architecture improves incrementally or not at all, so the output is a
sequence of independently deployable steps, never a rewrite proposal.

## When to use

- Codebase architecture is the explicit subject of the task.
- Coupling or cohesion problems have been identified or suspected.
- Module boundaries are unclear or are being violated.
- Long-term maintainability of the structure is in question.
- A diagnose or refactor step has flagged an architectural root cause.

## Method

1. Read the actual structure. Trace real dependencies, callers, and data access
   paths in the code. Ground every observation in specific files and modules.
2. Name each problem precisely. For each, state the named modules involved, the
   named coupling or boundary violation, and the concrete consequence it causes —
   what it makes impossible, slow, or unsafe today.
3. Distinguish symptom from root cause. Group related complaints under the
   structural cause that produces them so the roadmap fixes causes, not surface
   noise.
4. Propose incremental changes only. Each improvement must be independently
   deployable. Reject any step that requires a big-bang rewrite; decompose it
   into safe, shippable moves instead.
5. Order by impact-to-risk ratio. Sequence improvements by the value they
   unlock relative to the risk they carry, not by theoretical elegance. State
   the justification for the chosen order.
6. State "why now" for each step. Name what becomes possible or safer after the
   change lands — what future work it unblocks.
7. Preserve behavior. Each proposed change preserves existing behavior, or
   explicitly names what behavior changes and why that is acceptable.

## Quality bar

- Each identified problem is specific: named modules, named coupling, named
  consequence.
- Every problem references actual code locations, not general impressions.
- Improvements are ordered by impact-to-risk ratio, not theoretical elegance.
- Every proposed change is independently executable and deployable.
- No proposal requires a big-bang rewrite.
- Each change preserves behavior or explicitly names what changes and why.
- The "why now" — what becomes possible or safer — is stated for each step.

## Output

An inline document containing: current problems, each with the problem, its
affected modules, and its consequence; an improvement roadmap, each step with
its change, rationale, risk, and what it unlocks; and a justification for the
chosen priority order.

## Anti-patterns

- Vague complaints like "this is messy" that name no module or consequence.
- Proposing a full rewrite instead of a sequence of deployable steps.
- Ordering by elegance or preference rather than impact-to-risk.
- Silently changing behavior without naming the change and its justification.
- Listing problems with no roadmap, or a roadmap with no priority rationale.
