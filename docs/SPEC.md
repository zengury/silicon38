# Silicon Org — Technical Specification

**Version**: 0.5.0-dev

---

## Overview

Silicon Org is a dynamic multi-agent software development organization encoded
as a weighted Graph. When you open a repository containing Silicon Org in a
coding agent, the main instance becomes the Runtime — an execution substrate
that drives 35 specialized agents through any engineering task, maintains a
full audit trail, and delivers production-ready output.

---

## 1. Architectural Principles

### 1.0 Five Core Concepts

Silicon Org deliberately keeps the control model small:

- **Graph** = static law. Nodes, edges, edge types, weights, and reachability.
  These files currently live under `ontology/`, but that directory is only the
  storage path for Graph data.
- **Ledger** = durable task facts. `manifest.yaml`, `state.yaml`,
  `events.yaml`, artifacts, provenance, and handoffs under `traces/<task_id>/`.
  `state.yaml` is part of the Ledger, not a separate runtime-state entity.
- **Policy** = legal interpreter. Given Graph + Ledger, it decides which actions
  are valid now: activate, skip, defer, reject, converge, deliver. The Policy
  kernel lives in `tools/policy.py`; the Ledger CLI calls it before writing
  state.
- **Runtime** = executor. It runs nodes, records decisions, follows Policy, and
  delivers only after convergence.
- **Learning** = feedback layer. It reads Ledger traces and updates role,
  relation, model-routing, and graph-evolution priors without weakening hard
  legality.

`org/CONTEXT_BLOCK.md` is the continuity anchor for these concepts. New task
manifests record its digest so long-running iteration does not lose the original
intent.

### 1.1 The Graph Is the Organization

Traditional software organizations have fixed roles and rigid reporting structures. Silicon Org has neither. The organization is a parameterized weighted graph:

- **Nodes** = agent roles (what kind of work gets done)
- **Edges** = typed relationships (how work flows between nodes)
- **Weights** = learned probabilities and quality signals

Every task assembles a different team by traversing different paths through the graph. Zero reorganization cost.

### 1.2 Encoder–Decoder Architecture

```
[ENCODER]   parse task type → select entry nodes → initialize ledger
[GRAPH]     propagate through layers → parallel where safe, sequential where required
[DECODER]   collect terminal artifacts → check consistency → assemble deliverable
```

### 1.3 Actor Model

Nodes are actors that self-navigate. At runtime, each node queries the Graph:
- `supports_me`: which nodes provide input I should wait for
- `i_trigger`: which nodes I activate on completion
- `evaluates_me`: which nodes will review my output

The Runtime executes, but the Graph is the routing table and Policy is the
legality check.

---

## 2. Node Architecture

### 2.1 Three-Layer Structure

```
Layer 1 — Intake & Understanding (7 nodes)
  Entry points. Classify, decompose, research before execution.

Layer 2 — Execution (20 nodes)
  Architecture, Engineering, Operations, Design & Experience, customer,
  and org-development roles.
  Produce primary deliverables.

Layer 3 — Quality & Output (8 nodes)
  Review, challenge, delivery proof, document, release, hand off,
  and organizational learning.
```

### 2.2 Required Completion Report

Every node, every execution:

```yaml
completion_report:
  what_was_done: string
  key_decisions:
    - decision: string
      rationale: string
  handoff_focus: [string]
  open_questions: [string]
  known_constraints: [string]
  iteration_context: string | null
```

---

## 3. Relation Types and Weighted Edges

### 3.1 Seven Relation Types

| Type | Semantics | Key Dimension |
|------|-----------|---------------|
| `triggers` | Completion creates an activation candidate | `probability` [0,1] |
| `may_trigger` | Conditional activation candidate | `probability` + `condition` |
| `constrains` | Reduces target's design space | `strength` [0,1] + `rigidity` |
| `evaluates` | Reviews target's output | `strictness` [0,1] + `blocking` |
| `supports` | Provides context/input | `necessity` [0,1] + `substitutability` |
| `complements` | Combined output > either alone | `synergy` + `overlap` |
| `augments` | Adds to target's output | `necessity` + `depth` |

### 3.2 Weight Learning

Weight update proposals use bounded EMA (α=0.05). The current Runtime writes
learning indices and review proposals with `ledger weights`; it does not mutate
`relations.yaml` automatically.

```
new_value = old_value × (1 − α) + signal × α
confidence = min(1.0, samples / 100)
```

### 3.3 Hub Nodes

- `senior-engineer` — degree 24
- `architect` — degree 22
- `code-reviewer` — degree 18

---

## 4. Runtime Protocol

### Phase 0 — Encoder
1. Parse task type
2. Select Layer 1 entry nodes only
3. Initialize ledger at `traces/<task_id>/`

### Phase 1 — Graph Propagation
1. Package inputs (harness + skill + supporting artifacts)
2. Invoke node via Agent tool
3. Receive output, write artifact + provenance sidecar
4. Register the node's Context Compression Report
5. Update ledger (state.yaml, events.yaml)
6. Query graph for next activations
7. Check join gates
8. Write handoff records before downstream activation
9. Handle evaluations (approve / reject / advisory)

Downstream nodes require a completed predecessor, a predecessor artifact, and a
handoff over an activation-capable Graph relation. The handoff must carry both
`deliverable` metadata and a digest-linked `context_block` that compresses the
producer's upstream context. That block is built from the producer's registered
`context_compression_report`; it is not free-written by Runtime. The Policy
kernel rejects Layer 2/3 entry nodes, orphan downstream activations, incomplete
handoffs, invalid context digests, malformed context compression reports,
context reports whose cited handoff digests do not match the real upstream
handoffs, and attempts to activate through context-only relations such as
`supports`. Policy also rejects node completion until both the node's primary
artifact and Context Compression Report are registered.

Activation is a decision, not an automatic command. `triggers` edges with
probability >= 0.50 and satisfied `may_trigger` edges become candidates that
must be activated, skipped, or deferred with a recorded reason. `evaluates`
edges are reverse activation candidates: once a producer completes, the
evaluator may be activated to review that artifact. `supports`, `constrains`,
`complements`, and `augments` provide context or ordering pressure;
they do not activate nodes by themselves.

Skip is not free. Required blocking evaluators cannot be skipped after their
producer completes. Repeated role skips record `skip_cost`; after repeated
skips the Ledger requires a more explicit justification and carries the cost
into task quality. Advisory skips remain possible, but they become learning
signals instead of disappearing as local judgement.

`ledger candidates <task_id>` lists undecided graph candidates. `ledger
validate <task_id>` fails while activation candidates are undecided.
`ledger deliver <task_id> success ...` also refuses to complete while any
activation candidate remains undecided, any artifact remains draft/under_review,
or any convergence gate is false.

### Phase 2 — Convergence Detection
```
all_non_loop_nodes_settled    every triggered node completed or skipped
all_loops_resolved             every loop converged or exhausted (max 3)
all_blocking_evals_resolved    no pending required evaluations
all_joins_passed               no blocked nodes
all_artifacts_resolved         no draft/under_review artifacts
no_undecided_activation_candidates
                               every graph candidate activated, skipped, or deferred
```

### Phase 3 — Decoder
1. Collect approved artifacts from terminal nodes
2. Check for semantic conflicts
3. Assemble coherent deliverable
4. Write manifest outcome with `ledger deliver`
5. Update weight indices
6. Deliver

### Phase 3.5 — Post-Delivery Learning
After `task_completed`, Policy allows post-delivery activation for `meta: true`
nodes. Automatic meta nodes (`hrbp`, `graph-topologist`) must still register
their artifacts and Context Compression Reports before completion. Their outputs
feed skill scoring and topology proposals; they do not bypass Ledger.

`ledger weights` also writes `traces/index_learning_proposals.yaml`. These
proposals are machine-readable review inputs for Policy/Runtime changes. After
human review, accepted proposals may activate temporary Policy overlays that
the Policy kernel reads during `activation-decision` and `deliver success`
checks. Learning writes both per-trace findings and cross-trace aggregate
pattern proposals. They are never auto-applied to `ontology/relations.yaml`.

---

## 5. Artifact Ledger

### Storage Layout

```
traces/<task_id>/
  manifest.yaml
  state.yaml
  events.yaml
  artifacts/<node>-<type>-v<n>.<ext>
  artifacts/<node>-<type>-v<n>.provenance.yaml
  handoffs/<from>→<to>-<timestamp>.yaml
  ../index_learning_proposals.yaml
```

Each handoff is a context-chain block:

```yaml
deliverable:
  producer: senior-engineer
  artifact_refs: [senior-engineer-code-v1]

context_block:
  schema: silicon_org.context_chain.v1
  source:
    producer_role: senior-engineer
    context_compression_report_ref: artifacts/senior-engineer-context-report-v1.yaml
    input_handoffs:
      - ref: handoffs/architect→senior-engineer-...
        context_digest: <sha256>
    input_artifacts:
      - artifact_id: architect-analysis-v1
        used: true
        why: "Defines implementation constraints."
  compressed_context:
    decisions: []
    constraints: []
    assumptions: []
    open_questions: []
  omitted_context: []
  compression_rationale:
    method: "retain context that changes downstream action"
    loss_notes: []
  quality_checks:
    - name: "All retained claims cite a source."
      passed: true
  producer_output_artifact_refs: [senior-engineer-code-v1]
  inherited_artifact_refs: [architect-analysis-v1, api-designer-contract-v1]
  previous_blocks:
    - ref: handoffs/architect→senior-engineer-...
      context_digest: <sha256>
  context_digest: <sha256>
```

The receiver gets the direct artifact plus the compressed chain of context that
led to it. This is intentionally block-like: every handoff summarizes prior
handoffs and links to their digests instead of flattening the whole trace.

### Context Compression Report

Every producer node writes a YAML report before it can hand off:

```yaml
context_compression_report:
  input_scope:
    artifacts_read:
      - artifact_id: architect-analysis-v1
        used: true
        why: "Set module ownership and constraints."
    handoffs_read:
      - ref: handoffs/zoom-out→architect-...
        context_digest: <sha256>

  retained_context:
    decisions:
      - statement: "Policy is separated from Ledger writes."
        source: architect-analysis-v1
        impact: "Implementation must put legality checks in tools/policy.py."
    constraints:
      - statement: "Downstream handoff requires deliverable and context_block."
        source: org/RUNTIME.md
        impact: "Activation guard must reject incomplete handoffs."
    assumptions:
      - statement: "Ledger CLI remains the only write surface."
        source: org/CONTEXT_BLOCK.md
        risk: "Future direct writers must call Policy too."
    open_questions:
      - statement: "Should context quality become a blocking evaluator?"
        source: user task
        owner: runtime

  omitted_context:
    - source: README.md
      reason: background_only

  compression_rationale:
    method: "retain decisions, constraints, assumptions, and open questions that changed the output"
    loss_notes: ["Narrative explanation was omitted because artifact refs preserve it."]

  quality_checks:
    - name: "All retained claims cite a source."
      passed: true
    - name: "All upstream artifacts are marked used or omitted."
      passed: true
    - name: "Hard constraints and open questions are preserved."
      passed: true
```

The LLM performs the compression, but the schema and quality bar are fixed by
Policy and Harness. This keeps compression useful without letting every node
invent its own summary style.

### Artifact ID Convention

```
<role>-<type>-v<iteration>
  senior-engineer-code-v1
  code-reviewer-review-v2
  architect-analysis-v1
```

---

## 6. Extension Protocol

1. Add or select a backing skill for the role
2. Write a harness in `org/registry/<role>.md` (follow `org/HARNESS.md`)
3. Add a Graph node to `ontology/nodes.yaml`
4. Add Graph edges to `ontology/relations.yaml`
5. Update `org/REGISTRY.md`

Rules: new roles are additive unless an ADR justifies a graph correction; every
node must reference a backing skill; every node must be reachable from Layer 1.
