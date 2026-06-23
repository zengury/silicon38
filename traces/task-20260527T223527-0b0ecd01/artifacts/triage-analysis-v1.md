# Triage Analysis — Silicon Org 3D Operations Visualizer

## Task Classification

```yaml
task_type: feature
subtype:
  - internal_observability
  - graph_visualization
  - realtime_operations_ui
  - developer_experience
priority: high
priority_justification: >
  The request targets Silicon Org's own operating surface: a realtime visualizer
  for Graph, Policy, Ledger, Runtime, Learning, node activity, handoffs, and
  context blocks. This directly protects continuity, auditability, and the
  user's concern that iterative work may drift away from the original intent.
```

## Problem Statement

Silicon Org currently has a rich organizational graph, ledger, policy, runtime,
learning loop, and context-block discipline, but the user cannot see that system
operate as a live organization. The desired state is a Three.js-based frontend
that renders the organization as a 3D operational map and updates as runs
progress: active nodes glow or animate, handoffs move between nodes, context
blocks appear as payloads attached to transfers, and Policy/Ledger/Runtime/
Learning are visible as governance and operating layers rather than hidden
files.

This is falsifiable: the task is not done until a user can open a runnable demo
and inspect the current Silicon Org graph plus at least one live or simulated
trace flow with node activity, handoff payloads, and context-block metadata.

## Scope

### In Scope

- Build a frontend experience using Three.js or a Three.js wrapper that presents
  Silicon Org as a 3D organization map.
- Represent the five primary concepts from `org/CONTEXT_BLOCK.md`:
  Graph, Ledger, Policy, Runtime, and Learning.
- Render graph nodes from `ontology/nodes.yaml` and relation edges from
  `ontology/relations.yaml`.
- Show different edge semantics visually:
  `triggers`, `may_trigger`, `supports`, `evaluates`, `constrains`,
  `complements`, and `augments`.
- Show operational state from task traces:
  activated, running, completed, skipped, blocked, evaluating, delivered.
- Show handoffs as animated transfers between nodes.
- Show each handoff's context block as an inspectable payload with retained
  decisions, constraints, assumptions, open questions, omitted context, and
  digest/provenance references.
- Show Policy as the legality/gate layer that explains why an activation is
  legal, deferred, or skipped.
- Show Ledger as the durable fact layer: manifest, state, events, artifacts,
  handoffs, and context reports.
- Show Runtime as the execution layer that applies legal actions and updates
  Ledger.
- Show Learning as post-run feedback: weights, proposals, HRBP/graph-topologist
  loops, and graph evolution signals.
- Support realtime or near-realtime updates from trace files or a local runtime
  event stream.
- Include a demo mode when no active Silicon Org task is running.
- Maintain a clear path from demo visualization to future production
  observability.

### Out of Scope

- Replacing Silicon Org's Policy, Ledger, Graph, Runtime, or Learning logic.
- Making LangGraph the organization brain.
- Changing graph legality rules or edge semantics.
- Editing the graph topology unless downstream architecture/design work
  explicitly identifies required visualization metadata.
- Building a generic multi-agent dashboard unrelated to Silicon Org's own
  concepts.
- Adding remote multi-user auth, hosted deployment, or cloud persistence in the
  first demo.
- Rewriting trace storage or making a new source of truth outside Ledger.
- Implementing arbitrary node execution from the UI.
- Designing model-routing policy unless needed to display model activity.

## Key Constraints

- `org/CONTEXT_BLOCK.md` defines the conceptual anchor: Graph, Ledger, Policy,
  Runtime, Learning. The visualizer must reinforce this model rather than
  introduce competing top-level concepts.
- `ontology/` is the storage path for Graph files, not a separate product
  concept in the UI.
- `state.yaml` is part of Ledger, not a separate runtime-state concept.
- Graph legality remains server/tool-side; the frontend may visualize and
  explain legality but must not become the source of truth.
- `supports`, `constrains`, `complements`, and `augments` are not activation
  edges. The UI must not imply they directly activate nodes.
- Activation is dynamic and based on prior outputs. The visualization should
  show candidates and decisions over time, not a preselected full path.
- Every handoff includes both deliverable refs and a digest-linked
  `context_block`; the UI should show both.
- Runtime private reasoning is not a fact until written to Ledger; the UI should
  render Ledger facts, not inferred invisible state.

## Risks

- **Concept drift risk:** A flashy 3D visualization could obscure Silicon Org's
  core semantics. Mitigation: design around Graph/Ledger/Policy/Runtime/Learning
  as first-class layers.
- **False authority risk:** If the UI infers state not written to Ledger, users
  may trust ungrounded information. Mitigation: every displayed operational
  fact must cite trace source files or event records.
- **Performance risk:** Rendering 35 nodes and 122 edges is manageable, but
  animated history, particles, labels, and payload panels may become cluttered.
  Mitigation: level-of-detail controls, filtering, and focused trace playback.
- **Semantic edge risk:** Edge types have different meanings; visual encoding
  must not flatten them into one generic line type.
- **Realtime plumbing risk:** File watching, event streaming, and browser state
  can become a separate infrastructure project. Mitigation: start with local
  trace polling or a lightweight dev server API, then evolve.
- **Implementation quality risk:** Three.js scenes can appear blank or broken
  under responsive layouts. Mitigation: require delivery-prover/browser
  verification across desktop and mobile viewports.
- **Overbuilt v1 risk:** Full operational control, collaboration, and graph
  editing would delay the core demo. Mitigation: v1 focuses on visualization,
  inspection, and playback.

## Recommended Next Graph Candidates

These are graph candidates for Runtime to evaluate after this triage node
completes. They are recommendations, not forced activations.

```yaml
recommended_candidates:
  - role: caveman
    relation_basis: entry_node_already_active
    reason: >
      Reduce the visualizer to the essential user outcome and prevent an
      overbuilt 3D spectacle from displacing operational clarity.

  - role: to-prd
    relation_basis: triage -> to-prd triggers probability 0.70
    reason: >
      Convert the request into product requirements: personas, critical views,
      realtime behavior, demo acceptance, and staged scope.

  - role: ux-researcher-designer
    relation_basis: triage -> ux-researcher-designer may_trigger
    condition_assessment: task involves user-facing interface and interaction design
    reason: >
      Define the mental model, navigation, inspect interactions, state legends,
      and how a user understands the organization at a glance.

  - role: prototype
    relation_basis: triage -> prototype may_trigger
    condition_assessment: feasibility of proposed 3D interaction is unknown
    reason: >
      Validate layout, camera, animation, payload inspection, and trace playback
      before committing to production structure.

  - role: architect
    relation_basis: downstream from to-prd or zoom-out may_trigger, not direct from triage
    reason: >
      Design data ingestion from Graph and Ledger, runtime event streaming,
      frontend/backend boundary, and demo-to-production path.

  - role: ui-design-system
    relation_basis: downstream from ux-researcher-designer may_trigger
    reason: >
      Define visual encodings for node states, edge types, policy gates, ledger
      facts, learning signals, and context blocks.

  - role: epic-design
    relation_basis: downstream from ui-design-system may_trigger
    reason: >
      The request explicitly asks for a memorable 3D front-end summary; this
      node can shape the immersive treatment without sacrificing operational
      clarity.

  - role: senior-frontend
    relation_basis: downstream from prototype/ui-design-system/epic-design
    reason: >
      Implement the runnable Three.js demo once design and data contracts are
      clear.

  - role: delivery-prover
    relation_basis: prototype/senior-frontend -> delivery-prover triggers
    reason: >
      Verify the 3D scene is nonblank, responsive, interactive, and actually
      renders graph/activity/context-block elements.

  - role: code-reviewer
    relation_basis: senior-frontend/delivery-prover -> code-reviewer triggers
    reason: >
      Review correctness, maintainability, trace-source truthfulness, and
      frontend failure modes before convergence.
```

## Blocking Questions

None for the first graph pass. The request is clear enough to proceed into
product/design/prototype/architecture. Downstream nodes may ask targeted
questions only if they must choose between incompatible UI/data directions.

## Done Conditions

- A runnable frontend demo exists and can be opened locally.
- The demo renders Silicon Org's current graph with node groups/layers and typed
  relation edges.
- The demo shows the five operating concepts: Graph, Ledger, Policy, Runtime,
  Learning.
- The demo can replay or simulate a Silicon Org run, including active nodes,
  completed nodes, handoff animation, and context-block payload inspection.
- Displayed operational facts are sourced from graph files or trace ledger
  files rather than private inference.
- The visual semantics distinguish activation-capable edges from context-only
  relations.
- Browser/visual verification confirms the Three.js canvas is nonblank,
  responsive, correctly framed, and interactive.
- The implementation leaves room for future realtime trace streaming without
  replacing Ledger as source of truth.

## Completion Report

```yaml
completion_report:
  what_was_done: >
    Classified the user request as a high-priority Silicon Org internal
    feature and produced scope boundaries, risks, graph candidate
    recommendations, and completion conditions for downstream nodes.
  key_decisions:
    - decision: Treat this as an internal observability and graph-visualization feature.
      rationale: >
        The requested UI is not a generic dashboard; it visualizes Silicon Org's
        own operating model, trace facts, handoffs, and context-chain behavior.
    - decision: Recommend prototype and UX work before frontend implementation.
      rationale: >
        The hardest risk is not rendering a graph but preserving the semantics
        of Policy, Ledger, Runtime, Learning, edge types, and context blocks in
        a usable 3D mental model.
    - decision: Require Ledger-backed facts in the UI.
      rationale: >
        Silicon Org's auditability depends on private runtime reasoning not
        being presented as operational truth unless it is written to Ledger.
  handoff_focus:
    - Preserve the five-concept model from org/CONTEXT_BLOCK.md.
    - Make context blocks inspectable, not just decorative particles.
    - Separate activation-capable edges from context-only relations visually.
    - Start with a demo/playback mode and evolve toward realtime streaming.
  open_questions: []
  known_constraints:
    - Do not replace Graph, Ledger, Policy, Runtime, or Learning.
    - Do not make the frontend a source of truth for legality or execution state.
    - Do not imply supports/constrains/complements/augments activate nodes.
    - Keep activation dynamic and trace-driven.
  confidence_differential: 0.08
  dissent_if_alone: null
  iteration_context: null
```
