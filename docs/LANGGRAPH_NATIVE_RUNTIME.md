# LangGraph-Native Runtime

This document describes the target runtime contract and the first executable
native kernel. The current release compiles and runs the LangGraph control
plane, validates all 41 harness profiles, preserves Silicon weighted graph
propagation, executes Ledger-backed role transactions, and runs the mandatory
post-delivery learning path. Real semantic subagent execution is still behind
the pluggable `NodeRunner` boundary.

Silicon Org must use LangGraph in its terminal form, not as an adapter around a
legacy loop. LangGraph is the execution kernel. Silicon Org remains the
organization brain.

```text
Silicon Graph  -> weighted organizational law
Silicon Policy -> dynamic propagation judge
LangGraph      -> durable execution kernel
Ledger         -> transactional fact store
Learning       -> post-run topology/model/weight improvement
```

## Non-Negotiables

1. All ontology nodes are mapped into the LangGraph-native runtime.
2. No reduced "small loop" is allowed to stand in for the organization.
3. Relation weights remain in Silicon Graph and are read by Silicon Policy.
4. LangGraph static edges do not replace Silicon relation edges.
5. Gates are Policy predicates, not peer organization nodes.
6. Every node keeps independent model-routing capability.
7. Graph Topologist and Learning are mandatory post-delivery runtime stages.
8. Only local MIT-licensed LangGraph OSS runtime packages are allowed.
9. Hosted/commercial services are forbidden for runtime execution.

## OSS-Only Boundary

Install local OSS runtime support with:

```bash
python3 -m pip install -e '.[langgraph-oss]'
```

The runtime may import local MIT-licensed `langgraph` packages, but must not
connect to:

- LangGraph Platform
- LangSmith hosted tracing
- LangChain hosted tracing
- remote LangGraph API execution

`runtime/langgraph_native.py` fails closed if hosted-service environment
variables are present, including `LANGSMITH_API_KEY`,
`LANGCHAIN_TRACING_V2`, or `LANGGRAPH_API_KEY`.

The local packages installed by `requirements-langgraph-oss.txt` must remain
MIT-licensed OSS packages. The runtime may tolerate transitive client packages
installed by LangGraph, but Silicon Org code must not call hosted tracing,
hosted deployment, or remote graph execution APIs.

`pyproject.toml` is the authoritative project dependency manifest. The
`requirements-langgraph-oss.txt` file is kept as a pinned, explicit install
shortcut for environments that do not use editable installs.

## Release Smoke

Run the native runtime smoke test before release:

```bash
python3 tools/langgraph_native_smoke.py
```

Expected properties:

- `ontology_nodes == 41`
- `harness_profiles == 41`
- `mapping_issues == []`
- `triage_candidate_count > 0`
- post-delivery `graph-topologist` and `learning-engine` complete
- Ledger-backed execution runs a weighted two-node path (`triage -> diagnose`)
  through artifact registration, Context Compression Reports, activation
  decisions, and a real handoff
- `graph-topologist` writes a trace artifact after partial delivery
- `learning-engine` writes trace-local `learning.yaml` with signals and
  conservative proposals
- prompt-package execution writes a complete node invocation package for an
  external semantic executor
- external-command execution calls a local executor through the same package and
  returns artifact + Context Compression Report to Ledger
- `configured_service_vars == []`

Negative OSS-only check:

```bash
LANGSMITH_API_KEY=x python3 - <<'PY'
from runtime.langgraph_native import compile_native_runtime
compile_native_runtime()
PY
```

This must fail with `NonOssRuntimeConfigured`.

## Run A Local Task

Use `tools/langgraph_run.py` as the local long-lived entrypoint. It starts the
LangGraph-native runtime, writes Ledger facts under `traces/<task_id>/`, invokes
the selected node runner, delivers the trace, then runs Graph Topologist and
Learning. The default runner is `semantic_command`, which calls
`tools/semantic_node_executor.py` and executes each node with the same local
semantic agent CLI. The default local agent is `pi`; `codex` and `claude` are
also supported when their local CLI auth/model setup is healthy.

```bash
python3 tools/langgraph_run.py \
  --task-id task-local-demo \
  --task-type runtime_release_validation \
  --description "Validate native LangGraph task execution." \
  --max-role-executions 2 \
  --max-parallel-dispatch 1 \
  --replace
```

The command prints a JSON summary with completed roles, artifact count, handoff
count, activation decisions, manifest outcome, and file refs.

Select the local agent with:

```bash
SILICON_ORG_NODE_AGENT=pi python3 tools/langgraph_run.py --description "..."
SILICON_ORG_NODE_AGENT=codex python3 tools/langgraph_run.py --description "..."
SILICON_ORG_NODE_AGENT=claude python3 tools/langgraph_run.py --description "..."
```

`semantic_command` passes every node's invocation package, harness, model
selection, upstream handoffs, and upstream artifacts to the selected agent and
requires JSON with `artifact_body` and a Context Compression Report. This is the
business execution path. By default every node uses the same runtime/default
model. Per-role model overrides remain available through `org/models.local.yaml`
for the later multi-model version.

For deterministic CI/runtime plumbing validation, use `external_command` with
the local contract validator:

```bash
python3 tools/langgraph_run.py \
  --task-id task-contract-demo \
  --description "Validate runner contract." \
  --runner-mode external_command \
  --external-runner-command "python3 tools/local_node_executor.py" \
  --max-role-executions 2 \
  --replace
```

For a package-only run that prepares prompts for another executor:

```bash
python3 tools/langgraph_run.py \
  --task-id task-prompt-package-demo \
  --description "Prepare node invocation package." \
  --runner-mode prompt_package \
  --max-role-executions 1 \
  --replace
```

For custom production executors, replace `tools/semantic_node_executor.py` with
a command that consumes `SILICON_ORG_INVOCATION_JSON` and
`SILICON_ORG_INVOCATION_PROMPT`, honors the harness tool/write constraints, and
returns JSON with `artifact_body`, optional `artifact_type`, and
`context_report`.

## Runtime Topology

LangGraph topology is deliberately small:

```text
START
  -> encoder
  -> policy_router
  -> run_role_node       # dynamic Send(role=...)
  -> policy_router       # repeat until convergence
  -> convergence_policy  # policy predicate, not org node
  -> graph_topologist_node
  -> learning_engine_node
  -> END
```

This does not shrink Silicon Org. The full organization remains in:

```text
ontology/nodes.yaml
ontology/relations.yaml
runtime/harness_profiles.yaml
```

`policy_router` reads the full weighted graph every time a node completes. It
builds legal activation candidates from `triggers`, `may_trigger`, and reverse
`evaluates` relations. Context-only relations stay context-only.

## What LangGraph Changes

The previous Silicon Org runtime already computed next-node candidates from
Graph + Policy. The LangGraph integration does not introduce dynamic
propagation; it changes the execution substrate that carries those decisions.

Before LangGraph, the Runtime had to manually hold the loop, remember which
candidates were considered, avoid stale state, perform fan-out, and resume
after interruptions. With LangGraph, Silicon Policy still computes the legal
candidates, while LangGraph carries the durable control loop, dynamic
`Send(...)`, state reducers, checkpoint/resume boundary, and post-delivery
stages.

## Full-Graph Dynamic Propagation

The runtime never preselects a three-layer path. A completed node produces a
Ledger fact and context report. Policy then scores all relevant graph edges:

```text
completed_role + artifact + context_block + ledger facts + relation weights
  -> candidate envelopes
  -> activate / skip / defer / interrupt
  -> LangGraph Send("run_role_node", role=<target>)
```

Candidate envelopes preserve dimensions:

```yaml
candidate:
  from: prototype
  to: senior-frontend
  relation_type: may_trigger
  legal: true
  score: 0.75
  confidence: 0.05
  dimensions:
    probability: {value: 0.35, confidence: 0.05, samples: 0}
    condition: feasibility of proposed solution is unknown
```

The scoring formula is Silicon Policy territory and can evolve with learning.
LangGraph only transports the decision and executes durable work.

## Harness Mapping

Every node has a profile in:

```text
runtime/harness_profiles.yaml
```

The profile defines:

- purpose
- model capability profile
- tool groups
- write scope
- resource budget
- required and optional inputs
- output artifact contract
- context focus
- activation notes
- completion gates

The runtime fails closed if `ontology/nodes.yaml` and
`runtime/harness_profiles.yaml` differ.

## Per-Node Model Routing

Concrete model IDs do not belong in the graph. They are configured locally:

```text
org/models.local.yaml
```

Resolution order:

1. `roles.<role>`
2. `profiles.<harness model_profile>`
3. `default`
4. Runtime current/default model

This means every node can run on a different provider/model without changing
the organization graph.

Example:

```yaml
roles:
  triage:
    provider: local
    model: fast-local-model
    reasoning_effort: low
  architect:
    provider: frontier
    model: strongest-architecture-model
    reasoning_effort: high
  security-engineer:
    provider: frontier
    model: security-specialist-model
    reasoning_effort: high
```

## Gates Are Policy Predicates

`artifact_valid`, `context_report_valid`, `required_evaluators_resolved`,
`convergence_reached`, and `can_deliver_success` are not organization nodes.
They are Policy predicates and Ledger transaction preconditions.

Real organization nodes include roles such as `security-engineer`,
`code-reviewer`, `delivery-prover`, `graph-topologist`, and `technical-writer`.

## Ledger Transactions

LangGraph checkpoints are execution state. Ledger is durable fact state.

LangGraph nodes must not perform scattered YAML writes. They submit idempotent
Ledger transactions through `runtime/ledger_transactions.py`:

```text
commit_node_activation
commit_artifact
commit_context_report
commit_handoff
commit_node_completion
commit_delivery
commit_learning_signal
```

This prevents the parallel write race observed in the previous trace.

Role execution is behind `runtime/node_runner.py`. The current built-in
`HarnessDryRunNodeRunner` is a deterministic local runner for release smoke and
plumbing validation; it is not a semantic replacement for isolated subagents.
`PromptPackageNodeRunner` assembles the complete invocation package an external
executor needs: registry harness, skill text, harness profile, model selection,
upstream handoffs, upstream artifact bodies, and required output shape.
`SemanticCommandNodeRunner` executes the package through a real local agent CLI
using `tools/semantic_node_executor.py`. `ExternalCommandNodeRunner` sends that
package to a local command via
`SILICON_ORG_INVOCATION_JSON` and `SILICON_ORG_INVOCATION_PROMPT`, then expects
JSON containing `artifact_body`, optional `artifact_type`, and optional
`context_report`.

Production runners should implement the same `NodeRunner` contract and provide
model/tool isolation per harness profile. The command runners are local-only;
they must not silently call hosted tracing or remote graph execution services.

Example local contract validator:

```bash
SILICON_ORG_NODE_EXECUTOR_CMD="python3 tools/local_node_executor.py" \
python3 tools/langgraph_native_smoke.py
```

## Activation Decisions

Every policy wave scores candidates from Silicon Graph relation weights. The
runtime can limit dispatch width for safety, but the choice is still dynamic:
highest-scoring candidates are activated first and non-dispatched candidates
remain in the candidate backlog. Candidates below threshold are recorded as
`defer` decisions in Ledger with an explicit reason.

For the current smoke trace, `triage -> diagnose` wins because its trigger
probability is higher than the other candidates. The handoff transaction then
records the corresponding `activate` event.

## Mandatory Post-Delivery Learning

After delivery:

```text
delivery outcome
  -> graph-topologist
  -> learning-engine
```

Graph Topologist reads the full trace: manifest, state, events, handoffs,
artifacts, evaluator findings, delivery proof, runtime fallbacks, skipped
candidates, timing, and quality signals.

Learning writes conservative proposals or updates:

- relation weights
- role reliability
- model-routing policy
- skipped-node penalties
- context block quality patterns
- graph topology proposals

This is where Silicon Org becomes a trained organization rather than a
workflow.

The smoke test writes learning output to the task trace only. It does not
mutate the global learning indices; production delivery can still call
`tools/ledger.py weights <task_id>` when the run should update cross-task
indices.
