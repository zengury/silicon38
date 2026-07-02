---
name: tdd
description: Write behavior-focused tests through public interfaces on a red-green-refactor cycle in vertical slices — use when new behavior is implemented, a bug fix must be locked in, or an interface contract needs coverage.
---

## Purpose

Mastery of this skill produces tests that verify behavior through public
interfaces, not implementation details. One test makes one behavioral claim,
stated in its name. Tests are built in vertical slices on a red-green-refactor
cycle: never all tests first, never all implementation first. The result is a
suite that survives a complete internal rewrite as long as behavior is
preserved, and that fails loudly the moment behavior actually breaks.

## When to use

- New behavior is being implemented and needs to be specified by tests.
- A bug fix needs to be locked in so it cannot silently regress.
- The task explicitly involves test coverage.
- A feature has a specified interface contract to verify against.

## Method

1. Take one behavior. Choose the smallest single behavior to specify next.
   Resist the urge to enumerate every test up front; work one vertical slice at
   a time.
2. Write the test first, through the public interface. Exercise the behavior the
   way a real caller would — no internal method access, no database inspection
   unless the database is the interface. Name the test as a specification: "user
   cannot checkout with empty cart," not "test_checkout_error."
3. Confirm RED. Run the test and watch it fail before any implementation exists.
   A test that has never failed has proven nothing.
4. Implement the minimum to reach GREEN. Write only enough production code to
   make this one test pass. Broader implementation belongs to later slices.
5. Refactor safely. With the test green, improve the code's structure. If a
   refactor that preserves behavior breaks the test, the test was coupled to
   implementation and must be rewritten to assert behavior instead.
6. Repeat the slice. Move to the next behavior and cycle again, keeping each
   test focused on exactly one behavioral claim.
7. Keep setup legible. If test setup grows so complex it obscures what is being
   tested, simplify it; opaque setup hides the specification.

## Quality bar

- Tests use public interfaces only — no internal access unless the interface is
  the boundary under test.
- Each test makes one clear behavioral claim, stated in its name.
- Tests would survive a complete internal rewrite that preserves behavior.
- Coverage targets critical paths and edge cases, not trivial assertions.
- Test names read as specifications, describing behavior not method names.
- No test setup so complex it obscures what is being tested.
- RED is confirmed before implementation; GREEN is confirmed after.

## Output

A test suite file covering the specified behaviors through the public interface,
with names that read as behavioral specifications. Evidence accompanies it: the
tests failed before implementation (RED confirmed) and pass after (GREEN
confirmed), and no test is coupled to implementation details.

## Anti-patterns

- Testing implementation details, so behavior-preserving refactors break tests.
- Writing all tests first or all implementation first instead of vertical
  slices.
- Skipping the RED step, so a test that never could fail proves nothing.
- Naming tests after methods ("test_checkout_error") rather than behavior.
- Inflating coverage with trivial assertions while critical paths go untested.
