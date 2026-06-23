# Runtime — Operating Protocol

The Runtime is the main coding agent instance executing a task.
It is not an agent. It is the execution substrate: it drives the graph,
manages the ledger, and delivers the final output.

**Tooling**: All ledger operations use `python tools/ledger.py <command>`.
Policy legality lives in `tools/policy.py`; `tools/ledger.py` calls it before
writing state.
All subagent prompt assembly uses `python tools/spawn.py preview <role> <task_id> <desc>`.
Read `org/CONTEXT_BLOCK.md` before changing runtime, graph, policy, ledger, or
learning behavior.

**Concept boundary**:
- Graph = static law: nodes, edges, edge types, weights. These files currently
  live under `ontology/`.
- Ledger = task facts: `manifest.yaml`, `state.yaml`, `events.yaml`,
  artifacts, provenance, and handoffs under `traces/<task_id>/`.
- Policy = legality interpreter over Graph + Ledger. These gates live in
  `tools/policy.py`, with scheduling advice in `tools/scheduler.py`.
- Runtime = executor. It may judge and choose among legal options, but it must
  not treat its private reasoning as fact until it writes the Ledger.
- Learning = feedback layer over traces. It updates priors conservatively from
  structured signals; it does not override hard legality.

**LangGraph-native execution boundary**: LangGraph OSS core is the target
execution kernel, not an adapter around a legacy loop. Silicon Org remains the
organization brain: Graph legality, multi-dimensional relation weights, Ledger
truth, Policy predicates, Context Blocks, and Learning updates stay here.
LangGraph executes Policy decisions durably through checkpoints, interrupts,
parallel `Send(...)` fan-out, and resume. It must never replace Silicon Graph
with static workflow edges.

---

## Phase 0 — Encoder: Task Intake and Ledger Initialization

**Step 0.1 — Understand the task**

Read the task. Before activating anything, identify:
- Task type: `bug_fix | feature | refactor | architecture | design | ops | docs | ambiguous`
- Deliverable: what must exist when the task is done
- Constraints: what cannot change, what must be preserved
- Done condition: how you will know the task is complete

If any of these is unclear, activate `triage` as the first node.

**Step 0.2 — Initialize the ledger**

```bash
TASK_ID="task-$(date +%Y%m%dT%H%M%S)-$(head -c4 /dev/urandom | xxd -p)"
python tools/ledger.py init "$TASK_ID" "<task_type>" "<one sentence summary>"
```

This creates `traces/$TASK_ID/` with `manifest.yaml`, `state.yaml`, `events.yaml`,
and `artifacts/` + `handoffs/` directories — all pre-populated with correct schemas.
The manifest records the `org/CONTEXT_BLOCK.md` digest so future runs can recover
the design intent that governed the task.

Inspect the active continuity anchor when needed:
```bash
python tools/ledger.py context
```

**Step 0.3 — Select entry nodes**

Read `org/ENCODER.md` for the task-type to entry-node mapping.
Entry nodes MUST be Layer 1 nodes. Do not activate Layer 2 or Layer 3 nodes
in Phase 0, even when the final deliverable obviously needs them.
For each entry node, register it:
```bash
python tools/ledger.py node "$TASK_ID" <role> activated --set-entry
```

**Step 0.4 — Load soul for design-bearing tasks**

If the task type is `design`, `feature` (with UI/UX), or `architecture`,
read `org/soul.md` before graph propagation and check `ontology/nodes.yaml`
for `carries_soul: true` on each node the task may touch. Entry nodes do not
need to carry soul; soul-bearing nodes are often downstream. When writing a
handoff to any soul-bearing node, Ledger includes a `soul_ref: org/soul.md`
field and Policy rejects the handoff if it is missing. The receiving node reads
the full file before producing its artifact. Never extract snippets; the file
must be read whole so future soul.md iterations propagate automatically.

---

## Phase 1 — Graph Propagation

This is the execution loop. Repeat until convergence (Phase 2).

### Activating a Node

For non-entry activations, the ledger requires:
- a completed predecessor node
- at least one registered artifact from that predecessor
- an activation-capable handoff:
  - `triggers` or satisfied `may_trigger` in the graph direction
  - `evaluates` in reverse handoff direction, from completed producer to evaluator

If any of these is missing, `tools/ledger.py node ... activated` rejects the
activation. This keeps downstream selection dynamic and artifact-driven.
`supports`, `constrains`, `complements`, and `augments` may carry
context, but they cannot activate a node by themselves.

**Step 1.1 — Package node inputs**

Read the node's harness (`org/registry/<role>.md`) and skill.
Build the invocation prompt:
```bash
python tools/spawn.py preview <role> "$TASK_ID" "<task description>"
```

The preview prints the resolved model source and recommended model profile.
Concrete model IDs are optional user configuration, not graph policy. If the
user has not configured `org/models.local.yaml`, run the node on the Runtime's
current/default model and use `org/MODELS.md` only as capability guidance.

When useful, ask the user whether they want to configure model overrides before
a long or expensive run. If they do not configure anything, proceed with the
Runtime default.

Register the activation:
```bash
python tools/ledger.py node "$TASK_ID" <role> activated
```

**Step 1.2 — Run the node**

Execute the node's work (reading harness + skill as context, producing the artifact).
Nodes with no dependency between them may be activated in parallel.

**Step 1.3 — Register output**

```bash
# Save artifact
echo "<output>" > traces/$TASK_ID/artifacts/<role>-<type>-v1.md

# Register in ledger (auto-creates provenance sidecar)
python tools/ledger.py artifact "$TASK_ID" <role> <type> "artifacts/<role>-<type>-v1.md"

# Register the node's Context Compression Report before any downstream handoff.
# The report is produced by the node, but schema-validated by Policy.
python tools/ledger.py context-report "$TASK_ID" <role> "artifacts/<role>-context-report-v1.yaml"

# Mark completed
python tools/ledger.py node "$TASK_ID" <role> completed
```

Completion is blocked until both the primary artifact and the Context
Compression Report are registered. Terminal nodes still produce a report; it is
part of the node output contract, not only a handoff convenience.

### Determining Next Activations

**Step 1 — Ask the scheduler.** Before reading `relations.yaml` by hand,
run the scheduler to get a categorized proposal:

```bash
python tools/scheduler.py propose "$TASK_ID"
```

This returns three lists (proposed_activations / deferred / proposed_skips)
plus any required gates still open. The scheduler is a **soft advisor** —
Runtime keeps final say — but every override must be recorded.

**Step 2 — Apply graph semantics yourself when needed.** The raw edges in
`ontology/relations.yaml` from `from: <completed_role>`:

- `triggers (probability ≥ 0.50)`: create an activation candidate; activate,
  skip, or defer with a recorded reason
- `may_trigger`: evaluate the condition; activate, skip, or defer with a
  recorded reason
- incoming `evaluates` edges where `to: <completed_role>`: create an evaluator
  candidate, with handoff from producer to evaluator

Inspect undecided candidates directly when the scheduler output is unclear:
```bash
python tools/ledger.py candidates "$TASK_ID"
```

**Step 3 — Record every decision.** A candidate that won't be activated
must produce a ledger event, NOT silence:

```bash
# Defer or override: writes activation_decision event
python tools/ledger.py activation-decision "$TASK_ID" <from> <to> <rel_type> defer "<reason>"

# Definitively skip a node (not just one edge to it): writes node_skipped event
python tools/ledger.py skip "$TASK_ID" <role> "<reason>"
```

Skipping a node when its edges still have undecided candidates is allowed
but must be done through `skip`, never by silence. Required blocking evaluators
cannot be skipped after their producer has completed. Repeated skips carry a
`skip_cost`; after repeated skips the Ledger requires a detailed justification
and the cost lowers the task quality signal.

Before registering any downstream activation, write the handoff:
```bash
python tools/ledger.py handoff "$TASK_ID" <from> <to> <relation_type> "<focus>"
```

Every handoff MUST contain three payloads:
- `deliverable`: the producer's artifact refs and compact metadata.
- `context_block`: a compressed digest-linked summary of the upstream context
  the producer used. This block preserves the chain of prior handoffs without
  forcing downstream nodes to re-read every previous artifact.
- `soul_ref` (if target node has `carries_soul: true`): a reference to
  `org/soul.md`. The receiving node reads the full file before producing its
  artifact. Never include snippets — the file is read whole so future
  soul.md iterations propagate without manual updates to every handoff.

The `context_block` is built from the producer's registered
`context_compression_report`; Runtime does not free-write it. If the report is
missing or malformed, `ledger handoff` fails.

Then activate the target:
```bash
python tools/ledger.py node "$TASK_ID" <to> activated
```

### Evaluation Loops

If evaluator returns `CHANGES_REQUIRED` with `blocking=required`:
- Re-activate producer (max 3 iterations)
- After max: select best artifact, mark exhausted

---

## Phase 2 — Convergence Detection

After every node completion:
```bash
python tools/ledger.py converge "$TASK_ID"
```

Convergence requires all active nodes to be settled, loops and joins to be
resolved, blocking evaluations to be clear, artifacts to be approved or
otherwise resolved, and every activation candidate to have an explicit
activate / skip / defer decision.

- `CONVERGED` → proceed to Phase 3
- `NOT CONVERGED` → continue propagation

---

## Phase 3 — Decoder: Synthesis and Delivery

See `org/DECODER.md` for full protocol.

1. Collect terminal artifacts (status = approved)
2. Check for conflicts
3. Assemble coherent deliverable
4. Write outcome and update weights:
```bash
python tools/ledger.py deliver "$TASK_ID" success "<summary>"
python tools/ledger.py weights "$TASK_ID"
```
5. Review any new entries in `traces/index_learning_proposals.yaml`
6. Deliver to user

### Phase 3.5 — Post-Delivery Meta Nodes

After every task delivery (any outcome: success, partial, failed, abandoned),
the Runtime activates two automatic meta nodes in parallel to close the
learning loop. These are post-delivery meta activations: Policy allows them
only after `task_completed`, and they do not require graph handoffs.

#### 3.5a — HRBP (Talent Evaluation)

```bash
python tools/ledger.py node "$TASK_ID" hrbp activated
```

The HRBP evaluates the talent (skill performance) demonstrated in the
just-completed task. It reads traces, scores each activated skill on quality
and efficiency, and updates the skill's quality_score in the candidate pool.
This is per-task talent evaluation — not a replacement decision, but continuous
performance data that feeds future replacement decisions.

Register the evaluation:
```bash
python tools/ledger.py artifact "$TASK_ID" hrbp evaluation "artifacts/hrbp-evaluation-v1.md"
python tools/ledger.py context-report "$TASK_ID" hrbp "artifacts/hrbp-context-report-v1.yaml"
python tools/ledger.py node "$TASK_ID" hrbp completed
```

#### 3.5b — Graph Topologist (Organizational Learning)

```bash
python tools/ledger.py node "$TASK_ID" graph-topologist activated
```

The graph-topologist reads the full trace and produces a structured retrospective
covering what worked, what broke, structural observations, and proposed changes.
See `org/registry/graph-topologist.md` for the full output format.

```bash
python tools/ledger.py artifact "$TASK_ID" graph-topologist retrospective "artifacts/graph-topologist-retrospective-v1.md"
python tools/ledger.py context-report "$TASK_ID" graph-topologist "artifacts/graph-topologist-context-report-v1.yaml"
python tools/ledger.py node "$TASK_ID" graph-topologist completed
```

Both meta nodes run in parallel after delivery. Their outputs feed the
Learning layer (HRBP updates skill scores; graph-topologist proposes
structural changes).

---

## Error Handling

- **Node blocked**: Report what it waits for. Do not continue on assumption.
- **Node failed**: Re-invoke once. Second fail → escalate.
- **Loop diverging**: Stop. Report. Do not continue looping.
- **Conflicting artifacts**: Document both, ask user to decide.

### Runtime Fallback Discipline

Runtime is the execution substrate, not an implementer. When a subagent
cannot run (session quota exhausted, two consecutive failures, graph
topology has no activation-capable edge):

1. **Do NOT silently write the artifact yourself.**
2. Register the situation with the ledger:
   ```bash
   python tools/ledger.py runtime-fallback "$TASK_ID" <role> "<reason>"
   ```
   Acceptable reasons describe the cause: `subagent_quota_exhausted`,
   `subagent_failed_twice`, `graph_topology_dead_end`, `explicit_user_override`.
3. **Ask the user before proceeding.** Use AskUserQuestion to surface
   the choice (wait / retry / explicit Runtime-implementation /
   user-authored fallback). Do not auto-implement.

Trace truthfulness is non-negotiable. A `runtime_fallback` event in the
ledger is honest; a silently-Runtime-authored artifact looks like a
phantom subagent and corrupts the audit trail.

## Parallel Execution

Activate in parallel when no dependency edges between nodes.
Sequential when Node B has dependency on Node A's output.
