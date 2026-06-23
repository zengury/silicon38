## Analysis

### Problem Statement
The codebase at /Users/ZQ/roboease contains duplicated code, unclear module structure, and low maintainability/testability, which increases technical debt and slows development.

### Scope
**In Scope:**
- Identify duplicate code patterns across the codebase
- Assess current module structure and propose improvements
- Evaluate test coverage and testability
- Provide recommendations for refactoring

**Out of Scope:**
- Actual code changes or refactoring implementation
- Performance optimization unrelated to structure
- Dependency upgrades or security fixes
- New feature development

### Recommended Agents
- code_analyzer (for static analysis and duplication detection)
- architect (for module restructuring)
- quality_engineer (for testability assessment)

### Blocking Questions
- What is the primary programming language(s) in the codebase?
- Are there existing tests? What testing framework is used?
- Are there any architectural constraints or ADRs to respect?
- What is the desired module structure (e.g., layered, feature-based)?

### Priority
**High** – Duplicate code and poor structure directly impact development velocity and bug rates.

## Completion Report

```yaml
completion_report:
  what_was_done: Triaged the request to optimize/refactor /Users/ZQ/roboease codebase. Produced problem statement, scope, recommended agents, and blocking questions.
  key_decisions:
    - decision: Classified as enhancement (refactoring) rather than bug.
      rationale: The request is about improving code quality, not fixing a broken feature.
    - decision: Recommended code_analyzer, architect, and quality_engineer agents.
      rationale: These roles cover duplication detection, structural improvement, and testability.
  handoff_focus:
    - Clarify blocking questions with user before proceeding.
    - Prepare detailed analysis of codebase once language and constraints are known.
  open_questions:
    - What is the primary programming language?
    - Are there existing tests and frameworks?
    - Any architectural constraints?
    - Desired module structure?
  known_constraints:
    - Cannot modify code in this triage step.
    - Must respect existing ADRs and out-of-scope decisions.
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
      - Task is enhancement/refactoring, not bug.
      - Recommended agents: code_analyzer, architect, quality_engineer.
    constraints:
      - No code changes during triage.
      - Must respect ADRs and out-of-scope knowledge base.
    assumptions:
      - Codebase is primarily one language (to be confirmed).
      - User wants actionable recommendations, not implementation.
    open_questions:
      - Primary language?
      - Existing tests?
      - Architectural constraints?
      - Desired module structure?
  omitted_context:
    - Detailed code analysis (not yet performed).
    - Specific duplicate code locations (unknown).
  compression_rationale:
    method: Focused on triage output and blocking questions; omitted speculative details.
    loss_notes: []
  quality_checks:
    - name: problem_statement_falsifiable
      passed: true
    - name: scope_boundary_present
      passed: true
    - name: recommended_agents_derived_from_problem
      passed: true
    - name: blocking_questions_specific
      passed: true
```