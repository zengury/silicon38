## Issues

### Issue 1: Detect and Report Duplicate Code Patterns
- **Description**: Run a static analysis tool (e.g., jscpd for JS/TS) on the codebase to identify exact and near-miss duplicate code. Generate a report file listing all duplicates with file paths, line numbers, and similarity percentages. The report will be used to prioritize refactoring.
- **Acceptance Criteria**:
  - [ ] A duplicate detection tool is selected and configured.
  - [ ] The tool runs successfully on the entire codebase.
  - [ ] A report file (e.g., `duplicates-report.json`) is generated in the project root.
  - [ ] The report includes at least file paths, line numbers, and similarity scores.
- **Estimated Size**: M
- **Blocked By**: None - can start immediately

### Issue 2: Extract Shared Utility Functions into `shared/utils` Module
- **Description**: Identify common utility functions (e.g., string manipulation, date formatting, error handling) that are duplicated across the codebase. Extract them into a new `shared/utils` module with a stable API. Update all existing usages to import from the new module. Ensure backward compatibility by keeping original functions as deprecated wrappers if needed.
- **Acceptance Criteria**:
  - [ ] A `shared/utils` directory is created with appropriate module files.
  - [ ] At least three distinct utility functions are extracted and deduplicated.
  - [ ] All original usages are updated to import from `shared/utils`.
  - [ ] Existing tests pass without modification.
  - [ ] No new duplication introduced.
- **Estimated Size**: M
- **Blocked By**: Issue 1 (to know which duplicates to extract)

### Issue 3: Define Feature-Based Module Structure and Migrate Core Module
- **Description**: Define a feature-based module structure (each feature has its own directory with code, tests, and docs). Choose one core module (e.g., the most stable or smallest) and migrate it to the new structure. Update imports and ensure all tests pass. Document the new structure in a `MODULE_STRUCTURE.md` file.
- **Acceptance Criteria**:
  - [ ] A `MODULE_STRUCTURE.md` file is created describing the feature-based layout.
  - [ ] One core module is migrated to the new structure.
  - [ ] All imports are updated and the application builds successfully.
  - [ ] All existing tests pass.
- **Estimated Size**: L
- **Blocked By**: None - can start immediately (can be done in parallel with Issue 1)

### Issue 4: Introduce Interfaces and Dependency Injection for a Core Module
- **Description**: For a core module that currently has hard-coded dependencies (e.g., database, external service), define an interface for that dependency and refactor the module to accept the dependency via constructor or function parameter. Update the composition root to wire the real implementation. Add unit tests that mock the dependency.
- **Acceptance Criteria**:
  - [ ] An interface is defined for the dependency (e.g., `IDatabase`).
  - [ ] The core module is refactored to accept the dependency via injection.
  - [ ] The composition root is updated to provide the real implementation.
  - [ ] Unit tests are added that mock the dependency and verify behavior.
  - [ ] All existing tests pass.
- **Estimated Size**: M
- **Blocked By**: Issue 3 (to have a stable module structure)

### Issue 5: Add Unit Tests for Core Modules
- **Description**: Write unit tests for core modules (business logic, data access, utilities) using the existing or chosen testing framework. Aim for at least 60% line coverage on the modules under test. Tests should verify external behavior, not implementation details, and mock external dependencies.
- **Acceptance Criteria**:
  - [ ] Testing framework is confirmed or set up.
  - [ ] Unit tests are written for at least three core modules.
  - [ ] Line coverage for each module is at least 60%.
  - [ ] Tests are isolated, fast, and deterministic.
  - [ ] All tests pass.
- **Estimated Size**: L
- **Blocked By**: Issue 4 (to have testable interfaces)

### Issue 6: Measure Code Coverage Before and After Refactoring
- **Description**: Set up a code coverage tool (e.g., Istanbul for JS/TS, JaCoCo for Java) and run it on the current codebase to get a baseline coverage report. After the refactoring issues are complete, run the tool again and compare results. Document the improvement in a `COVERAGE_REPORT.md` file.
- **Acceptance Criteria**:
  - [ ] A coverage tool is configured and produces a baseline report.
  - [ ] After all refactoring, a final coverage report is generated.
  - [ ] A `COVERAGE_REPORT.md` file compares before/after coverage percentages.
  - [ ] The report highlights modules with significant improvement.
- **Estimated Size**: S
- **Blocked By**: Issue 5 (to have tests to measure)

### Issue 7: Document New Module Structure and Interfaces
- **Description**: Write comprehensive documentation for the new feature-based module structure, including the purpose of each module, key interfaces, and how to add a new feature. Update any existing documentation to reflect the changes. The documentation should be in the repository's `docs/` folder.
- **Acceptance Criteria**:
  - [ ] A `docs/module-structure.md` file describes the new structure.
  - [ ] Key interfaces are documented with examples.
  - [ ] A guide on adding a new feature is included.
  - [ ] Existing documentation is updated to remove references to old structure.
- **Estimated Size**: S
- **Blocked By**: Issue 3 (to have a defined structure)

## Completion Report

```yaml
completion_report:
  what_was_done: Decomposed the PRD for refactoring the roboease codebase into 7 independently implementable issues with acceptance criteria, estimated sizes, and dependency relationships.
  key_decisions:
    - decision: Use vertical slices (tracer bullets) for each issue.
      rationale: Ensures each issue delivers end-to-end value and is independently testable.
    - decision: Separate duplicate detection into its own issue.
      rationale: Provides data-driven prioritization for extraction work.
    - decision: Migrate module structure incrementally, starting with one core module.
      rationale: Reduces risk and allows learning before scaling.
    - decision: Add unit tests after dependency injection is in place.
      rationale: Ensures testability improvements are leveraged.
  handoff_focus:
    - Execute issues in dependency order: start with Issues 1 and 3 in parallel.
    - After Issue 1 completes, begin Issue 2.
    - After Issue 3 completes, begin Issue 4, then Issue 5, then Issue 6.
    - Issue 7 can be done after Issue 3.
  open_questions:
    - What is the primary programming language(s) in the codebase?
    - Are there existing tests? If so, what framework?
    - Is there a preferred module structure (e.g., feature-based, layered)?
    - Are there any constraints (e.g., must maintain backward compatibility)?
  known_constraints:
    - Must maintain backward compatibility.
    - Refactoring must be incremental to avoid long-lived branches.
  confidence_differential: 0.85
  dissent_if_alone: null
  iteration_context: null
```

## Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read:
      - artifacts/to-prd-prd-v1.md
    handoffs_read:
      - handoffs/to-prd→to-issues-20260531-172214.yaml
  retained_context:
    decisions:
      - statement: Adopt feature-based module structure.
        source: to-prd-prd-v1
        impact: Affects module organization in issues.
      - statement: Use static analysis for duplicate detection.
        source: to-prd-prd-v1
        impact: Drives Issue 1.
      - statement: Introduce dependency injection for testability.
        source: to-prd-prd-v1
        impact: Drives Issue 4.
      - statement: Incremental refactoring with backward compatibility.
        source: to-prd-prd-v1
        impact: Constrains all issues.
    constraints:
      - statement: Must maintain backward compatibility.
        source: to-prd-prd-v1
        impact: All issues must preserve public APIs.
      - statement: Refactoring must be incremental.
        source: to-prd-prd-v1
        impact: Issues are small and reversible.
    assumptions:
      - statement: Codebase is at /Users/ZQ/roboease and is accessible.
        source: handoff
        risk: Assumption may need review.
      - statement: Task is a general refactoring request.
        source: handoff
        risk: Assumption may need review.
    open_questions:
      - statement: Primary language?
        source: handoff
        owner: runtime
      - statement: Existing tests?
        source: handoff
        owner: runtime
      - statement: Preferred module structure?
        source: handoff
        owner: runtime
      - statement: Backward compatibility constraints?
        source: handoff
        owner: runtime
  omitted_context:
    - source: to-prd-prd-v1
      reason: Detailed implementation decisions (e.g., specific tools) are not needed for issue decomposition; they can be decided during implementation.
  compression_rationale:
    method: Retained all decisions, constraints, assumptions, and open questions from the PRD and handoff. Omitted detailed implementation decisions that are not necessary for issue decomposition.
    loss_notes:
      - Omitted specific tool recommendations (e.g., jscpd, Jest) as they are implementation details.
  quality_checks:
    - name: independent_issues_present
      passed: true
    - name: dependencies_named
      passed: true
    - name: acceptance_criteria_present
      passed: true
    - name: dependency_graph_acyclic
      passed: true
```