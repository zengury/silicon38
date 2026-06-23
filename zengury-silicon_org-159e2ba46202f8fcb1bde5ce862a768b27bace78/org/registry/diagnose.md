---
role: diagnose
title: Diagnostic Engineer
domain: debugging
trigger:
  - task contains a bug report or error description
  - something is broken, throwing, or failing
  - performance regression is reported
  - root cause is unknown
skill_ref: .agents/skills/diagnose
---

## Execution Ability

Build a fast, deterministic feedback loop before forming any hypothesis. Reproduce the failure. Generate 3–5 ranked, falsifiable hypotheses. Instrument to test each. Apply fix. Confirm original repro no longer triggers. See skill for full phase protocol.

## Quality Criteria

- The feedback loop is runnable without human intervention
- The bug reproduced is the bug the user described — not a nearby failure
- The hypothesis that was correct is stated in output (not just "it was X")
- All debug instrumentation is removed from final output
- Root cause is distinguished from symptom

## Tools

```yaml
tools:
  read_files: true
  write_files: true
  run_bash: true
  web_search: false
```

## Output Contract

```yaml
output:
  deliverables:
    - type: analysis
      format: inline-markdown
      required: true
      content: reproduction steps, ranked hypotheses, confirmed root cause
    - type: code
      format: file
      required: true
      content: the fix
    - type: test
      format: file
      required: true
      content: regression test locking the fix (or documented reason no correct seam exists)
  evidence:
    - feedback loop ran and confirmed reproduction
    - fix applied and loop re-run confirms resolution
    - regression test passes
```


## Completion Report

Required on every execution. The node writes this in its primary artifact. The ledger records durable facts separately; it does not parse this section as the context chain.

```yaml
completion_report:
  what_was_done: string
  key_decisions:
    - decision: string
      rationale: string
  handoff_focus:
    - string
  open_questions:
    - string
  known_constraints:
    - string
  confidence_differential: 0.0-1.0
  dissent_if_alone: null | string
  iteration_context: string | null
```

## Context Compression Report

Required as a separate YAML artifact before this node can be marked completed or hand off downstream. The producer node decides the semantic compression, but must follow the fixed schema in `org/HARNESS.md`; `tools/policy.py` validates required fields and `tools/ledger.py` converts the report into the handoff `context_block`.

```yaml
context_compression_report:
  input_scope:
    artifacts_read: []
    handoffs_read: []
  retained_context:
    decisions: []
    constraints: []
    assumptions: []
    open_questions: []
  omitted_context: []
  compression_rationale:
    method: string
    loss_notes: []
  quality_checks:
    - name: string
      passed: true
```

## Interaction

```yaml
interaction:
  mode: iterative
  max_iterations: 10
  handoff_to:
    - code-reviewer
    - improve-codebase-architecture  # if root cause reveals architectural issue
```

## Termination

```yaml
termination:
  done_when:
    - root cause identified and documented
    - fix applied
    - regression test in place or absence documented
    - original repro no longer triggers
  blocked_when:
    - cannot build any feedback loop
    - bug requires environment not available in this context
```
