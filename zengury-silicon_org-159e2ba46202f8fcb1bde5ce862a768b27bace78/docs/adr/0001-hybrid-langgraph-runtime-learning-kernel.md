# ADR 0001: LangGraph-Native Runtime and Learning Kernel

Date: 2026-05-26

## Status

Superseded by LangGraph-native runtime direction. The earlier optional-adapter
position is no longer the target architecture.

## Context

Silicon Org's Graph, Policy, Ledger, node harnesses, and documentation have
become richer than its Runtime implementation. The current runtime is mostly
protocol plus small CLI tools. That was useful for proving the design, but it
does not yet provide mature durable execution, checkpoint/resume, isolated
subagent execution, human-in-the-loop pauses, or robust parallel orchestration.

At the same time, Silicon Org's core value should not become a generic runtime
framework. The defensible part is the learnable organization: typed weighted
edges, activation policy, artifact contracts, ledger truth, and accumulated
programming experience.

LangGraph OSS core is MIT licensed and already solves much of the execution
substrate problem. Platform-specific LangGraph services are not treated as core
dependencies.

## Decision

Adopt a LangGraph-native architecture:

- Silicon Org remains the policy and learning layer.
- LangGraph OSS core is the target execution kernel, not an adapter wrapper.
- All 35 ontology nodes must have harness profiles and be executable through
  the generic LangGraph `run_role_node`.
- Silicon Policy dynamically routes the full weighted graph and emits LangGraph
  `Send(...)` fan-out decisions.
- Ledger remains the source of truth; LangGraph checkpoints are execution
  support, not canonical task memory.
- Concrete model IDs remain configurable per role/profile in local model
  routing config, not in Graph nodes.
- Learning Kernel becomes a first-class package for structured outcome,
  role, relation, cost, review, and model-routing signals.

## Consequences

Positive:

- Runtime gains a path to durable execution without reimplementing a workflow
  engine.
- Node isolation can move toward LangGraph subgraphs over time.
- Future model routing can be implemented independently of Graph topology.
- Learning can become the long-term moat rather than a coarse outcome counter.

Tradeoffs:

- There are now two graph concepts: Silicon Org Graph and LangGraph execution
  graph. Documentation must keep this distinction sharp.
- Runtime implementation must keep Silicon Graph and LangGraph execution graph
  distinct.
- Ledger and LangGraph checkpoint state can drift unless all durable facts go
  through idempotent Ledger transactions.
- Full-node harness coverage is mandatory; partial closed-loop demos are not a
  substitute for dynamic graph propagation.

## Implementation Status

1. `runtime/langgraph_native.py` defines the target LangGraph-native runtime.
2. `runtime/harness_profiles.yaml` maps all 35 ontology nodes to harness
   resources, constraints, tools, model profiles, and output contracts.
3. `docs/LANGGRAPH_NATIVE_RUNTIME.md` records the non-adapter architecture.
4. `learning/` contains structured signals and conservative scoring helpers.
5. `org/CONTEXT_BLOCK.md` is recorded by digest in new task manifests.
6. `tools/policy.py` owns activation and graph-legality checks.
7. `tools/ledger.py` remains the durable write surface and calls Policy before
   state-changing operations.
