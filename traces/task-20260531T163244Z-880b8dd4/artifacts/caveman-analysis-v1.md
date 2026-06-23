## Plain-Language Explanation

This codebase has three problems:
1. Same code written many times (duplication). Fix one place, miss others -> bugs.
2. Modules do too many things (unclear boundaries). Hard to find where change goes.
3. Not enough tests. Change code, no safety net.

Goal: Clean up without changing what the software does. No new features. No API changes.

## Minimum Viable Version

1. Find all duplicate code blocks using a tool (e.g., `jscpd`).
2. Pick one module. Extract shared code into one function/class.
3. Update all callers to use the shared version.
4. Run existing tests. If none, add one test per extracted function.
5. Repeat for next module.

That's it. No new architecture. No interface extraction unless needed for testing.

## Complexity Assessment

**Justified complexity:**
- Using static analysis to find duplicates (saves manual search).
- Writing tests for extracted code (catches regressions).

**Unnecessary complexity:**
- Feature-based module restructuring before duplication removal. Start with duplication, then reorganize if needed.
- Extracting interfaces for all modules upfront. Only extract when a module has external dependencies that block unit testing.
- Full documentation of module interfaces before refactoring. Document after changes stabilize.

**Tradeoff:** Feature-based structure improves navigation but adds churn. Layer-based is simpler but may not reduce duplication. Start with duplication removal; structure emerges.

## Completion Report

```yaml
completion_report:
  what_was_done: Analyzed PRD for roboease refactoring. Identified minimum viable version and unnecessary complexity.
  key_decisions:
    - decision: Start with duplication removal, not module restructuring.
      rationale: Duplication is root cause of maintenance cost. Restructuring without removing duplication adds churn.
    - decision: Extract interfaces only when needed for testing.
      rationale: Premature abstraction adds complexity without immediate benefit.
  handoff_focus:
    - "Duplicate detection tool selection (jscpd, PMD, etc.)"
    - "First module to refactor: pick one with highest duplication density"
  open_questions:
    - "Does codebase have existing tests? If yes, what framework?"
    - "Team preference for module structure after duplication removal?"
  known_constraints:
    - Must not change external behavior.
    - Codebase path: /Users/ZQ/roboease.
  confidence_differential: 0.8
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
      - handoffs/to-prd→caveman-20260531-163320.yaml
  retained_context:
    decisions:
      - statement: Task is a refactoring task.
      - statement: Adopt feature-based module structure.
      - statement: Use static analysis to identify duplicates.
      - statement: Incremental refactoring per module.
    constraints:
      - statement: Must not change external behavior.
      - statement: Codebase path: /Users/ZQ/roboease.
      - statement: Existing tests must be preserved.
    assumptions:
      - statement: User wants to improve maintainability and testability.
      - statement: Existing tests may exist but are not guaranteed.
    open_questions:
      - statement: Preferred module structure (feature-based vs layer-based)?
      - statement: Existing test preservation requirements?
      - statement: Risk tolerance for refactoring?
  omitted_context:
    - "User stories 4-7 (test preservation, new tests, incremental, documentation) are covered by minimum viable version."
    - "Out of scope items (new features, API changes, etc.) are already clear."
  compression_rationale:
    method: Retained only decisions and constraints directly relevant to execution. Omitted redundant user stories and out-of-scope list.
    loss_notes: []
  quality_checks:
    - name: Explanation passes non-engineer test
      passed: true
    - name: Minimum viable version is simpler than PRD
      passed: true
    - name: Complexity tradeoff named
      passed: true
```