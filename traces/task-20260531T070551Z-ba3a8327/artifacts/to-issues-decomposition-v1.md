## Issues

### Issue 1: Extract duplicate utility functions into shared module
- **Title**: Extract duplicate utility functions into shared module
- **Description**: Identify and consolidate duplicated utility functions (e.g., string helpers, validation logic, constants) across the codebase into a single shared module under `src/shared/utils/`. Ensure all existing callers are updated to import from the new module. No behavior changes.
- **Acceptance Criteria**:
  - [ ] All duplicate utility functions are moved to `src/shared/utils/` with appropriate naming.
  - [ ] All original callers are updated to import from the new module.
  - [ ] Existing tests pass without modification.
  - [ ] No new functionality introduced.
- **Estimated Size**: M
- **Blocked By**: None - can start immediately

### Issue 2: Define and implement layered module structure
- **Title**: Define and implement layered module structure
- **Description**: Agree on a layered architecture (e.g., presentation, business logic, data access) and restructure existing modules accordingly. Move files into new directories, update imports, and ensure separation of concerns. This includes creating `src/presentation/`, `src/business/`, `src/data/` directories and relocating relevant code.
- **Acceptance Criteria**:
  - [ ] Team agrees on the layered structure (documented in ADR or README).
  - [ ] Existing modules are moved to appropriate layers.
  - [ ] All imports are updated and code compiles/runs.
  - [ ] Existing tests pass.
- **Estimated Size**: L
- **Blocked By**: None - can start immediately

### Issue 3: Introduce dependency injection for core business logic
- **Title**: Introduce dependency injection for core business logic
- **Description**: Refactor core business logic modules to accept dependencies via constructor or function parameters instead of hardcoded imports. This improves testability and decouples modules. Start with one critical module (e.g., order processing) as a pilot.
- **Acceptance Criteria**:
  - [ ] At least one core business logic module uses dependency injection.
  - [ ] Existing behavior is preserved (tests pass).
  - [ ] Unit tests can be written for the module without complex setup.
- **Estimated Size**: M
- **Blocked By**: Issue 2 (layered structure provides clear boundaries)

### Issue 4: Add unit tests for extracted utility module
- **Title**: Add unit tests for extracted utility module
- **Description**: Write comprehensive unit tests for the shared utility module created in Issue 1. Cover all exported functions with edge cases. Follow existing test patterns (Jest/Mocha).
- **Acceptance Criteria**:
  - [ ] All functions in the shared utility module have unit tests.
  - [ ] Tests cover normal cases, edge cases, and error conditions.
  - [ ] Tests are written using the project's existing test framework.
  - [ ] All tests pass.
- **Estimated Size**: S
- **Blocked By**: Issue 1

### Issue 5: Add unit tests for core business logic module with DI
- **Title**: Add unit tests for core business logic module with DI
- **Description**: Write unit tests for the core business logic module that was refactored with dependency injection in Issue 3. Use mocking to isolate the module under test.
- **Acceptance Criteria**:
  - [ ] Unit tests exist for the refactored module.
  - [ ] Tests use mocks for dependencies.
  - [ ] Tests verify external behavior, not implementation details.
  - [ ] All tests pass.
- **Estimated Size**: S
- **Blocked By**: Issue 3

### Issue 6: Add integration tests for critical workflows
- **Title**: Add integration tests for critical workflows
- **Description**: Write integration tests that cover end-to-end critical workflows (e.g., user registration, order placement). Ensure that the refactored modules work together correctly.
- **Acceptance Criteria**:
  - [ ] At least two critical workflows are covered by integration tests.
  - [ ] Tests run against the actual codebase (no mocking of core modules).
  - [ ] All tests pass.
- **Estimated Size**: M
- **Blocked By**: Issues 1, 2, 3 (core refactoring complete)

### Issue 7: Enforce consistent naming and structure conventions
- **Title**: Enforce consistent naming and structure conventions
- **Description**: Review the codebase for inconsistent naming (e.g., file names, variable names, module exports) and align them with a documented convention. Update linting rules if applicable. This is a cleanup pass after major restructuring.
- **Acceptance Criteria**:
  - [ ] Naming conventions are documented in CONTRIBUTING.md or similar.
  - [ ] All files and modules follow the convention.
  - [ ] Linting rules (if any) are updated to enforce conventions.
  - [ ] Existing tests pass.
- **Estimated Size**: S
- **Blocked By**: Issue 2 (structure is settled)

## Completion Report

```yaml
completion_report:
  what_was_done: Decomposed the PRD for refactoring /Users/ZQ/roboease into 7 independent issues with acceptance criteria, estimated sizes, and dependency relationships.
  key_decisions:
    - decision: Use vertical slices that cut across layers (extraction, restructuring, DI, testing) rather than horizontal layers.
      rationale: Each issue is independently completable and demoable, aligning with the skill's tracer bullet approach.
    - decision: Order issues so that foundational refactoring (extraction, restructuring) comes first, then DI, then testing.
      rationale: Testing depends on stable modules; DI depends on clear module boundaries.
    - decision: Mark Issue 2 (layered structure) as L due to coordination overhead; all others are S or M.
      rationale: Restructuring requires team agreement and careful file moves; utility extraction and testing are more contained.
  handoff_focus:
    - Review issue granularity and dependency graph for correctness.
    - Confirm that acceptance criteria are verifiable without full system.
  open_questions:
    - Preferred module structure details? (to be decided in Issue 2)
    - Any files off-limits for refactoring? (assumed none)
  known_constraints:
    - No new features or API changes.
    - All existing tests must pass after each change.
  confidence_differential: 0.9
  dissent_if_alone: null
  iteration_context: null
```

## Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read:
      - to-prd-prd-v1
    handoffs_read:
      - handoffs/to-prd→to-issues-20260531-070629.yaml
  retained_context:
    decisions:
      - statement: Task is a refactoring enhancement
        source: semantic_node_executor
        impact: Affects downstream node execution.
      - statement: Priority is high
        source: semantic_node_executor
        impact: Affects downstream node execution.
    constraints:
      - statement: No new features
        source: semantic_node_executor
        impact: Constrains downstream node execution.
      - statement: Preserve existing behavior
        source: semantic_node_executor
        impact: Constrains downstream node execution.
    assumptions:
      - statement: Codebase is at /Users/ZQ/roboease
        source: semantic_node_executor
        risk: Assumption may need review.
      - statement: Refactoring will improve maintainability and testability
        source: semantic_node_executor
        risk: Assumption may need review.
    open_questions:
      - statement: Preferred module structure?
        source: semantic_node_executor
        owner: runtime
      - statement: Any files off-limits?
        source: semantic_node_executor
        owner: runtime
  omitted_context:
    - source: Detailed code analysis (not yet performed)
      reason: background_only
    - source: Specific duplicate instances (not yet identified)
      reason: background_only
  compression_rationale:
    method: Retain high-level scope and constraints from PRD; omit low-level code details not yet available.
    loss_notes:
      - No code-level specifics retained; will be gathered by downstream agents.
  quality_checks:
    - name: scope_boundary_present
      passed: true
    - name: done_condition_present
      passed: true
```