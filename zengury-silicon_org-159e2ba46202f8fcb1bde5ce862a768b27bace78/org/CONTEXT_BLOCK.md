# Silicon Org Context Block

This file is the continuity anchor for Silicon Org. Read it before making
runtime, graph, ledger, policy, or learning decisions. Every task ledger should
record a reference and digest for this file so future traces can recover the
design intent that governed the run.

This is **not** the same thing as a handoff `context_block`.

- `org/CONTEXT_BLOCK.md` is organization-level memory: why Silicon Org exists,
  which concepts are load-bearing, and what must not drift.
- `handoffs/*/context_block` is task-level memory: what upstream context a node
  used to produce one deliverable.

## Who Uses This File

This file has five concrete consumers:

1. **Runtime** reads it before changing runtime, graph, ledger, policy,
   learning, or model-routing behavior.
2. **Ledger** records its SHA-256 digest in every new task manifest so future
   trace readers know which organizational intent governed the run.
3. **Policy maintainers** use it to reject changes that weaken graph legality,
   ledger truthfulness, or context-chain handoffs.
4. **Learning/evaluation code** uses it as the fixed intent reference when
   interpreting traces across versions.
5. **Future maintainers and ADR authors** use it to decide whether a change is
   a normal implementation detail or a change to Silicon Org's identity.

Ordinary nodes should not treat this file as task input unless they are working
on Silicon Org itself. For normal user tasks, downstream context comes from
artifact refs, handoff records, and the per-handoff `context_block`.

## Origin

Silicon Org exists to make large-model engineering work behave like a learning
organization instead of a bag of prompts. The original idea is not "many
agents". It is a graph-shaped organization whose structure, routing, quality
gates, and model choices improve from real programming experience.

The core analogy is a private neural network:

- Nodes are specialized organizational functions.
- Edges are typed and weighted synapses.
- Policy is the activation rule.
- Ledger is episodic memory.
- Learning updates weights, routing heuristics, model choices, and eventually
  graph topology.

## Current Core Concepts

Only five concepts are primary:

1. Graph = static law. Nodes, edges, edge types, weights, and reachability.
2. Ledger = durable task facts. Manifest, state, events, artifacts, handoffs.
3. Policy = legal interpreter. Graph + Ledger -> legal next actions.
4. Runtime = executor. It performs legal actions and writes back to Ledger.
5. Learning = feedback layer. It reads traces and proposes conservative
   updates without weakening Policy gates.

Do not create a new top-level entity unless it removes more confusion than it
adds. `ontology/` is the storage path for Graph files, not a separate concept.
`state.yaml` is part of Ledger, not a separate runtime-state system.

## Non-Negotiables

- Silicon Org's moat is Graph + Policy + Ledger + Runtime + Learning, not a
  particular execution framework.
- LangGraph may be used as an execution substrate, but it must not become the
  organization brain.
- Runtime may choose among legal options, but private reasoning is not a fact
  until it is written to the Ledger.
- Activation is dynamic and based on prior outputs. Do not pre-select a whole
  multi-layer path at task start.
- Every downstream handoff carries two things: the producer's deliverable and a
  compressed context block describing the upstream information used to produce
  it. The context block forms a digest-linked chain: each block summarizes prior
  blocks and artifact refs rather than forcing downstream nodes to re-read the
  entire trace.
- Context compression is structured, not stylistic. The producer node supplies
  a `context_compression_report` with source coverage, retained decisions,
  constraints, assumptions, open questions, omitted context, rationale, and
  quality checks. Ledger writes the block; Policy validates structure, source
  references, and digest integrity. A report that names an upstream handoff must
  cite the actual handoff ref and its exact `context_block.context_digest`, not
  a prose summary.
- `supports`, `constrains`, `complements`, and `augments` provide
  context or ordering pressure. They do not activate nodes by themselves.
- Every skipped, deferred, overridden, or fallback decision needs a ledger
  event. Silence is not state.
- Model IDs do not belong in Graph nodes. Store capability profiles and let
  users configure concrete providers.

## Decision Checklist

Before changing runtime, graph, policy, ledger, or learning:

1. Does this preserve the five-concept model?
2. Does this strengthen Ledger truthfulness?
3. Does this keep Silicon Org independent from any one agent or model vendor?
4. Does this produce learning signal, not just a one-off behavior?
5. Would a future maintainer understand the original intent from the trace?
6. Does each downstream handoff preserve the context chain: deliverable plus
   compressed upstream context, with prior block digests intact?
7. Does each context compression report explain its sources, omissions, and
   downstream impact rather than merely summarizing prose?
