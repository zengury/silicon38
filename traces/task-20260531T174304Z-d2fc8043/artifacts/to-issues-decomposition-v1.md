## Issues

### Issue 1: Identify and report code duplication in roboease

**Description:** Run a static analysis tool (e.g., jscpd for JavaScript/TypeScript, or similar for the actual language) on the entire codebase to generate a duplication report. The report should list exact and near-duplicate code blocks with file locations and line numbers. The output should be saved as a machine-readable file (e.g., JSON) for later comparison.

**Acceptance criteria:**
- [ ] A duplication report is generated covering all source files (excluding third-party dependencies).
- [ ] The report includes exact duplicates and near-duplicates (configurable threshold).
- [ ] The report is saved in a structured format (e.g., JSON) in a known location.
- [ ] A summary of total duplicate lines and percentage is printed to stdout.

**Estimated size:** M

**Blocked by:** None - can start immediately

---

### Issue 2: Extract deep module for file I/O operations

**Description:** Identify all file I/O operations scattered across the codebase. Create a new module (e.g., `file-io`) that encapsulates common file reading/writing patterns. The module should have a stable, documented interface. Migrate existing callers to use the new module. Keep the old code in place initially (Strangler Fig pattern).

**Acceptance criteria:**
- [ ] A new `file-io` module is created with functions for common file operations (read, write, append, etc.).
- [ ] The module has unit tests covering all public functions.
- [ ] At least 3 existing callers are migrated to use the new module.
- [ ] The old code remains functional and is marked as deprecated.
- [ ] Documentation for the module interface is added.

**Estimated size:** L

**Blocked by:** None - can start immediately

---

### Issue 3: Extract deep module for data transformation

**Description:** Identify all data transformation logic (e.g., parsing, formatting, conversion) scattered across the codebase. Create a new module (e.g., `data-transform`) that encapsulates common transformation patterns. The module should have a stable, documented interface. Migrate existing callers to use the new module. Keep the old code in place initially.

**Acceptance criteria:**
- [ ] A new `data-transform` module is created with functions for common transformations.
- [ ] The module has unit tests covering all public functions.
- [ ] At least 3 existing callers are migrated to use the new module.
- [ ] The old code remains functional and is marked as deprecated.
- [ ] Documentation for the module interface is added.

**Estimated size:** L

**Blocked by:** None - can start immediately

---

### Issue 4: Extract deep module for logging

**Description:** Identify all logging statements scattered across the codebase. Create a new module (e.g., `logger`) that provides a consistent logging interface (levels, formatting, output destinations). The module should have a stable, documented interface. Migrate existing callers to use the new module. Keep the old code in place initially.

**Acceptance criteria:**
- [ ] A new `logger` module is created with configurable log levels and output.
- [ ] The module has unit tests covering all public functions.
- [ ] At least 5 existing callers are migrated to use the new module.
- [ ] The old code remains functional and is marked as deprecated.
- [ ] Documentation for the module interface is added.

**Estimated size:** M

**Blocked by:** None - can start immediately

---

### Issue 5: Reorganize modules based on single-responsibility principle

**Description:** Review the current module structure and propose a reorganization that ensures each module has a single, clear responsibility. Create a dependency graph of the proposed modules. Implement the reorganization by moving files and updating imports. Ensure backward compatibility by keeping old module paths as re-exports during transition.

**Acceptance criteria:**
- [ ] A dependency graph of the new module structure is documented.
- [ ] Each module has a single responsibility documented in its README or header.
- [ ] The codebase compiles and tests pass after reorganization.
- [ ] Old module paths are preserved as re-exports (deprecated).
- [ ] No circular dependencies exist in the new structure.

**Estimated size:** L

**Blocked by:** None - can start immediately

---

### Issue 6: Add unit tests for refactored modules

**Description:** Write unit tests for all newly extracted deep modules (file-io, data-transform, logger) and any modules that were reorganized. Aim for at least 70% line coverage on these modules. Tests should be fast, deterministic, and isolated (use mocking/stubbing where needed).

**Acceptance criteria:**
- [ ] Unit tests exist for all public functions of file-io, data-transform, and logger modules.
- [ ] Unit tests exist for all reorganized modules.
- [ ] Test coverage is at least 70% for each tested module.
- [ ] Tests pass consistently (no flaky tests).
- [ ] Tests do not depend on external resources (network, filesystem) unless absolutely necessary.

**Estimated size:** L

**Blocked by:** 
- Issue 2: Extract deep module for file I/O operations
- Issue 3: Extract deep module for data transformation
- Issue 4: Extract deep module for logging
- Issue 5: Reorganize modules based on single-responsibility principle

---

### Issue 7: Eliminate exact duplicate code blocks

**Description:** Using the duplication report from Issue 1, refactor all exact duplicate code blocks into shared functions or modules. Prioritize high-impact duplicates (large blocks, many occurrences). Each refactoring should be done in a separate commit with a clear description.

**Acceptance criteria:**
- [ ] All exact duplicate blocks identified in the report are eliminated.
- [ ] Each elimination is done in a separate commit with a descriptive message.
- [ ] The codebase compiles and tests pass after each commit.
- [ ] A final duplication report shows reduction in duplicate lines.

**Estimated size:** L

**Blocked by:** 
- Issue 1: Identify and report code duplication in roboease

---

### Issue 8: Eliminate near-duplicate code blocks

**Description:** Using the duplication report from Issue 1, refactor near-duplicate code blocks into parameterized functions or templates. Prioritize high-impact near-duplicates. Each refactoring should be done in a separate commit with a clear description.

**Acceptance criteria:**
- [ ] All near-duplicate blocks identified in the report are eliminated (or justified as acceptable).
- [ ] Each elimination is done in a separate commit with a descriptive message.
- [ ] The codebase compiles and tests pass after each commit.
- [ ] A final duplication report shows reduction in duplicate lines.

**Estimated size:** L

**Blocked by:** 
- Issue 1: Identify and report code duplication in roboease

---

### Issue 9: Add linter/static analysis configuration

**Description:** Set up a linter (e.g., ESLint for JavaScript/TypeScript) and static analysis tool to enforce code quality rules: no duplicate code, consistent module structure, no circular dependencies, etc. Add configuration files and integrate with the build process. Document the rules and how to run the tools.

**Acceptance criteria:**
- [ ] A linter configuration is added to the project.
- [ ] A static analysis tool (e.g., dependency cruiser) is configured.
- [ ] The tools can be run via a single command (e.g., `npm run lint`).
- [ ] The tools pass on the current codebase (or known exceptions are documented).
- [ ] Documentation is added on how to use the tools.

**Estimated size:** M

**Blocked by:** None - can start immediately

---

### Issue 10: Generate before/after duplication metrics report

**Description:** After all refactoring is complete, run the duplication detection tool again and compare results with the initial report. Generate a summary report showing reduction in duplicate lines, percentage improvement, and any remaining duplication. Publish the report as a project document.

**Acceptance criteria:**
- [ ] A final duplication report is generated using the same tool and configuration as Issue 1.
- [ ] A comparison report shows before/after metrics (total duplicate lines, percentage).
- [ ] The report is saved in the project repository (e.g., `docs/duplication-report.md`).
- [ ] Any remaining duplication is documented with justification.

**Estimated size:** S

**Blocked by:** 
- Issue 7: Eliminate exact duplicate code blocks
- Issue 8: Eliminate near-duplicate code blocks

---

## Completion Report

```yaml
completion_report:
  what_was_done: Decomposed the PRD for refactoring the roboease codebase into 10 independently executable issues. Each issue has a clear title, description, acceptance criteria, estimated size, and dependency information. The dependency graph is acyclic: Issues 1,2,3,4,5,9 can start immediately; Issue 6 depends on 2,3,4,5; Issue 7 depends on 1; Issue 8 depends on 1; Issue 10 depends on 7 and 8.
  key_decisions:
    - decision: Created separate issues for extracting deep modules (file-io, data-transform, logger) to allow parallel work.
      rationale: These modules are independent and can be worked on simultaneously.
    - decision: Separated exact and near-duplicate elimination into two issues.
      rationale: Exact duplicates are lower risk and can be automated more easily; near-duplicates require more judgment.
    - decision: Added a dedicated issue for linter/static analysis configuration.
      rationale: Ensures structural quality is maintained after refactoring.
    - decision: Added a metrics report issue to measure success.
      rationale: Provides objective evidence of improvement.
  handoff_focus:
    - Confirm primary programming language and test framework to refine issue details.
    - Begin execution of independent issues (1,2,3,4,5,9) in parallel.
  open_questions:
    - What is the primary programming language(s) in the codebase?
    - Are there existing tests? If so, what framework is used?
    - Are there any architectural constraints (e.g., must remain compatible with certain libraries)?
    - What is the desired outcome metric (e.g., reduce duplicate lines by X%, improve test coverage to Y%)?
  known_constraints:
    - No write access to the codebase; analysis only.
    - Must respect existing ADRs and out-of-scope decisions.
  confidence_differential: 0.85
  dissent_if_alone: null
  iteration_context: null
```
