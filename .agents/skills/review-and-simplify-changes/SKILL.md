---
name: review-and-simplify-changes
description: Perform behavior-preserving refactors that solve a specific, named structural problem while keeping the test suite green and the code smaller.
---

## Purpose

Improve the structure of existing code without changing its behavior. A refactor
that alters behavior is not a refactor — it is a feature or a bug. This skill
starts from a green test suite, targets one precisely stated structural problem,
and ends with a green test suite and code that is measurably easier to change.
It favors deletion and the smallest viable move over new abstraction.

## When to use

- Technical debt is explicitly named and scoped.
- Code is described as hard to understand or change.
- Real, harmful duplication has been identified.
- Module boundaries are unclear and coupling is high.
- The task is a refactor, not the delivery of new functionality.

## Method

1. Establish a green baseline. Run the test suite and confirm it passes. If no
   suite covers the code, write characterization tests that pin current behavior
   before touching anything.
2. State the specific problem in concrete terms. "This code is messy" is not a
   problem; "six callers duplicate the same validation, so the seventh forgot
   it" is. Refactor toward that improvement and nothing else.
3. Run the minimalism gate before each move: Is the change necessary? Can the
   problem be solved by deleting code instead of reorganizing it? Is inlining
   clearer than extracting? Does an existing abstraction already fit? Is there a
   smaller step? If the new abstraction were deleted, would an engineer recreate
   it — or just use the concrete form?
4. If the honest answer is "they would delete it again," do not create the
   abstraction.
5. Make one logical change at a time. After each move, re-run the suite so every
   step is independently green.
6. Keep the commit history clean: one refactor move per commit, each passing on
   its own.
7. Confirm the stated problem is resolved and boundaries are cleaner by a
   measurable standard — fewer dependencies, clearer interfaces, less coupling.

## Quality bar

- Tests are green before and after; behavior is demonstrably preserved.
- The refactor solves the stated problem, not a more interesting nearby one.
- No new features are introduced during the refactor.
- No speculative abstractions — only existing duplication is removed.
- Module boundaries improve by a measurable metric.
- Each commit is one green, logical step.

## Output

Refactored implementation as file changes, plus an inline-markdown analysis
stating the problem solved, what changed and why, and what is now easier to
change. Evidence must show tests passing before and after, and the stated
problem demonstrably resolved.

## Anti-patterns

- Changing behavior while calling it a refactor.
- Refactoring without a stated, specific problem.
- Adding abstraction that a future engineer would just inline again.
- Bundling many unrelated moves into one large, unreviewable commit.
- Refactoring code with no tests and no characterization coverage.
