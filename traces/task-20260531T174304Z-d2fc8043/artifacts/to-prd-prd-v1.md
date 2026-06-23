## Problem Statement

The /Users/ZQ/roboease codebase suffers from duplicated code, poorly structured modules, and low maintainability/testability. This increases technical debt, slows development, and raises the risk of bugs. The team needs a clear plan to refactor the codebase to improve structure, eliminate duplication, and enhance testability.

## Solution

Conduct a systematic refactoring of the roboease codebase: identify and eliminate duplicate code, reorganize modules into cohesive units with clear responsibilities, and improve test coverage and testability. The refactoring will be guided by architectural principles and will not introduce new features.

## User Stories

1. As a developer, I want duplicate code identified and consolidated, so that maintenance effort is reduced and bugs are less likely to propagate.
2. As a developer, I want modules to have clear, single responsibilities, so that the codebase is easier to navigate and understand.
3. As a developer, I want module interfaces to be simple and well-documented, so that I can use them without reading internal implementation.
4. As a developer, I want the codebase to have consistent coding patterns, so that I can predict how code behaves.
5. As a developer, I want to be able to write unit tests for isolated modules, so that I can verify correctness quickly.
6. As a developer, I want existing tests to be reliable and not brittle, so that I trust the test suite.
7. As a developer, I want a clear dependency graph between modules, so that I understand the impact of changes.
8. As a developer, I want to be able to run a linter or static analysis to catch structural issues, so that regressions are prevented.
9. As a developer, I want the refactoring to be done incrementally, so that I can merge changes without long-lived branches.
10. As a developer, I want a report of code duplication metrics before and after, so that I can measure improvement.

## Implementation Decisions

- **Module Extraction**: Identify deep modules that encapsulate common functionality (e.g., file I/O, data transformation, logging) and extract them into separate modules with stable interfaces.
- **Duplication Detection**: Use a static analysis tool (e.g., jscpd for JavaScript/TypeScript, or similar for other languages) to generate a duplication report. Prioritize eliminating exact duplicates first, then near-duplicates.
- **Module Boundaries**: Redefine module boundaries based on single-responsibility principle. Each module should have one reason to change. Use dependency inversion to decouple high-level modules from low-level details.
- **Test Infrastructure**: Ensure the existing test framework (to be confirmed) supports unit testing of isolated modules. Add mocking/stubbing capabilities if missing. Aim for at least 70% unit test coverage on refactored modules.
- **Incremental Refactoring**: Apply the Strangler Fig pattern: introduce new module interfaces alongside old ones, migrate callers gradually, then remove old code. Each commit should keep the codebase in a working state.
- **Architectural Constraints**: Respect existing ADRs. Do not change external APIs or data formats unless explicitly required. Maintain backward compatibility during the transition.

## Testing Decisions

- **Good Test Characteristics**: Tests should verify external behavior, not implementation details. They should be fast, deterministic, and isolated. Avoid testing private methods directly.
- **Modules to Test**: All newly extracted deep modules must have unit tests. Existing modules that are refactored should have their test coverage increased to at least 70%.
- **Prior Art**: Look for existing tests in the codebase that follow these principles. Use similar patterns (e.g., same test framework, same assertion style) to maintain consistency.

## Out of Scope

- Adding new features or functionality.
- Performance optimization unrelated to structural improvement.
- Rewriting the entire codebase from scratch.
- Changing external APIs or data formats.
- Updating documentation beyond what is necessary for module interfaces.
- Refactoring third-party dependencies.

## Further Notes

- The primary programming language(s) and test framework need to be confirmed before detailed planning.
- The desired outcome metrics (e.g., reduce duplicate lines by X%, improve test coverage to Y%) should be defined with stakeholders.
- All refactoring should be reviewed by at least one other developer to ensure quality.

## Completion Report

what_was_done: Produced a PRD for refactoring the roboease codebase, including problem statement, solution, user stories, implementation decisions, testing decisions, and out-of-scope items.
key_decisions:
  - decision: Use incremental refactoring (Strangler Fig pattern) to avoid long-lived branches.
    rationale: Minimizes risk and allows continuous integration.
  - decision: Extract deep modules for common functionality.
    rationale: Improves testability and reduces duplication.
  - decision: Prioritize elimination of exact duplicates first.
    rationale: Highest impact with lowest risk.
handoff_focus:
  - Confirm primary programming language(s) and test framework.
  - Define specific metrics for success (e.g., duplication reduction percentage, test coverage target).
  - Begin code analysis to identify duplication and structural issues.
open_questions:
  - What is the primary programming language(s) in the codebase?
  - Are there existing tests? If so, what framework is used?
  - Are there any architectural constraints (e.g., must remain compatible with certain libraries)?
  - What is the desired outcome metric (e.g., reduce duplicate lines by X%, improve test coverage to Y%)?
known_constraints:
  - No write access to the codebase; analysis only.
  - Must respect existing ADRs and out-of-scope decisions.
confidence_differential: 0.8
dissent_if_alone: null
iteration_context: null