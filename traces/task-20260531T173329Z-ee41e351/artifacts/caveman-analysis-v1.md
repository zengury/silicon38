## Caveman Analysis: roboease Refactor

### Plain-Language Explanation

roboease is a codebase with problems:
- Same code written many times (duplication).
- Files mixed up, no clear job (poor module structure).
- Hard to change without breaking things (low maintainability).
- Hard to write tests (low testability).

Goal: Clean it up. No new features. Just make code simpler, less repetitive, easier to test.

### Minimum Viable Version

1. Find all exact duplicate functions. Move to one shared file.
2. Group files by what they do (e.g., all file-reading code together).
3. Make classes take dependencies via constructor (dependency injection).
4. Run existing tests after each change. Fix if broken.

That's it. No new patterns, no big rewrite.

### Complexity Assessment

**Justified complexity:**
- Dependency injection: needed for testability. Worth it.
- Module grouping: needed for navigation. Worth it.

**Unnecessary complexity:**
- Over-engineering abstractions (e.g., factory pattern for simple utils). Avoid.
- Renaming everything at once. Do only where confusing.
- Adding new lint rules or tooling. Not needed now.

### Completion Report

```yaml
completion_report:
  what_was_done: Analyzed roboease refactor task from first principles. Identified minimum viable steps and unnecessary complexity.
  key_decisions:
    - decision: Focus on deduplication and module grouping first.
      rationale: Highest impact, lowest risk.
    - decision: Avoid new abstractions beyond DI.
      rationale: Keep simple, avoid over-engineering.
  handoff_focus:
    - Start with deduplication scan.
    - Then module restructuring.
  open_questions:
    - Exact language and directory structure?
    - Existing test framework?
  known_constraints:
    - Cannot write files or run commands.
    - No access to external issue tracker.
  confidence_differential: 0.8
  dissent_if_alone: null
  iteration_context: null
```

### Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read:
      - to-prd-prd-v1
    handoffs_read:
      - handoffs/to-prd→caveman-20260531-173413.yaml
  retained_context:
    decisions:
      - Task is refactoring/enhancement, no new features.
      - Scope excludes full rewrite.
    constraints:
      - Cannot write files or execute commands.
      - No external issue tracker access.
    assumptions:
      - Codebase likely Python or TypeScript.
      - Tests may be absent or minimal.
    open_questions:
      - Exact directory structure and languages.
      - Existing test coverage and frameworks.
      - Priority between deduplication vs. long-term refactoring.
  omitted_context:
    - Detailed codebase analysis (not yet performed).
    - Specific instances of duplicate code.
  compression_rationale:
    method: Extracted key decisions, constraints, and open questions from upstream handoff and PRD. Omitted speculative details.
    loss_notes:
      - No loss of critical information.
  quality_checks:
    - name: explanation_passes_non_engineer_test
      passed: true
    - name: minimum_viable_version_simpler_than_existing
      passed: true
    - name: complexity_tradeoff_named
      passed: true
```