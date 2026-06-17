# Evaluator — Execution Meta-Analysis Protocol

Optional trace evaluation protocol. It is not currently fired automatically by
`tools/ledger.py`, `tools/scheduler.py`, or the Runtime protocol in
`org/RUNTIME.md`.

Use this document only when a human or future evaluator explicitly asks for a
post-task execution review. The evaluator is not a graph node and must not be
treated as an activation candidate.

---

## Trigger Condition

```yaml
# Decoder must have completed and written manifest.yaml with outcome
manifest.outcome.status: success | partial | failed
```

If `manifest.outcome` is missing, evaluation blocks. Decoder first, optional
trace evaluation second.

---

## Step 1 — Collect Execution Data

Read the entire task trace from `traces/<task_id>/`:

```yaml
sources:
  - manifest.yaml          # entry_nodes, terminal_nodes, outcome, artifact_index
  - state.yaml             # node_states, loop_states, join_gates, convergence
  - events.yaml            # full event stream
  - artifacts/*.provenance.yaml  # all provenance sidecars
  - ontology/relations.yaml      # the organization graph (read-only, for comparison)
```

Extract:

```yaml
activation_record:
  total_nodes_in_graph: <derived from ontology/nodes.yaml at evaluation time>
  nodes_activated: [role, ...]        # completed + partial
  nodes_skipped: [role, ...]          # in graph but never activated
  nodes_blocked: [role, ...]          # blocked at join gate
  nodes_failed: [role, ...]           # exhausted or failed
  
  # For each activated node:
  per_node:
    - role: string
      status: completed | partial | blocked | failed
      iterations: integer
      input_sources: [string]         # which nodes provided input
      output_artifacts: [string]      # artifact_ids produced
      handoff_to: [string]            # which nodes it triggered

propagation_record:
  edges_fired:                        # relations that triggered a downstream node
    - from: string
      to: string
      type: triggers | may_trigger
      probability_at_time: float
      condition: string | null
  edges_skipped:                      # relations that COULD have fired but didn't
    - from: string
      to: string
      type: triggers | may_trigger
      probability_at_time: float
      skip_reason: string             # e.g. "condition not met", "overridden by Runtime"
  edges_overridden:                   # relations where Runtime made a judgment call
    - from: string
      to: string
      type: triggers | may_trigger
      probability_at_time: float
      graph_signal: fire | skip       # what the graph said
      runtime_decision: fire | skip   # what Runtime did
      justification: string

runtime_overrides:
  # Every time Runtime deviated from a pure graph signal
  - context: string                   # what situation
    graph_expected: string            # what the weights said
    runtime_did: string               # what Runtime actually did
    justification: string
    was_correct: true | false | unknown  # assessed retrospectively

quality_record:
  review_nodes_activated: [string]    # evaluator/evaluates nodes
  review_verdicts:                    # APPROVED | CHANGES_REQUIRED | BLOCKED
    - artifact_id: string
      reviewer: string
      verdict: string
  loop_iterations_total: integer      # sum of all loop iterations
  max_loop_depth: integer
  defect_escape: unknown              # can't know yet — needs human or downstream signal

convergence_record:
  total_iterations: integer           # total node activations (including loops)
  max_node_depth: integer             # longest activation chain
  waves: integer                      # parallel activation waves
  total_duration_seconds: float       # timestamp_end - timestamp_start
  any_blocked_nodes: boolean
  any_exhausted_loops: boolean
  settled_cleanly: boolean            # convergence reached without escalation
```

---

## Step 2 — Score the Execution

```yaml
execution_score:
  # Each dimension: 0.0 (worst) to 1.0 (best)
  
  graph_fidelity:
    # How closely did Runtime follow the graph signals?
    # 1.0 = every edge respected. 0.0 = Runtime ignored all edges.
    value: float
    formula: |
      N_followed = count(edges where runtime_decision == graph_signal)
      N_total = N_followed + count(edges_overridden)
      graph_fidelity = N_followed / N_total
      (edges_skipped by condition are NOT counted — they count as "followed")
  
  propagation_completeness:
    # Did all triggered nodes actually complete?
    # 1.0 = all triggered nodes completed. 0.0 = none did.
    value: float
    formula: |
      N_completed = count(node_states where status == completed)
      N_activated = N_completed + N_blocked + N_failed
      propagation_completeness = N_completed / N_activated
  
  convergence_efficiency:
    # How efficiently did the task converge?
    # Penalized by: loops, blocked nodes, deep chains
    # 1.0 = first-wave completion, no loops, no blocks.
    value: float
    formula: |
      loop_penalty = min(1.0, loop_iterations_total * 0.15)
      block_penalty = 1.0 if any_blocked else 0.0
      depth_penalty = max(0, (max_node_depth - 3) * 0.1)
      convergence_efficiency = max(0, 1.0 - loop_penalty - block_penalty * 0.3 - depth_penalty)
  
  quality_confidence:
    # How confident are we that the output is correct?
    # Derived from review verdicts and quality signals.
    value: float
    formula: |
      if manifest.outcome.quality_signal.source != null:
        quality_confidence = manifest.outcome.quality_signal.value
      else if code-reviewer activated and verdict == APPROVED:
        quality_confidence = 0.85
      else if code-reviewer activated and verdict == CHANGES_REQUIRED:
        quality_confidence = 0.40
      else:
        quality_confidence = 0.50  # unknown
  
  overall:
    # Weighted composite
    value: float
    formula: |
      overall = graph_fidelity * 0.25
              + propagation_completeness * 0.25
              + convergence_efficiency * 0.20
              + quality_confidence * 0.30
```

---

## Step 3 — Produce Structured Evaluation

Write `traces/<task_id>/evaluation.yaml`:

```yaml
task_id: <TASK_ID>
evaluated_at: <now ISO8601>

# ── Activation Analysis ──────────────────────────
activation:
  nodes_activated: {count, list}
  nodes_skipped: {count, list}
  entry_node_selection:
    rules_applied: [string]           # which ENCODER rules matched
    assessment: correct | questionable | incorrect
    notes: string

  # For EACH skipped node, explain why
  skip_justifications:
    - role: string
      reason: string                  # e.g. "condition not met", "not relevant for task type"
      graph_signal_ignored: true | false
      assessment: justified | questionable | missed

# ── Propagation Analysis ─────────────────────────
propagation:
  edges_fired_count: integer
  edges_skipped_count: integer
  edges_overridden_count: integer
  
  propagation_path:                   # ordered by activation time
    - wave: integer
      nodes: [string]
      parallel: boolean

  # For EACH override, explain the judgment call
  overrides:
    - edge: "from→to/type"
      graph_said: fire | skip
      runtime_did: fire | skip
      rationale: string
      retrospective: correct | incorrect | needs_review

# ── Quality Analysis ────────────────────────────
quality:
  review_verdict: APPROVED | CHANGES_REQUIRED | BLOCKED | NONE
  issues_found: integer
  correctness_issues: integer
  maintainability_notes: integer
  spec_coverage_pct: float
  
  # What feedback loops would have helped?
  missed_evaluations:
    - evaluator_role: string          # e.g. grill-me, caveman
      target_artifact: string
      would_have: string              # what it might have caught

# ── Convergence Analysis ─────────────────────────
convergence:
  total_duration_seconds: float
  waves_required: integer
  max_chain_depth: integer
  loop_iterations: integer
  any_divergence: boolean
  settled_cleanly: boolean
  
  bottlenecks:
    - node: string
      waited_for: [string]
      duration_blocked_seconds: float | null

# ── Scores ──────────────────────────────────────
scores:
  graph_fidelity: {value, detail}
  propagation_completeness: {value, detail}
  convergence_efficiency: {value, detail}
  quality_confidence: {value, detail}
  overall: {value, breakdown}

# ── Recommendations ─────────────────────────────
recommendations:
  # What should be different next time?
  weight_adjustments:
    - relation: "from→to/type"
      dimension: string
      current_value: float
      suggested_value: float
      delta: float
      confidence: low | medium | high
      reason: string
  
  graph_changes:
    # Suggestions for new edges, removed edges, or weight changes
    - change: add_edge | remove_edge | adjust_weight
      detail: string
      reason: string
  
  protocol_improvements:
    - suggestion: string
      priority: high | medium | low
```

---

## Step 4 — Compare Against Weight Learning Indices

The current implemented learning path is:

```bash
python tools/ledger.py weights "$TASK_ID"
```

That command appends conservative role and relation signals to the cross-task
index files. This Evaluator protocol may read those indices and propose
changes, but it must not directly mutate `ontology/relations.yaml`.

### 4a. Index by Role

```yaml
# traces/index_by_role.yaml (append)
<role>:
  - task_id: <TASK_ID>
    timestamp: <evaluated_at>
    outcome: success | partial | failed
    iterations: integer
    quality_contribution: float       # how much this node contributed to overall quality
```

### 4b. Index by Relation

```yaml
# traces/index_by_relation.yaml (append)
<from>→<to>/<type>:
  - task_id: <TASK_ID>
    timestamp: <handoff timestamp>
    signal: +1.0 | -1.0 | 0.0        # acceptance / rejection / skip
    fidelity: followed | overridden
    detail: string
```

### 4c. Weight Update Proposals

For each relation that was activated in this task, use the proposal formulas
from `ontology/trace_schema.yaml`:

```yaml
# Proposed for ontology/relations.yaml; not applied automatically

# triggers.probability:
#   signal = 1.0 if trigger fired, 0.0 if node completed without firing
#   new_value = old_value * (1 - α) + signal * α
#   α = 0.05

# constrains.strength:
#   signal = 0.0 if target overrode constraint, 1.0 if constraint was followed
#   new_value = old_value * (1 - α) + signal * α

# All weights also update confidence:
#   confidence = min(1.0, samples / 100)
#   samples increment by 1 for each task that activates this relation
```

**IMPORTANT:** Weight updates are PROPOSED by the Evaluator, not applied automatically.
They are written to `traces/<task_id>/evaluation.yaml` under `recommendations.weight_adjustments`.
A human or a dedicated weight-update agent must review and apply them to `relations.yaml`.

---

## Step 5 — Deliver Evaluation to User

After writing the evaluation, the Runtime presents a concise summary to the user:

```
## Execution Evaluation — <task_id>

| Score | Value | Bar |
|-------|-------|-----|
| Graph Fidelity | 0.92 | ████████▊░ |
| Propagation | 1.00 | ██████████ |
| Convergence | 0.85 | ████████▌░ |
| Quality | 0.85 | ████████▌░ |
| **Overall** | **0.90** | █████████░ |

### Activated: 10 nodes in 3 waves over 420s
### Skipped: 3 nodes (triage, zoom-out, grill-with-docs — justified)
### Overrides: 2 (senior-engineer skip, zoom-out→architect block override)
### Code Review: APPROVED (0 correctness, 2 maintainability)

### Weight adjustments proposed:
  → to-issues→senior-engineer/probability: 0.85 → 0.81 (override)
  → architect→devops-engineer/strength: 0.60 → 0.57 (skipped)
```

---

## Runtime Status

```
Phase 0 — Encoder: Task Intake and Ledger Initialization
Phase 1 — Graph Propagation: Activate nodes, propagate signals
Phase 2 — Convergence Detection: Check settlement conditions
Phase 3 — Decoder: Synthesis and Delivery
```

There is no implemented Phase 4. A task is complete after Phase 3 when
`ledger deliver` has written `manifest.outcome` and `ledger weights` has updated
the learning indices. If an evaluation is requested, write
`traces/<task_id>/evaluation.yaml` as an additional audit artifact.
