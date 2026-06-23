# UX Spec: Silicon Org 3D Operations Visualizer

## Purpose

Build an operator-facing Three.js interface that lets a maintainer watch Silicon
Org behave as a living organization. The interface must answer four questions in
one glance:

1. What is the organization made of?
2. What is running now?
3. Why did the Runtime activate, skip, defer, or block a node?
4. What evidence was passed between nodes, including the context block chain?

The visualizer is an operational projection of Graph and Ledger facts. It is
not a new source of truth, a graph editor, or a replacement for Policy.

## Primary Users

### Runtime Operator

Watches an active or replayed Silicon Org run, confirms that graph propagation
is legal, and notices missing context, blocked candidates, or weak handoffs.

Needs:
- Instant read of active nodes and pending gates.
- Confidence that displayed state comes from Ledger facts.
- Fast inspection of handoffs without opening raw YAML files.

### Org Maintainer

Tunes graph, policy, learning, and model-routing behavior across many traces.

Needs:
- Compare relation behavior across runs.
- See where skips, deferrals, blocking reviews, and weak learning signals occur.
- Preserve the five-concept mental model: Graph, Ledger, Policy, Runtime,
  Learning.

### New Contributor

Learns how Silicon Org operates without reading every protocol file first.

Needs:
- Stable spatial layout.
- Plain status language.
- Inspectable evidence chain.

## Design Principles

- Ledger first: every status, artifact, handoff, decision, digest, and outcome
  shown in the UI cites a trace or graph source.
- Stable over spectacular: the organization should occupy the same spatial
  shape across runs so users build memory.
- Causality over animation: motion should show why and when something happened.
- Five concepts, no drift: Graph, Ledger, Policy, Runtime, and Learning are the
  only top-level operating concepts.
- Details on demand: the 3D scene shows structure and motion; side panels show
  readable evidence.

## Information Architecture

### App Shell

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Top bar: task id | live/replay | convergence | source truth | model profile │
├───────────────┬───────────────────────────────────────────────┬─────────────┤
│ Left rail     │ 3D organization scene                         │ Inspector   │
│               │                                               │             │
│ - Run summary │ - Graph nodes                                 │ - Selected  │
│ - Gates       │ - Typed edges                                 │   object    │
│ - Filters     │ - Policy gates                                │ - Evidence  │
│ - Search      │ - Handoff blocks                              │ - Context   │
│               │ - Runtime activity                            │   chain     │
├───────────────┴───────────────────────────────────────────────┴─────────────┤
│ Ledger timeline: events, node state changes, handoffs, gates, outcome       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### First Viewport

The first viewport should open directly into the operational surface, not a
landing page.

Visible immediately:
- Current task id and mode: Live, Replay, or Demo.
- Convergence badge: Running, Blocked, Converged, Delivered, or Incomplete.
- Center 3D org map with all 35 nodes and 122 typed edges.
- Active nodes pulsing, completed nodes settled, candidates rim-lit.
- One visible handoff block when a replayed event exists.
- Left rail with open gates and active filters.
- Right inspector in an empty state: "Select node, edge, block, or event."
- Bottom timeline at the current event position.

The scene should use a dark operations-console theme by default. Light theme can
invert the same semantic tokens without changing meanings.

## Spatial Model

### Layout

Use deterministic placement, not free physics as the default.

- Layer 1 intake and planning nodes sit on the front/top band.
- Layer 2 execution and design nodes sit through the central band.
- Layer 3 quality and delivery nodes sit on the rear/bottom band.
- Organizational learning nodes sit in an outer halo.
- Policy gates sit as translucent checkpoints between producer and candidate
  target when a decision exists.
- Ledger is represented as a horizontal evidence plane below the graph.
- Runtime is represented as a vertical activity spine that emits legal actions
  into the graph.
- Learning is represented as a slow outer halo, only lighting up after outcomes
  or learning proposals exist.

This preserves the mental model:

```
Graph = center structure
Policy = gates/checkpoints
Ledger = evidence plane and timeline
Runtime = activity spine
Learning = outer feedback halo
```

### Camera

Default camera:
- 3/4 perspective, all nodes in frame.
- Slight depth so handoff blocks can move along visible arcs.
- No automatic spinning.

Controls:
- Orbit: drag background.
- Pan: shift-drag or middle drag.
- Zoom: wheel/pinch.
- Reset: one button returns to canonical view.
- Focus: double-click node, edge, handoff, or event to center it.

## Visual Semantics

### Node Status Language

Use the same labels in scene, inspector, timeline, and filters.

| Status | Meaning | Visual treatment |
|---|---|---|
| idle | Node exists in Graph but has no current run activity | Low-opacity solid node |
| candidate | Policy has a possible activation decision to make | Thin amber rim |
| activated | Ledger records node activation | Bright outline, no pulse yet |
| running | Node execution is in progress | Slow breathing pulse |
| completed | Node completed and registered required outputs | Stable filled node with artifact count |
| skipped | Runtime explicitly skipped node or edge candidate | Muted node with diagonal mark |
| deferred | Candidate kept for later decision | Amber paused ring |
| blocked | Policy gate is missing required facts | Red gate marker attached to node or edge |
| evaluating | Evaluator is reviewing a producer artifact | Purple review beam |
| approved | Artifact or evaluation passed | Green check accent |
| failed | Node or tool execution failed | Red pulse plus error event link |
| delivered | Task outcome written by ledger deliver | Gold outer completion ring |

Never infer "running" from private Runtime reasoning. Only show it when Ledger
or runtime stream records it.

### Edge Types

| Relation type | UX meaning | Visual treatment |
|---|---|---|
| triggers | Activation-capable default path | Solid bright line |
| may_trigger | Conditional activation path | Dashed bright line |
| evaluates | Review path; handoff flows producer -> evaluator | Purple line with reverse-aware arrow marker |
| supports | Context assistance only | Thin muted blue line |
| constrains | Boundary or hard pressure | Thin red-orange line |
| complements | Parallel useful pairing | Thin teal line |
| augments | Adds capability or enhancement | Thin green line |

Activation-capable edges must be visually distinct from context-only edges.
`supports`, `constrains`, `complements`, and `augments` must never look like
direct activation routes.

### Edge Weights and Confidence

- Probability or necessity controls line thickness.
- Confidence controls opacity.
- Recent successful use adds a temporary glow.
- Recent skip or deferral adds a small tick marker near the target.
- Learning-proposed weight deltas appear only in Learning mode, not as current
  Policy truth.

## Interaction Model

### Selection

Single selection at a time:
- Node selection opens node inspector.
- Edge selection opens relation inspector.
- Handoff block selection opens block inspector.
- Policy gate selection opens legality inspector.
- Timeline event selection syncs scene, inspector, and camera focus.

Multi-select is reserved for future comparison. Do not overload v1.

### Node Inspector

Shows:
- Role, title, layer, domain, carries_soul flag.
- Current status and source event.
- Harness ref and skill ref.
- Inbound and outbound relation summary.
- Current task artifacts produced by this node.
- Current task handoffs sent/received.
- Candidate decisions involving this node.
- "Why active?" section showing predecessor, relation type, handoff ref, and
  activation_decision event.

Primary actions:
- Focus inbound.
- Focus outbound.
- Show in timeline.
- Copy source refs.

No execution controls in v1. The visualizer observes; it does not run nodes.

### Edge Inspector

Shows:
- from, to, relation type, weight/probability/necessity/strictness.
- Whether this relation can activate.
- Recent decisions using this edge.
- Samples count if available from learning data.
- Last handoff refs using this relation.
- Warning if edge is context-only.

### Policy Gate Inspector

Shows:
- Candidate: from -> to.
- Relation type.
- Legal choices: activate, skip, defer.
- Recorded decision and reason.
- Gate result: allowed, blocked, skipped, deferred.
- Missing facts when blocked:
  - no predecessor artifact
  - no context report
  - context-only relation
  - unresolved candidate
  - blocking evaluation open
  - missing soul ref for soul-bearing target

This panel is the main education surface for "Graph defines legality, Policy
interprets, Runtime executes, Ledger records."

## Handoff Block and Context Block Inspector

### Handoff Block Object

A handoff is a moving payload, not a decorative particle.

In scene:
- A compact rectangular/capsule block moves from producer to target along the
  relation path.
- Its color inherits the relation type.
- It carries a small stacked mark representing deliverable + context block.
- If `soul_ref` exists, add a subtle light slit marker.
- If digest chain is broken or absent, render as blocked/error state.

### Block Inspector Tabs

#### Summary

- Handoff ref.
- Timestamp.
- From, to, relation type.
- Focus.
- Artifact refs.
- Context digest.
- Previous block digests if present.

#### Deliverable

- Producer role.
- Artifact id, type, version, status.
- Content ref.
- Provenance ref if available.
- Readable preview of the first useful excerpt, with source link.

#### Context Block

Display the compressed context as structured sections:
- Decisions.
- Constraints.
- Assumptions.
- Open questions.
- Omitted context.
- Compression rationale.
- Quality checks.

Each retained item shows source and impact/risk/owner. The UI should not flatten
the context block into a paragraph because downstream action depends on its
structure.

#### Digest Chain

Shows:
- Current `context_block.context_digest`.
- `source.context_compression_report_ref`.
- `input_handoffs`.
- `inherited_artifact_refs`.
- Digest verification state: verified, missing, mismatch, or not checked.

If verification cannot run in the browser, show "not checked" rather than a
false green state.

## Realtime and Replay Controls

### Modes

| Mode | Purpose | Source |
|---|---|---|
| Demo | Show a bundled illustrative trace when no task is active | Generated fixture |
| Replay | Inspect an existing trace folder | Ledger files |
| Live | Follow a running trace | Polling or runtime event stream |

Use the same normalized snapshot schema for all three modes.

### Timeline

Controls:
- Play/pause.
- Step previous/next event.
- Speed: 0.5x, 1x, 2x, 4x.
- Jump to: first activation, first handoff, first blocked gate, convergence,
  delivery.
- Scrub bar with event ticks colored by event type.

Timeline event row:
- Timestamp.
- Event type.
- Actor or node.
- Short detail.
- Source ref.

When the user scrubs, the 3D scene should reconstruct state at that point,
not only move a cursor.

### Live Update Behavior

Live mode:
- Poll or stream normalized run snapshots.
- Show a small "synced" timestamp.
- If source stops updating, show "stale" after a threshold.
- If trace schema changes, show tolerant partial rendering with an error in the
  evidence panel.

Live mode must never hide replay. Operators need history to understand why the
current state exists.

## Filters and Search

Left rail filters:
- Node layer: Layer 1, Layer 2, Layer 3, learning/meta.
- Status: candidate, running, blocked, skipped, completed.
- Relation type.
- Activation-capable only.
- Context-only only.
- Has handoff.
- Has artifact.
- Has open question.
- Has missing digest or failed check.

Search:
- Role id.
- Artifact id.
- Handoff ref.
- Context digest prefix.
- Event id.
- Relation type.

Search results should focus the scene and timeline together.

## Accessibility

- Full keyboard navigation for search, timeline stepping, selection, inspector
  tabs, and reset camera.
- Provide a 2D table/list fallback for node, edge, event, and handoff data.
- Do not rely on color alone; use shape, line style, labels, and icons.
- Respect reduced motion by disabling continuous pulses and replacing moving
  handoff blocks with stepped positions.
- Ensure text panels meet WCAG AA contrast in both dark and light themes.
- Provide hover labels, but never require hover for essential information.
- Preserve readable font sizes inside panels; 3D labels can fade, inspector text
  cannot.
- Provide "focus mode" for users who want to isolate one node and its immediate
  evidence chain.

## Empty, Error, and Edge States

### No Trace Selected

Show graph structure, relation legend, and a prompt to load demo or choose a
trace. Do not fabricate run activity.

### Partial Trace

Render available facts and surface missing pieces:
- Missing context report.
- Missing artifact ref.
- Missing handoff file.
- Unknown node id.
- Unknown relation type.
- Unparseable YAML.

### Blocked Candidate

Show the candidate in the scene, attach the Policy gate, and list missing facts
in the inspector.

### Context-Only Relation Attempted as Activation

Show a red Policy gate and message:
"This relation carries context but cannot activate a node."

### Digest Mismatch

Keep the block visible but mark the digest chain as unverified. The user should
see the payload and the integrity problem together.

## Data Contract for UX

The UI should consume a normalized snapshot, not parse every raw file in every
component.

```yaml
org:
  nodes:
    - id: string
      title: string
      layer: number
      domain: string
      carries_soul: boolean
  edges:
    - from: string
      to: string
      relation_type: string
      weight: number|null
      activation_capable: boolean
run:
  task_id: string
  mode: live|replay|demo
  manifest: {}
  node_states: {}
  events: []
  artifacts: []
  handoffs: []
  candidates: []
  gates: []
  convergence: {}
learning:
  signals: []
  proposals: []
source:
  generated_at: string
  refs: []
  warnings: []
```

Component rule: every displayed operational fact should be able to point back
to `source.refs` or a concrete item in `events`, `artifacts`, `handoffs`, or
Graph files.

## MVP Acceptance Criteria

- Opens directly to a Three.js scene with the current Silicon Org graph.
- Shows 35 nodes and 122 relation edges from Graph files.
- Provides deterministic layer-based layout.
- Replays at least one trace from Ledger files.
- Animates node state changes from events.
- Animates handoff blocks from handoff files.
- Lets users inspect node, edge, Policy gate, handoff block, artifact, and
  context block data.
- Distinguishes activation-capable relations from context-only relations.
- Includes a timeline that can scrub the scene state.
- Includes reduced-motion and 2D fallback access.
- Does not provide graph editing or node execution controls in v1.

## Downstream Handoff Focus

- `ui-design-system`: define tokens for status, relation type, evidence source,
  digest verification, and theme inversion.
- `prototype`: prove deterministic 3D layout, handoff block animation, timeline
  scrubbing, and inspector readability with a real trace.
- `architect`: define trace-to-snapshot adapter, live/replay/demo source
  boundary, digest verification boundary, and future runtime stream hook.
- `senior-frontend`: build scene and panels from normalized snapshot rather
  than coupling UI components to raw YAML file layouts.

## Completion Report

```yaml
completion_report:
  what_was_done: >
    Produced an operator-facing UX specification for a Three.js realtime
    Silicon Org 3D operations visualizer, covering information architecture,
    first viewport, interaction model, node and relation status language,
    handoff/context block inspection, realtime/replay controls, accessibility,
    and visual semantics.
  key_decisions:
    - decision: "Use a deterministic 3D organization layout rather than free physics by default."
      rationale: "Operators need spatial memory and comparable runs more than organic motion."
    - decision: "Represent handoffs as inspectable moving blocks with deliverable and context_block slices."
      rationale: "The user's central need is to see block transfer and understand what each block contains."
    - decision: "Make Ledger-derived facts the only operational truth shown in the UI."
      rationale: "This preserves Silicon Org's auditability and avoids presenting Runtime private reasoning as fact."
    - decision: "Keep execution controls out of v1."
      rationale: "The first visualizer should observe, replay, and explain; node execution from UI would expand scope and risk."
  handoff_focus:
    - "Design system should turn the status and relation semantics into tokens and components."
    - "Prototype should validate canvas framing, deterministic layout, block motion, timeline scrubbing, and inspector readability."
    - "Architecture should normalize Graph and Ledger files into one snapshot contract before frontend components consume them."
  open_questions:
    - "Which trace should become the canonical demo fixture for v1?"
    - "Should live mode use polling first or wait for a runtime event stream adapter?"
  known_constraints:
    - "Do not introduce top-level concepts beyond Graph, Ledger, Policy, Runtime, and Learning."
    - "Do not imply context-only relations can activate nodes."
    - "Do not render operational facts that cannot be tied to Graph or Ledger sources."
    - "Do not make LangGraph or any execution adapter appear to be Silicon Org's organization brain."
  confidence_differential: 0.05
  dissent_if_alone: null
  iteration_context: null
```
