# PRD: Three.js Realtime Silicon Org 3D Operations Visualizer

## Overview

Silicon Org has a rich operating model: Graph, Policy, Ledger, Runtime, and
Learning. Today those concepts exist mostly as files, traces, and protocol
rules. The user needs a living 3D operational surface that shows Silicon Org as
an organization in motion: which nodes exist, which nodes are active, why they
were activated, what handoff blocks moved between them, what each block carries,
what Policy allowed or blocked, what Ledger recorded, what Runtime is doing, and
what Learning may improve after the run.

The product is a local web frontend using Three.js or a Three.js-backed view. It
renders the current Silicon Org Graph, projects Ledger trace facts onto that
graph, animates node execution and handoff blocks, and provides readable
inspection surfaces for context blocks, artifacts, policy gates, timeline
events, and learning signals.

The first version should prove operational understanding with trace playback and
near-realtime trace polling. It must not create a new source of truth or replace
Silicon Org's Policy, Ledger, Runtime, or Learning logic.

## Goals

- Make Silicon Org understandable at a glance as a 3D organization, not a flat
  list of prompts or files.
- Show live or replayed task execution: active nodes, completed nodes, skipped
  nodes, deferred candidates, failed nodes, and convergence status.
- Make handoff blocks first-class visual objects with inspectable deliverable
  refs, context-block summaries, digest chains, relation metadata, and optional
  soul references.
- Explain Policy decisions visually: why a candidate exists, why activation is
  legal or illegal, and which decision was written to Ledger.
- Treat Ledger as the source of truth for run state, artifacts, handoffs,
  events, outcomes, and learning signals.
- Preserve the five-concept Silicon Org model: Graph, Policy, Ledger, Runtime,
  Learning.
- Provide a demo path that works even when no active runtime is currently
  running.

## Personas

### Silicon Org Builder

Maintains the graph, runtime protocol, ledger, learning loop, and future
LangGraph adapter. Needs to inspect whether the organization is behaving as
designed and whether context continuity is preserved.

### Runtime Operator

Watches an active task run. Needs to know what is happening now, what is blocked,
which node owns the next action, and whether convergence gates are clear.

### Graph Designer

Improves node topology and edge weights. Needs to see relation types, activation
paths, skipped candidates, weak edges, repeated handoffs, and learning signals.

### Reviewer / Quality Gate Owner

Checks whether artifacts and handoffs preserve the evidence chain. Needs quick
access to producer artifacts, context reports, context-block digests, and policy
gate failures.

## MVP Scope

The MVP is a local web app that can load Silicon Org graph files and one trace
folder, then replay or poll trace facts into a deterministic 3D scene.

### Required Surfaces

1. **3D Organization Graph**
   - Render all current Silicon Org nodes from `ontology/nodes.yaml`.
   - Render all relation edges from `ontology/relations.yaml`.
   - Place nodes in a deterministic layout by layer/domain so the same org has
     stable spatial memory across runs.
   - Visually distinguish activation-capable edges from context-only edges.

2. **Runtime Activity View**
   - Project node states from Ledger trace files onto the 3D graph.
   - Show at least these states: idle, candidate, activated, running, completed,
     skipped, deferred, failed, approved, delivered.
   - Animate active/running nodes with a pulse or glow.
   - Show completed nodes with timestamp and artifact count.

3. **Handoff Block Animation**
   - Animate handoff blocks moving from producer node to target node.
   - A handoff block must be clickable.
   - The block inspector must show deliverable refs, artifact metadata,
     context-block digest, retained decisions, constraints, assumptions, open
     questions, omitted context summary, relation type, focus, timestamp, and
     optional `soul_ref`.

4. **Policy Surface**
   - Show candidate activation cards or gates for trigger, may-trigger, and
     reverse-evaluates paths.
   - Show legal choices: activate, skip, defer.
   - Show blocked reasons when available: missing artifact, missing context
     report, context-only relation, unresolved candidate, blocking evaluation,
     malformed handoff, or unresolved artifact status.
   - Clearly mark that supports, constrains, complements, and augments cannot
     activate nodes by themselves.

5. **Ledger Surface**
   - Show manifest summary, task id, task type, outcome, context block digest,
     terminal nodes, convergence status, and timestamps.
   - Show node state table, event timeline, artifact list, context-report list,
     handoff trail, and unresolved gates.
   - Every displayed run fact must cite its source category: manifest, state,
     event, artifact registry, handoff file, or context report.

6. **Runtime Surface**
   - Show the Runtime as executor, not as the source of truth.
   - Display current phase when known: intake, propagation, convergence,
     delivery, or learning.
   - Show latest legal action applied and the Ledger write that resulted from
     it when such facts exist in events.

7. **Learning Surface**
   - Show learning signals and proposals when present in traces or learning
     indexes.
   - Show edge weight deltas, confidence changes, skip costs, model-routing
     observations, graph-topologist proposals, and HRBP skill signals when data
     exists.
   - Make clear that Learning proposes conservative updates and does not
     override Policy gates.

8. **Demo Mode**
   - If no live task is active, load a bundled or selected trace snapshot.
   - Replay the trace timeline so the user can see node activation and handoff
     movement.
   - Provide a reset/replay control.

## Realtime Behavior

The first implementation may use trace polling or a generated snapshot. It must
use a data model that can later be fed by a realtime runtime stream without
rewriting the frontend.

### Snapshot Contract

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
  context_reports: []
  handoffs: []
  candidates: []
  gates: []
learning:
  signals: []
  proposals: []
sources:
  graph_refs: []
  ledger_refs: []
  generated_at: string
```

### Update Rules

- The 3D scene updates from normalized snapshot state, not by parsing raw files
  inside rendering components.
- File polling is acceptable for MVP if visible updates appear within 2 seconds
  of a trace file change on a local machine.
- Handoff animations should be event-driven where timestamps exist and
  deterministic where only handoff files exist.
- Missing optional data should render as "not recorded" rather than inferred.
- The UI must not present private runtime reasoning as fact unless that
  reasoning appears in Ledger artifacts, events, handoffs, or reports.

## Functional Requirements

| ID | Requirement | Essential | Testable Criterion |
| --- | --- | --- | --- |
| R1 | Load graph nodes from `ontology/nodes.yaml`. | true | With the current repo, the scene renders the same count of nodes as the YAML file. |
| R2 | Load relation edges from `ontology/relations.yaml`. | true | With the current repo, the scene renders the same count of edges as the YAML file and exposes each relation type. |
| R3 | Render a deterministic 3D layout grouped by Silicon Org role/layer/domain. | true | Reloading the same snapshot produces the same node positions within a 1% tolerance. |
| R4 | Visually distinguish `triggers`, `may_trigger`, `evaluates`, `supports`, `constrains`, `complements`, and `augments`. | true | A user can identify each relation type from the legend and edge style without opening source files. |
| R5 | Distinguish activation-capable relations from context-only relations. | true | Context-only relation types are never styled as direct activation paths and include explanatory labeling. |
| R6 | Load Ledger facts from a trace folder. | true | Given a valid `traces/<task_id>/`, the app displays manifest, node states, artifacts, handoffs, context reports, and events that exist in that trace. |
| R7 | Animate node state changes during replay or polling. | true | Running a replay changes at least three node states over time and the visual state matches the underlying trace sequence. |
| R8 | Show active/running nodes with a visible animated state. | true | An activated or running node visibly pulses/glows within the 3D scene and is also marked in the detail panel. |
| R9 | Animate handoff blocks between producer and target nodes. | true | For each handoff in the selected trace, the app can animate a block along the producer-target path. |
| R10 | Make handoff blocks inspectable. | true | Clicking a handoff block opens a panel with deliverable refs, context-block digest, relation type, focus, timestamp, and available retained context. |
| R11 | Show context-block contents compactly. | true | The handoff inspector includes decisions, constraints, assumptions, open questions, omitted context, compression rationale, and quality checks when present. |
| R12 | Show Policy candidates and decisions. | true | Candidate, skipped, deferred, activated, or blocked decisions present in Ledger are visible in a Policy panel or gate overlay. |
| R13 | Explain blocked activation reasons when Ledger records them. | true | A blocked candidate shows the exact recorded reason rather than a generic "blocked" label. |
| R14 | Show Ledger timeline. | true | The bottom or side timeline lists events in timestamp order and selecting an event highlights related nodes or handoffs. |
| R15 | Show Graph, Policy, Ledger, Runtime, and Learning as first-class areas. | true | The first viewport contains labeled or visually distinct surfaces for all five concepts. |
| R16 | Provide side-panel inspection for nodes, edges, handoffs, artifacts, and policy gates. | true | Clicking each object type opens an object-specific panel with relevant metadata and source references. |
| R17 | Support demo replay without an active runtime. | true | The app can replay a chosen existing trace from the repo with no external service running. |
| R18 | Support near-realtime local update mode. | true | When a watched trace file changes, the rendered state updates within 2 seconds in local dev. |
| R19 | Preserve Ledger as source of truth. | true | No displayed operational state appears without a graph, manifest, state, event, artifact, handoff, context-report, or learning source reference. |
| R20 | Provide visual filtering. | true | User can filter or dim by relation type, node state, layer/domain, and trace phase. |
| R21 | Provide camera controls. | true | User can orbit, zoom, pan, focus a selected node, and reset camera to overview. |
| R22 | Include dark operations theme. | true | Default UI is legible in dark mode with contrast sufficient for labels, panels, and graph elements. |
| R23 | Avoid uncontrolled layout physics by default. | true | Nodes do not drift after initial load unless the user explicitly switches layout mode. |
| R24 | Show learning signals when data exists. | true | If learning signal/proposal files are present, the Learning surface lists them and links them to edges/nodes where possible. |
| R25 | Export or copy a run snapshot for debugging. | false | User can export the normalized snapshot JSON/YAML used by the frontend. |
| R26 | Select among multiple trace folders. | false | User can choose from available traces and reload the scene without restarting the app. |
| R27 | Show model routing metadata when present. | false | If node/model metadata exists in artifacts or events, node details show model profile/source. |

## Non-Functional Requirements

| ID | Requirement | Essential | Testable Criterion |
| --- | --- | --- | --- |
| N1 | Initial load performance. | true | Current graph plus one trace loads to first rendered scene within 3 seconds on a typical local development laptop. |
| N2 | Interaction performance. | true | Orbit, zoom, hover, and click interactions remain above 30 FPS with current graph size and one active trace. |
| N3 | Source traceability. | true | At least 95% of visible operational facts have a displayed source reference; unavailable optional facts show "not recorded". |
| N4 | Responsive layout. | true | The app remains usable at 1440px desktop width and 390px mobile width without overlapping critical UI. |
| N5 | Accessibility baseline. | true | Panels and controls are keyboard reachable, labels have readable contrast, and canvas selection has mirrored text details. |
| N6 | Failure clarity. | true | Malformed or missing trace files produce visible, actionable error states without blanking the whole scene. |
| N7 | Data adapter isolation. | true | Rendering components consume the normalized snapshot contract and do not directly read raw YAML/trace files. |

## Main Interface Design

### First Viewport

- Center: full-bleed Three.js organization map.
- Top bar: task id, run status, convergence status, phase, replay/live toggle,
  trace selector if available.
- Left rail: Graph filters, Policy gates, active candidates, relation legend.
- Right inspector: selected node, edge, handoff block, artifact, context block,
  policy gate, or learning signal.
- Bottom rail: Ledger event timeline with replay scrubber and event markers.
- Peripheral surfaces:
  - Policy gate plane between candidate source and target paths.
  - Ledger timeline plane anchored below the graph.
  - Runtime pulse/orchestrator object showing current legal action and phase.
  - Learning halo around graph edges/nodes with post-run proposal markers.

### Object Interactions

- Click node: role, title, domain, layer, status, timestamps, artifacts,
  inbound/outbound edges, handoffs, context reports, and latest events.
- Click edge: relation type, weight/necessity/strictness, probability,
  activation capability, condition, last observed decisions, and source file.
- Click handoff block: deliverable, context block, digest chain, focus, relation
  type, timestamp, producer, target, quality checks, and soul reference.
- Click Policy gate: candidate basis, legal options, selected decision, blocking
  reason, and ledger event.
- Click Ledger event: highlight related node/edge/handoff and show event payload.
- Click Learning marker: show proposed weight/model/topology update and source
  trace signal.

## Acceptance Criteria

- AC1: Opening the app renders a nonblank Three.js scene with Silicon Org nodes
  and typed edges from the current repo.
- AC2: The scene includes visible Graph, Policy, Ledger, Runtime, and Learning
  surfaces.
- AC3: Loading a trace shows node states that match `state.yaml`.
- AC4: Replaying a trace animates at least one node activation/completion
  sequence and at least one handoff block.
- AC5: Clicking a handoff block reveals deliverable refs and context-block
  details including the digest.
- AC6: The UI clearly marks context-only relations as non-activation edges.
- AC7: A Policy panel shows legal/blocked/deferred/skipped decisions when those
  facts exist in the trace.
- AC8: A Ledger timeline lists events in chronological order and highlights
  related scene objects.
- AC9: The app can run in demo mode without an active Silicon Org task.
- AC10: The normalized snapshot contract is documented and used as the frontend
  rendering input.
- AC11: Browser verification confirms desktop and mobile views render without
  critical overlap and the canvas is nonblank.

## Non-Goals

- Do not replace Silicon Org runtime execution, policy legality, ledger writes,
  or learning updates.
- Do not make LangGraph or any runtime adapter the organization brain.
- Do not edit graph topology from the 3D UI in MVP.
- Do not execute or approve nodes from the UI in MVP.
- Do not build a hosted multi-user observability platform in MVP.
- Do not implement full artifact full-text rendering inside the 3D scene.
- Do not infer private runtime reasoning that has not been written to Ledger.
- Do not make a generic multi-agent dashboard detached from Silicon Org's
  Graph/Policy/Ledger/Runtime/Learning model.

## Open Questions

- Which trace should become the canonical demo trace for first delivery?
- Should MVP trace selection be fixed, dropdown-based, or file-picker-based?
- Should the frontend live as a static viewer generated from snapshots or as a
  dev-server app with a lightweight local API?
- How should future live runtime streams authenticate or bind to a local task
  without adding hosted infrastructure?

## Risks

- A visually impressive 3D scene may hide causality. Mitigation: deterministic
  layout, explicit edge semantics, event timeline, and readable inspectors.
- Realtime plumbing may grow too large for MVP. Mitigation: start with trace
  replay and polling behind the same snapshot contract.
- UI may accidentally present inferred state as truth. Mitigation: source
  references and "not recorded" fallback for missing facts.
- Edge semantics may be flattened. Mitigation: relation-specific styling and
  policy explanations for activation capability.
- Context blocks may become unreadable in 3D. Mitigation: animate blocks in the
  scene but render details in a side inspector.
- Existing trace schema may evolve. Mitigation: tolerant adapter, versioned
  snapshot schema, and explicit missing-field handling.

## Success Criteria

- A maintainer can understand a Silicon Org run without opening raw trace files.
- The user can answer "what is happening, why, and what evidence exists" from
  the visualizer within 30 seconds of opening a trace.
- The visualizer improves continuity by making context-block chains visible.
- The implementation preserves Ledger as the truth layer and uses a reusable
  snapshot contract for future realtime integration.
- The visualizer becomes a foundation for later graph-learning inspection
  rather than a one-off animated diagram.

## Completion Report

```yaml
completion_report:
  what_was_done: >
    Produced a PRD for a Three.js realtime Silicon Org 3D operations
    visualizer covering goals, personas, MVP scope, realtime behavior,
    node/handoff/context-block visualization, Graph/Policy/Ledger/Runtime/
    Learning surfaces, requirements, acceptance criteria, non-goals, open
    questions, and risks.
  key_decisions:
    - decision: "Use Ledger-derived normalized snapshots as the frontend source of truth."
      rationale: "This preserves Silicon Org's rule that private Runtime reasoning is not fact until written to Ledger while leaving room for future live streams."
    - decision: "Make handoff blocks first-class inspectable objects."
      rationale: "The user explicitly wants block transfer and block contents visible, and context continuity is a core Silicon Org moat."
    - decision: "Start with trace replay and near-realtime polling before full event streaming."
      rationale: "Replay proves the operating model with lower infrastructure cost and the same snapshot schema can later accept live runtime events."
    - decision: "Use deterministic spatial layout instead of uncontrolled graph physics by default."
      rationale: "Stable spatial memory helps users compare runs and understand causality."
  handoff_focus:
    - "Architect should define the trace-to-snapshot adapter, live-stream boundary, and local app packaging."
    - "UX should validate the five-surface mental model and readable inspection patterns."
    - "Prototype should prove nonblank Three.js rendering, deterministic layout, handoff block animation, and context-block inspection."
    - "Frontend should keep rendering components isolated from raw YAML parsing."
  open_questions:
    - "Which trace should become the canonical demo trace for first delivery?"
    - "Should MVP trace selection be fixed, dropdown-based, or file-picker-based?"
    - "Should the frontend live as a static viewer generated from snapshots or as a dev-server app with a lightweight local API?"
  known_constraints:
    - "Graph, Policy, Ledger, Runtime, and Learning remain the five primary concepts."
    - "Ledger trace facts are the source of truth for displayed operational state."
    - "Context-only relations must not be shown as direct activation edges."
    - "Activation is dynamic and based on prior outputs, not preselected full paths."
    - "The visualizer must not replace runtime, policy, ledger, or learning behavior."
  confidence_differential: 0.05
  dissent_if_alone: null
  iteration_context: null
```
