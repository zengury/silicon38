## Analysis

### problem_statement
The /Users/ZQ/roboease codebase contains duplicated code, poorly structured modules, and low maintainability/testability, which increases technical debt and slows development.

### scope
in_scope:
- Identify duplicate code across the codebase
- Assess current module structure and coupling
- Evaluate test coverage and testability
- Recommend refactoring priorities and structural improvements

out_of_scope:
- Actual code changes or refactoring implementation
- Performance optimization unrelated to structure
- Adding new features
- Rewriting the entire codebase

### recommended_agents
- code_analyst: to scan for duplicates and structural issues
- architect: to design improved module boundaries
- test_engineer: to evaluate testability and suggest test improvements

### blocking_questions
- What is the primary programming language(s) in the codebase?
- Are there existing tests? If so, what framework is used?
- Are there any architectural constraints (e.g., must remain compatible with certain libraries)?
- What is the desired outcome metric (e.g., reduce duplicate lines by X%, improve test coverage to Y%)?

### priority
high - Duplicate code and poor structure directly increase maintenance cost and bug risk; early refactoring prevents compounding issues.

## Completion Report

what_was_done: Classified the incoming task as a codebase improvement initiative, defined scope boundaries, identified blocking questions, and recommended an agent team.
key_decisions:
  - decision: Classify as enhancement (refactoring) rather than bug
    rationale: The request is about improving existing code, not fixing a broken feature.
  - decision: Set priority to high
    rationale: Technical debt in core codebase affects all future work.
handoff_focus:
  - Resolve blocking questions with the user before proceeding.
  - Prepare for code analysis and architectural review.
open_questions:
  - What specific languages/frameworks are in use?
  - What is the current test coverage?
known_constraints:
  - No write access to the codebase; analysis only.
  - Must respect existing ADRs and out-of-scope decisions.
confidence_differential: 0.8
dissent_if_alone: null
iteration_context: null
