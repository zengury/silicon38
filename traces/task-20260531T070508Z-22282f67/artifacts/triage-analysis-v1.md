## Analysis

### Problem Statement
The /Users/ZQ/roboease codebase has accumulated code duplication, unclear module boundaries, and low test coverage, leading to reduced maintainability and testability. The goal is to refactor the codebase to eliminate duplication, improve module structure, and enhance maintainability and testability.

### Scope
**In scope:**
- Identify and remove duplicate code across the codebase.
- Refactor module structure to improve separation of concerns.
- Improve testability by extracting pure functions, reducing coupling, and adding interfaces.
- Update or add unit tests for refactored modules.
- Update documentation to reflect new structure.

**Out of scope:**
- Adding new features or functionality.
- Performance optimization unless directly related to refactoring.
- Rewriting the entire codebase from scratch.
- Changing external APIs or user-facing behavior.
- Database schema changes.

### Recommended Agents
- `code-analyzer` (to scan for duplication and structural issues)
- `refactor-agent` (to perform the refactoring)
- `test-agent` (to write/update tests)
- `reviewer` (to review changes)

### Blocking Questions
- What is the preferred module structure? (e.g., feature-based vs layer-based)
- Are there any existing tests that must be preserved?
- What is the acceptable level of test coverage after refactoring?
- Are there any constraints on external dependencies?

### Priority
**High** – Code duplication and poor structure increase technical debt and slow down development. Early refactoring reduces future costs.

## Completion Report

```yaml
completion_report:
  what_was_done: "Classified the task as a refactoring effort, defined scope, recommended agents, and identified blocking questions."
  key_decisions:
    - decision: "Task is a refactoring/enhancement, not a bug fix."
      rationale: "The request focuses on improving code quality, not fixing a broken feature."
    - decision: "Scope excludes new features and API changes."
      rationale: "Refactoring should not alter external behavior."
  handoff_focus:
    - "Resolve blocking questions with the user before proceeding."
    - "Assign code-analyzer to scan for duplication."
  open_questions:
    - "Preferred module structure?"
    - "Existing tests to preserve?"
    - "Target test coverage?"
    - "Dependency constraints?"
  known_constraints:
    - "Must not break existing functionality."
    - "Must maintain backward compatibility."
  confidence_differential: 0.8
  dissent_if_alone: null
  iteration_context: null
```