## Problem Statement

The codebase at /Users/ZQ/roboease suffers from duplicated code, unclear module structure, and low maintainability/testability. This increases technical debt, slows development velocity, and raises the risk of bugs. Developers spend excessive time understanding existing code and making changes without confidence.

## Solution

Refactor the codebase to eliminate duplicate code, reorganize modules into a clear, testable structure, and improve overall maintainability. The refactoring will be guided by automated analysis and manual review, with a focus on extracting deep modules that encapsulate functionality behind simple interfaces.

## User Stories

1. As a developer, I want to identify all duplicate code patterns, so that I can eliminate redundancy and reduce maintenance burden.
2. As a developer, I want a clear module structure (e.g., layered or feature-based), so that I can easily locate and understand code.
3. As a developer, I want each module to have a well-defined responsibility, so that changes are isolated and side effects are minimized.
4. As a developer, I want to extract deep modules that encapsulate complex logic behind simple interfaces, so that the codebase is easier to test and evolve.
5. As a developer, I want to improve test coverage and testability, so that I can make changes with confidence.
6. As a developer, I want to see a report of refactoring recommendations, so that I can prioritize work.
7. As a developer, I want to ensure that no existing functionality is broken during refactoring, so that the system remains stable.
8. As a developer, I want to establish coding standards and conventions, so that future code remains consistent.

## Implementation Decisions

- **Module Structure**: The codebase will be reorganized into a feature-based module structure, with each feature module containing its own components, services, and tests. Common utilities will be extracted into a shared module.
- **Deep Modules**: Identify opportunities to extract deep modules (e.g., a data access layer, a logging utility, a configuration manager) that encapsulate complex behavior behind simple, stable interfaces.
- **Duplication Detection**: Use static analysis tools (e.g., jscpd, PMD Copy/Paste Detector) to identify exact and near-miss duplicates. Manual review will confirm and prioritize removals.
- **Refactoring Approach**: Apply the Strangler Fig pattern for large changes: introduce new modules alongside old ones, gradually migrate callers, and remove old code once migration is complete.
- **Testing**: Ensure that existing tests pass after each refactoring step. Add unit tests for extracted modules. Integration tests should cover critical paths.
- **No New Features**: This PRD is strictly about refactoring. No new functionality will be introduced.

## Testing Decisions

- **What makes a good test**: Tests should verify external behavior, not implementation details. They should be resilient to refactoring. Unit tests should focus on individual modules in isolation, using mocks for dependencies.
- **Modules to test**: All extracted deep modules will have unit tests. Critical integration paths will have integration tests. Existing tests will be maintained and updated as needed.
- **Prior art**: The codebase may already have tests (to be confirmed). If so, follow the existing testing patterns and frameworks. If not, adopt a standard framework (e.g., Jest for JavaScript, pytest for Python) based on the language.

## Out of Scope

- New feature development
- Performance optimization unrelated to structure
- Dependency upgrades or security fixes
- UI/UX changes
- Database schema changes
- Deployment or infrastructure changes

## Further Notes

- The primary programming language(s) and existing test frameworks need to be confirmed before detailed planning.
- Architectural Decision Records (ADRs) must be respected.
- The refactoring should be done incrementally to minimize disruption.

## Completion Report

```yaml
completion_report:
  what_was_done: Produced PRD for refactoring /Users/ZQ/roboease codebase, including problem statement, solution, user stories, implementation decisions, testing decisions, out-of-scope items, and success criteria.
  key_decisions:
    - decision: Feature-based module structure
      rationale: Improves cohesion and developer navigation.
    - decision: Use Strangler Fig pattern for gradual migration
      rationale: Minimizes risk and allows incremental delivery.
    - decision: Extract deep modules for complex logic
      rationale: Encapsulates complexity behind simple interfaces, improving testability.
  handoff_focus:
    - Confirm primary language and existing tests before proceeding.
    - Begin code analysis to identify duplication and module boundaries.
  open_questions:
    - What is the primary programming language?
    - Are there existing tests and testing frameworks?
    - Are there any architectural constraints or ADRs?
    - What is the desired module structure (layered vs feature-based)?
  known_constraints:
    - No new features.
    - Must respect existing ADRs.
    - Refactoring must not break existing functionality.
  confidence_differential: 0.7
  dissent_if_alone: null
  iteration_context: null
```