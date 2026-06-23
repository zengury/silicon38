## Analysis

### Problem Statement
The codebase at /Users/ZQ/roboease contains duplicated code, unclear module boundaries, and insufficient test coverage, leading to reduced maintainability and increased risk of defects.

### Scope
**In Scope:**
- Identify and catalog duplicate code across the codebase.
- Propose module restructuring to improve separation of concerns.
- Recommend testability improvements (e.g., dependency injection, interface extraction).
- Suggest refactoring patterns (e.g., DRY, SOLID) without altering external behavior.

**Out of Scope:**
- Adding new features or functionality.
- Rewriting the entire codebase.
- Performance optimization unless directly related to code duplication.
- Changes to external APIs or user-facing behavior.

### Recommended Agents
- `refactoring-agent` (primary)
- `testing-agent` (secondary)

### Blocking Questions
- What is the preferred module structure (e.g., feature-based vs layer-based)?
- Are there any existing tests that must be preserved or updated?
- What is the acceptable risk level for refactoring (e.g., must maintain backward compatibility)?

### Priority
**High** – Duplicate code and poor structure increase maintenance cost and defect risk; early refactoring reduces technical debt.

## Completion Report

```yaml
completion_report:
  what_was_done: Triaged the task to optimize and refactor the roboease codebase. Produced problem statement, scope, recommended agents, and blocking questions.
  key_decisions:
    - decision: Classified as a refactoring task, not a feature request.
      rationale: The task explicitly mentions eliminating duplicate code and improving structure, not adding new functionality.
    - decision: Recommended refactoring-agent and testing-agent.
      rationale: Refactoring requires structural changes; testing agent ensures testability improvements.
  handoff_focus:
    - Confirm blocking questions with user.
    - Proceed with code analysis and refactoring plan.
  open_questions:
    - Preferred module structure?
    - Existing test preservation requirements?
    - Risk tolerance for refactoring?
  known_constraints:
    - Must not alter external behavior.
    - Codebase is at /Users/ZQ/roboease.
  confidence_differential: 0.8
  dissent_if_alone: null
  iteration_context: null
```

## Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read: []
    handoffs_read: []
  retained_context:
    decisions:
      - Task is a refactoring task.
      - Primary agent: refactoring-agent; secondary: testing-agent.
    constraints:
      - Must not change external behavior.
      - Codebase path: /Users/ZQ/roboease.
    assumptions:
      - User wants to improve maintainability and testability.
      - Existing tests may exist but are not guaranteed.
    open_questions:
      - Preferred module structure?
      - Existing test preservation?
      - Risk tolerance?
  omitted_context: []
  compression_rationale:
    method: Extracted only task-relevant information; omitted general triage instructions.
    loss_notes: []
  quality_checks:
    - name: Problem statement is falsifiable
      passed: true
    - name: Scope includes out-of-scope items
      passed: true
    - name: Recommended agents derived from problem
      passed: true
    - name: Blocking questions specific and actionable
      passed: true
```