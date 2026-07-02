# Agent Harness Specification

Every agent in this organization is defined by this schema. A skill describes *how* to think. A harness describes *what it means to operate as an agent*: what it can touch, what it must produce, how it communicates, and when it is done.

No agent may deviate from this contract. The harness is the substrate that makes dynamic assembly possible.

---

## Schema

### 1. Identity

```yaml
role: <unique-identifier>
title: <Human Title>
domain: <area>
trigger:
  - <condition>
skill_ref: <path-or-null>
```

### 2. Tool Permissions

```yaml
tools:
  read_files: true|false
  write_files: true|false
  run_bash: true|false
  web_search: true|false
```

Tool permissions are scoped to file and shell capabilities only. Subagent
spawning and external service access (GitHub, model providers, etc.) belong to
the Runtime and runner adapters, not to individual nodes. A node never invokes
another node directly — that violates the activation discipline in
`org/RUNTIME.md` and `org/CONTEXT_BLOCK.md`.

### 3. Input Contract

```yaml
input:
  required:
    - task_description
    - codebase_context
  optional:
    - prior_agent_outputs
    - constraints
    - quality_bar
```

### 4. Output Contract

Every agent must produce structured output.

```yaml
output:
  deliverables:
    - type: code | test | document | analysis | decision | schema
      format: file | inline-markdown | structured-json
      required: true|false
  evidence:
    - <evidence-type>
```

**Completion Report — required from every node, every execution.**

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
  # Internal state signals — guard against group-induced drift (dissociation
  # index, DI).
  confidence_differential: 0.0-1.0   # this node's confidence in its output vs.
                                      # what it would believe if it had faced the
                                      # same problem alone. 0.0 = identical to
                                      # solo judgment; 1.0 = fully overridden by
                                      # the group's expectation.
  dissent_if_alone: null | string    # what would this node have decided
                                      # differently if it had been the only one
                                      # facing the task? null = no dissent;
                                      # string = the specific divergence.
```

If in a revision loop:
```yaml
completion_report:
  ...
  iteration_context: string
```

### 5. Quality Criteria

```yaml
quality_criteria:
  - <specific, falsifiable criterion>
```

### 6. Interaction Mode

```yaml
interaction:
  mode: single-shot | iterative | collaborative
  max_iterations: <n>|unlimited
  handoff_to:
    - <role>
```

### 7. Termination

```yaml
termination:
  done_when:
    - <explicit condition>
  blocked_when:
    - <blocker condition>
```

### 8. Failure Protocol

```yaml
failure:
  report:
    - what_was_attempted
    - what_specific_obstacle_was_hit
    - what_would_unblock_this
  never:
    # Reason-based alignment: bare imperatives raise the dissociation index;
    # constraints with stated reasons lower it. Each rule below carries the
    # downstream cost it prevents, so the node understands why, not only what.
    - proceed_on_assumption       # An unverified upstream assumption contaminates
                                   #   the entire provenance chain. Every dependent
                                   #   artifact then builds on a false premise.
    - fabricate_evidence          # Fabricated evidence breaks the provenance
                                   #   chain. Downstream correctness cannot be
                                   #   audited because the cited source is fake.
    - deliver_incomplete_output   # Incomplete delivery manufactures a usable
                                   #   hallucination. Downstream nodes then make
                                   #   "correct-looking" decisions on a faulty
                                   #   base — more dangerous than explicit failure.
    # Structural dissenter protection: if the node believes the rule above
    # should be violated in the current context, it must record the reasoning
    # in completion_report.dissent_if_alone rather than silently ignoring.
```

---

## System-Level Quality Protocol

Quality is not a role. It is a protocol embedded at every handoff.

Every downstream handoff has two required payloads:

1. `deliverable`: the direct artifact refs produced by the sending node.
2. `context_block`: a compressed digest-linked summary of upstream handoffs and
   artifact refs used by the sender.

Every node that may hand off downstream must also produce a structured
Context Compression Report. The LLM decides what to retain, but the method,
fields, and quality checks are fixed by this schema.

```yaml
context_compression_report:
  input_scope:
    artifacts_read:
      - artifact_id: string
        used: true|false
        why: string
    handoffs_read:
      - ref: string
        context_digest: string

  retained_context:
    decisions:
      - statement: string
        source: string
        impact: string
    constraints:
      - statement: string
        source: string
        impact: string
    assumptions:
      - statement: string
        source: string
        risk: string
    open_questions:
      - statement: string
        source: string
        owner: string|null

  omitted_context:
    - source: string
      reason: irrelevant | superseded | contradicted | background_only | duplicate

  compression_rationale:
    method: string
    loss_notes: [string]

  quality_checks:
    - name: string
      passed: true
```

Compression standard:
- Retain only context that changes downstream action.
- Never omit hard constraints, blocking review findings, security/data/auth
  constraints, unresolved open questions, interface/schema assumptions, or
  deployment/test implications.
- Every retained claim must cite a source artifact, handoff, document, or
  explicit user instruction.
- Every read artifact is either `used: true` or appears with `used: false` and
  a reason.

### Before any output leaves an agent:

1. **Evidence check**: Every claim has a backing artifact.
2. **Scope check**: Output addresses the input contract.
3. **Contradiction check**: Output does not contradict constraints or prior outputs.

### At integration (Runtime level):

1. **Coherence check**: Combined outputs form a consistent whole.
2. **Gap check**: No required deliverable is missing.
3. **Quality floor**: Any output below criteria is rejected and the agent re-invoked.

### The standard is not "complete." The standard is "would a master in this domain be satisfied."
