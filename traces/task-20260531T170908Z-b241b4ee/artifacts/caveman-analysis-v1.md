## Plain-Language Explanation

Codebase at /Users/ZQ/roboease has same code copied in many places. Modules mix everything together. Hard to change one thing without breaking another. Hard to test. Developers waste time figuring out what code does.

Goal: Clean up without changing what the system does. No new features.

## Minimum Viable Version

1. Find all duplicate code blocks. Move each to one shared file.
2. Split modules by job: data access, business logic, UI. Each module does one thing.
3. Each module exposes only a few functions. Hide internals.
4. Write tests for each shared module.
5. Do changes in small steps. Keep system working after each step.

That's it. Everything else is extra.

## Complexity Assessment

**Justified complexity:**
- Incremental refactoring (small steps) – reduces risk.
- Tests for extracted modules – ensures correctness.
- Layered architecture – standard, well-understood.

**Unnecessary complexity:**
- Abstract base classes or protocols for every module interface – adds indirection without clear benefit. Simple functions or classes suffice.
- >80% coverage target – arbitrary. Test critical paths first.
- Feature flags or branch-by-abstraction – overkill for internal refactoring. Use short-lived branches.
- Formal documentation of module structure – code should be self-documenting. Minimal README is enough.

**Simpler approach:**
- Start with one module with most duplication. Extract, test, merge. Repeat.
- No new abstraction patterns. Use existing language features.
- No coverage percentage goal. Test what breaks.

## Completion Report

```yaml
completion_report:
  what_was_done: Analyzed PRD for unnecessary complexity. Identified minimum viable refactoring steps.
  key_decisions:
    - decision: Drop abstract base classes requirement
      rationale: Adds indirection without proven need. Simple functions work.
    - decision: Drop >80% coverage target
      rationale: Arbitrary. Test critical paths first.
    - decision: Drop feature flags / branch-by-abstraction
      rationale: Overkill for internal refactoring. Short-lived branches suffice.
  handoff_focus:
    - Start with most duplicated module.
    - Extract shared code, test, merge.
    - Keep changes small and reversible.
  open_questions:
    - Which module has most duplication?
    - What test framework exists?
    - Primary language?
  known_constraints:
    - No code modification during analysis.
    - Must use read-only tools.
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
      - handoffs/to-prd→caveman-20260531-170955.yaml
  retained_context:
    decisions:
      - Classify as enhancement (refactoring)
      - Priority high
    constraints:
      - No code modification during triage
      - Must use read-only tools
    assumptions:
      - Codebase is primarily one language
      - Existing tests may exist
    open_questions:
      - Primary language?
      - Existing tests?
      - Module structure?
  omitted_context:
    - Detailed user stories (8 items) – not needed for complexity assessment.
    - Implementation decisions about testing strategy details.
    - Out of scope list – already clear from PRD.
  compression_rationale:
    method: Extract key decisions, constraints, and open questions. Omit verbose descriptions and template boilerplate.
    loss_notes: []
  quality_checks:
    - name: scope_boundary_present
      passed: true
    - name: done_condition_present
      passed: true
```