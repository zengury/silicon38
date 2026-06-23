## Analysis

### Problem Statement
The HRBP test task is ambiguous. It is not clear what specific issue, bug, or enhancement is being referred to. The task lacks a description, issue number, or any context to classify and triage.

### Scope
- **In scope**: Clarify the task by requesting more information from the user.
- **Out of scope**: Any solution, code changes, or detailed investigation until the task is clarified.

### Recommended Agents
- orchestrator (to handle user interaction and re-triage after clarification)

### Blocking Questions
- What is the specific issue or request? Please provide a description, issue link, or more details.
- Is this a bug report, feature request, or something else?
- What is the expected outcome or desired action?

### Priority
- **Medium** – The task cannot proceed without clarification, but it is not urgent until more context is provided.

## Completion Report

- **what_was_done**: Analyzed the incoming task "hrbp test" and determined it is ambiguous. Produced a structured work item with blocking questions.
- **key_decisions**:
  - decision: Task is ambiguous and requires user clarification before further triage.
    rationale: No issue description, link, or context was provided.
- **handoff_focus**:
  - Return to orchestrator with blocking questions to resolve ambiguity.
- **open_questions**:
  - What is the specific issue or request?
- **known_constraints**:
  - No codebase access or issue tracker available to gather context.
- **confidence_differential**: 0.9
- **dissent_if_alone**: null
- **iteration_context**: null

## Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read: []
    handoffs_read: []
  retained_context:
    decisions:
      - Task is ambiguous; needs user clarification.
    constraints:
      - No issue details provided.
    assumptions:
      - The task is a request to triage an issue, but the issue is unspecified.
    open_questions:
      - What is the specific issue or request?
  omitted_context: []
  compression_rationale:
    method: Minimal retention; only the key ambiguity and blocking questions are kept.
    loss_notes: []
  quality_checks:
    - name: scope_boundary_present
      passed: true
    - name: done_condition_present
      passed: true
```