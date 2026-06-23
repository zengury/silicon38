# Caveman Analysis: Three.js Silicon Org Operations Visualizer

## One User Outcome

User needs one living map of Silicon Org.

Not static diagram. Not pretty graph only.

Need see:
- what organization is
- who is working now
- why node became active
- what block moved between nodes
- what each block carries
- what Policy allowed or blocked
- what Ledger recorded
- what Runtime is doing
- what Learning will change later

If user watches task run, map should answer: "What is happening? Why? What evidence exists?"

## Plain Model

Silicon Org = learning organization.

- Graph = law. Nodes, edges, weights, allowed routes.
- Policy = judge. Reads Graph + Ledger, decides legal next actions.
- Ledger = memory. Records facts, artifacts, handoffs, events, outcomes.
- Runtime = worker. Executes legal actions, writes facts back.
- Learning = slow brain. Reads traces, adjusts weights, routing, model choices, maybe graph shape.

3D visualizer must show these five, not hide them behind one graph blob.

## What Must Be Visible

### 1. Organization Graph

Show 35 agent nodes as 3D points or cards.

Layer placement:
- Layer 1 intake nodes near front/top
- Layer 2 execution nodes in middle
- Layer 3 quality/output nodes near back/bottom
- meta nodes slightly outside main plane: HRBP, graph-topologist, skill-scout

Edges:
- triggers / may_trigger = bright activation-capable paths
- evaluates = review paths, visually reverse-aware
- supports / constrains / complements / augments = thinner context/pressure paths

Weight:
- edge thickness or glow = probability / necessity / strictness
- confidence = opacity

### 2. Runtime Activity

Node states:
- idle
- candidate
- activated
- running
- completed
- skipped
- deferred
- failed
- approved

Activity must be time-based. If node is running, user sees pulse. If completed, user sees timestamp and artifact count.

### 3. Handoff Blocks

Handoff is not just edge animation.

Show moving block from producer to target.

Block must contain visible slices:
- deliverable: artifact refs and type
- context_block: compressed upstream decisions, constraints, assumptions, open questions
- digest chain: previous context digest
- soul_ref if target carries soul
- relation type and focus

Click block -> side panel opens compact content preview.

### 4. Policy Layer

Policy should appear as gate/checkpoint, not invisible code.

When candidate appears, show:
- source node
- target node
- relation type
- reason candidate exists
- legal choices: activate / skip / defer
- decision written to Ledger

If blocked, show exact missing fact:
- no artifact
- no context report
- context-only relation
- unresolved candidate
- blocking evaluation open

### 5. Ledger Layer

Ledger should be timeline + evidence drawer.

Visible:
- manifest summary
- node state table
- events timeline
- artifacts list
- handoff trail
- unresolved gates
- outcome and learning signal

Ledger is source of truth. 3D map is projection from Ledger, not separate truth.

### 6. Learning Layer

Learning should be "after-action intelligence", not magic.

Show:
- edges with changed weights
- confidence changes
- skip costs
- model routing signal
- graph-topologist proposals
- HRBP skill performance signals

Learning should never look like it directly overrides Policy. It proposes conservative updates.

## Minimum Viable Version

Build one local web app:

- Three.js scene with 35 nodes from `ontology/nodes.yaml`
- edges from `ontology/relations.yaml`
- static five-zone layout: Graph center, Policy gate, Ledger timeline, Runtime pulse, Learning halo
- load one trace folder from `traces/<task_id>/`
- animate node state from `events.yaml`
- animate handoff blocks from `handoffs/*.yaml`
- side panel for selected node / edge / handoff / artifact
- theme fits dark ops console

No backend required for V1. Read local JSON/YAML snapshots or generated static JSON.

This already proves core thing: Silicon Org can see itself run.

## Complexity To Avoid

Avoid first:
- real-time WebSocket server
- full replay scrubber with branching timelines
- editing graph in 3D
- live policy mutation from UI
- collaborative comments
- physics-heavy layout that moves every frame
- photorealistic sci-fi scene
- every artifact rendered full-text in scene

Reason: user needs operational understanding first. Too much motion hides causality.

## Justified Complexity

Use Three.js because:
- graph is relational, layered, spatial
- handoff blocks moving through edges are easier to understand in 3D than tables
- Policy/Ledger/Runtime/Learning can be visible as separate planes around graph

Use deterministic layout because:
- same org should look same every run
- user builds spatial memory
- diffs between runs become visible

Use side panel because:
- 3D scene shows shape
- details need readable text

Use event replay because:
- live view without history cannot explain why current state happened

Use data adapter because:
- trace files are truth now
- future LangGraph or runtime stream can feed same visual schema

## Product Shape

Main screen:
- center: 3D org map
- left rail: task manifest, active gates, filters
- right panel: selected object details
- bottom: ledger timeline
- top: run status, task id, convergence status, model routing profile

Primary interactions:
- click node -> see role, layer, harness, status, artifacts, inbound/outbound candidates
- click edge -> see type, weight, confidence, samples, last decision
- click moving block -> see deliverable + context_block digest chain
- click Policy gate -> see legal/illegal activation decisions
- click Learning halo -> see weight deltas and proposals

## Essential Data Contract

Visualizer should not parse raw files everywhere.

Create normalized run snapshot:

```yaml
org:
  nodes: []
  edges: []
run:
  task_id: string
  manifest: {}
  node_states: {}
  events: []
  artifacts: []
  handoffs: []
  candidates: []
  gates: []
learning:
  signals: []
  proposals: []
```

This snapshot can be generated from current Ledger files now. Later runtime can stream same shape.

## First Build Order

1. Build trace-to-snapshot adapter.
2. Build deterministic 3D layout.
3. Render nodes and typed edges.
4. Replay events into node states.
5. Animate handoff blocks.
6. Add side panel.
7. Add Policy/Ledger/Learning overlays.
8. Add live update hook later.

## Completion Report

```yaml
completion_report:
  what_was_done: "Reduced the Three.js realtime Silicon Org visualizer request to its essential operational outcome and first viable product shape."
  key_decisions:
    - decision: "Make Ledger-derived run snapshot the visualizer source of truth."
      rationale: "Private runtime state is not fact. Ledger facts keep visualization auditable."
    - decision: "Show five primary concepts as distinct visual zones: Graph, Policy, Ledger, Runtime, Learning."
      rationale: "User wants organization operation model visible, not only agent graph."
    - decision: "Use deterministic 3D layout instead of free physics as default."
      rationale: "Stable spatial memory makes runs comparable and causality easier to inspect."
    - decision: "Defer live server and graph editing until after replay MVP."
      rationale: "Replay proves understanding with lower complexity; live transport can reuse same snapshot schema."
  handoff_focus:
    - "Architect should define frontend/data architecture around trace-to-snapshot adapter and live stream boundary."
    - "UX should design readable operations surface: 3D map plus ledger timeline plus detail panel."
    - "Prototype/frontend should prove node activity and handoff block animation before adding advanced controls."
  open_questions:
    - "Should first demo load one fixed task trace or let user pick any trace folder?"
    - "Should the visualizer live inside this repo as a static app or as a dev-server frontend package?"
    - "Which trace should be the canonical demo run?"
  known_constraints:
    - "Visualizer must reflect Graph/Policy/Ledger/Runtime/Learning without creating new top-level concepts."
    - "Ledger remains source of truth; visual scene is projection."
    - "supports/constrains/complements/augments are context or pressure, not activation by themselves."
    - "Handoff block must include deliverable plus compressed context block, not just edge animation."
  confidence_differential: 0.82
  dissent_if_alone: "Do not build gorgeous 3D first. Build honest replay first, then make it beautiful."
  iteration_context: "Entry-node first-principles analysis for a Three.js realtime operations visualizer of Silicon Org."
```
