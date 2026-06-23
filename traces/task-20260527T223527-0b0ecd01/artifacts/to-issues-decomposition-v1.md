# Issue Decomposition: Three.js Silicon Org Operations Visualizer

## Source

Parent artifact: `to-prd-prd-v1`

This breakdown converts the PRD into independently grabbable vertical slices. Each slice is shaped so a completed issue is demonstrable on its own and preserves the central constraint: the visualizer projects Graph and Ledger facts; it does not become a new source of truth.

## Implementation Slices

### 1. Snapshot Exporter For One Trace

Type: AFK

Blocked by: None - can start immediately

User stories covered: Silicon Org Builder, Runtime Operator, Reviewer / Quality Gate Owner

What to build:

Create a read-only snapshot exporter that loads the current Graph files and one selected trace folder, then emits a normalized `silicon_org.visualizer.snapshot.v1` JSON document. The exporter must include Graph nodes and edges, run manifest/state, events, artifacts, context reports, handoffs, policy candidates/gates when recorded, learning signals when present, and source references for displayed facts.

Acceptance criteria:

- [ ] Export command can generate a snapshot for `traces/task-20260527T223527-0b0ecd01/`.
- [ ] Snapshot contains all nodes from `ontology/nodes.yaml` and all edges from `ontology/relations.yaml`.
- [ ] Snapshot includes manifest, state, artifact index, context report index, handoff trail, events, and parse errors or warnings.
- [ ] Each normalized object includes at least one source reference or an explicit `not_recorded`/`invalid` marker.
- [ ] Malformed optional files produce snapshot errors without preventing a nonblank export.
- [ ] Unit tests cover graph loading, trace loading, source refs, and missing optional data.

### 2. Local Snapshot Server And Polling API

Type: AFK

Blocked by: Slice 1

User stories covered: Runtime Operator, Silicon Org Builder

What to build:

Wrap the snapshot exporter in a local read-only server bound to `127.0.0.1` by default. Expose endpoints for org metadata, trace list, full snapshot, incremental events, artifact fetch, and health. The server should support local polling first and leave a clean upgrade path to SSE/WebSocket later.

Acceptance criteria:

- [ ] `GET /api/health` returns server status and selected workspace root.
- [ ] `GET /api/org` returns graph metadata and counts.
- [ ] `GET /api/runs` lists discoverable trace folders with task id and summary when available.
- [ ] `GET /api/runs/:task_id/snapshot` returns the same normalized contract as Slice 1.
- [ ] `GET /api/runs/:task_id/events?after=<sequence>` returns deterministic event batches with stable sequence numbers.
- [ ] Local polling reflects a trace file change within 2 seconds in development.
- [ ] The server is read-only and does not mutate Graph, Ledger, Policy, Runtime, or Learning files.

### 3. Graph Normalization And Semantic Styling Metadata

Type: AFK

Blocked by: Slice 1

User stories covered: Graph Designer, Runtime Operator

What to build:

Normalize Silicon Org graph semantics into frontend-ready node, edge, layout, and style metadata. This includes deterministic grouping, activation-capable relation flags, reverse-evaluates affordance, edge weights/confidence where available, and context-only styling for supports/constrains/complements/augments/precedes.

Acceptance criteria:

- [ ] Every node has stable id, title, layer/domain/group hints, model profile if known, and source refs.
- [ ] Every edge has stable id, relation type, activation capability, visual lane, thickness/opacity inputs, and source ref.
- [ ] `triggers`, `may_trigger`, and reverse-aware `evaluates` are marked as activation/evaluation-capable.
- [ ] `supports`, `constrains`, `complements`, `augments`, and `precedes` are never marked as direct activation paths.
- [ ] Reloading the same snapshot produces the same position hints within deterministic ordering.
- [ ] Tests assert current graph counts and relation-type classification.

### 4. Three.js Scene Skeleton With Five Operating Surfaces

Type: AFK

Blocked by: Slices 1 and 3

User stories covered: Silicon Org Builder, Graph Designer

What to build:

Create the first runnable frontend app using Vite, TypeScript, and Three.js or React Three Fiber. Render a nonblank full-bleed 3D scene with agent nodes, typed edges, and persistent Graph, Policy, Ledger, Runtime, and Learning surfaces. The scene should use deterministic layout, not uncontrolled physics.

Acceptance criteria:

- [ ] Running the app renders a nonblank Three.js canvas from a snapshot.
- [ ] All current graph nodes are represented, or a focused subset is clearly labeled as demo mode while counts remain visible.
- [ ] Typed edges render with distinct styles and a visible relation legend.
- [ ] Five operating surfaces are visible in the first viewport.
- [ ] Orbit, pan, zoom, focus selected object, and reset camera controls work.
- [ ] Desktop and mobile layouts avoid critical overlap between canvas, top bar, inspector, and timeline.

### 5. Node Runtime State Projection

Type: AFK

Blocked by: Slices 2 and 4

User stories covered: Runtime Operator, Reviewer / Quality Gate Owner

What to build:

Project Ledger node states onto the 3D scene and details panel. Nodes should show idle, candidate, activated, running, completed, skipped, deferred, failed, approved, and delivered where the trace records those states. Active/running nodes should have a visible pulse or glow, and completed nodes should expose timestamps and artifact counts.

Acceptance criteria:

- [ ] Loading a trace shows node states matching `state.yaml`.
- [ ] Active or running nodes visibly pulse or glow.
- [ ] Completed nodes show completed timestamp and artifact count in the inspector.
- [ ] Unknown or missing states are displayed as `not recorded` rather than inferred.
- [ ] Selecting a node highlights related inbound/outbound edges, handoffs, artifacts, context reports, and events.
- [ ] Tests verify state mapping from normalized snapshot to UI status names.

### 6. Handoff Block Animation And Context Inspector

Type: AFK

Blocked by: Slices 2, 4, and 5

User stories covered: Reviewer / Quality Gate Owner, Silicon Org Builder

What to build:

Render handoff blocks as first-class 3D objects moving from producer to target along the matching edge. Clicking a block opens an inspector showing deliverable refs, artifact metadata, relation type, focus, timestamp, context digest, previous block chain, retained decisions, constraints, assumptions, open questions, omitted context, compression rationale, quality checks, and optional `soul_ref`.

Acceptance criteria:

- [ ] Each handoff in the selected trace can create a block with stable id and source ref.
- [ ] At least one replay path animates a handoff block from producer to target.
- [ ] Clicking a handoff block opens a readable inspector with context digest and digest chain.
- [ ] The inspector shows retained context counts and expanded sections for decisions, constraints, assumptions, open questions, omitted context, and quality checks when present.
- [ ] Handoffs with malformed context blocks show an invalid marker and parse warning.
- [ ] The visual block does not imply activation when its relation type is context-only.

### 7. Policy Gates, Candidate Decisions, And Blocked Reasons

Type: AFK

Blocked by: Slices 2, 3, and 5

User stories covered: Runtime Operator, Graph Designer

What to build:

Add a Policy surface that displays activation candidates, legal choices, selected decisions, skipped/deferred states, blocked reasons, and convergence blockers when recorded by Ledger. The visualizer should explain that Policy interprets Graph plus Ledger and that context-only relations cannot activate nodes by themselves.

Acceptance criteria:

- [ ] Policy panel lists trigger, may-trigger, and reverse-evaluates candidates when present.
- [ ] Decisions show `activate`, `skip`, `defer`, or `undecided` using Ledger facts.
- [ ] Blocked reasons use recorded text such as missing artifact, missing context report, context-only relation, unresolved candidate, blocking evaluation, malformed handoff, or unresolved artifact status.
- [ ] Selecting a Policy gate highlights the source node, target node, relation edge, and Ledger event/source ref.
- [ ] Context-only edge types are labeled as non-activation pressure or evidence.
- [ ] Convergence blockers are displayed without allowing the UI to override them.

### 8. Ledger Timeline, Replay, And Live Poll Reconciliation

Type: AFK

Blocked by: Slices 2, 5, and 6

User stories covered: Runtime Operator, Silicon Org Builder

What to build:

Build the bottom Ledger timeline with play/pause, reset, step forward/back, event markers, selected-event highlighting, and live polling reconciliation. Replay and polling should use the same normalized event model. Repeated events must be idempotent and should not duplicate scene objects.

Acceptance criteria:

- [ ] Timeline lists normalized events in timestamp/sequence order.
- [ ] Replay changes at least three node states over time for the selected trace.
- [ ] Replay animates at least one handoff block.
- [ ] Selecting an event highlights related node, edge, handoff, artifact, or policy gate.
- [ ] Live polling updates the scene within 2 seconds of local trace changes.
- [ ] Polling failure keeps the last snapshot visible and shows stale-state age.
- [ ] Reset returns the scene to the beginning of the replay.

### 9. Object Inspectors, Filters, And Evidence Copy

Type: AFK

Blocked by: Slices 4, 5, 6, 7, and 8

User stories covered: Reviewer / Quality Gate Owner, Graph Designer, Runtime Operator

What to build:

Complete the right-side inspector and left-side controls for nodes, edges, handoffs, artifacts, context blocks, policy gates, learning signals, relation filters, node-state filters, concept layer toggles, and snapshot export/copy for debugging.

Acceptance criteria:

- [ ] Clicking a node, edge, handoff block, artifact, policy gate, Ledger event, or Learning marker opens an object-specific inspector.
- [ ] Inspectors show source category and source ref for operational facts.
- [ ] User can filter or dim by relation type, node state, layer/domain, and concept surface.
- [ ] User can copy or export the normalized snapshot used by the frontend.
- [ ] Keyboard navigation can reach panels and controls, and selected canvas objects have mirrored text details.
- [ ] Missing optional facts render as `not recorded`, not guessed.

### 10. Learning Surface And Graph Evolution Signals

Type: AFK

Blocked by: Slices 1, 3, and 4

User stories covered: Graph Designer, Silicon Org Builder

What to build:

Add the Learning surface that displays learning signals and proposals when trace or index data exists. Show edge weight deltas, confidence changes, skip costs, model-routing observations, graph-topologist proposals, and HRBP skill signals as conservative suggestions rather than Policy overrides.

Acceptance criteria:

- [ ] Learning surface renders even when no signals exist, with `not recorded` empty state.
- [ ] When learning signals/proposals exist, they link back to edge/node/model/source refs where possible.
- [ ] Edge deltas and confidence changes are visually associated with graph edges without changing legal edge behavior.
- [ ] The UI explicitly marks learning proposals as advisory.
- [ ] Tests cover empty learning data and at least one populated signal fixture.

### 11. Demo Trace Selection And First-Run Experience

Type: AFK

Blocked by: Slices 2, 4, and 8

User stories covered: Silicon Org Builder, Runtime Operator

What to build:

Provide demo mode for users who do not have an active runtime. The app should select or list available trace folders, load a canonical trace by default, and expose a clear replay/reset path.

Acceptance criteria:

- [ ] App can run with no active Silicon Org task.
- [ ] App loads a canonical demo trace by default or shows a trace selector populated from `/api/runs`.
- [ ] User can switch traces without restarting the app.
- [ ] If no trace exists, UI shows actionable empty state and still renders Graph-only mode.
- [ ] Demo mode is visibly labeled so it is not mistaken for live runtime state.

### 12. Verification Harness And Delivery Proof

Type: AFK

Blocked by: Slices 1 through 11

User stories covered: Silicon Org Builder, Reviewer / Quality Gate Owner

What to build:

Add automated and manual verification for the full visualizer. This should include snapshot tests, graph-count tests, replay behavior tests, nonblank canvas checks, desktop/mobile screenshots, source-ref coverage checks, and delivery proof documentation.

Acceptance criteria:

- [ ] Automated tests verify snapshot schema, current graph counts, relation classifications, and trace normalization.
- [ ] Browser verification confirms a nonblank Three.js canvas.
- [ ] Browser verification covers at least desktop and 390px mobile widths.
- [ ] Canvas and panels show no critical overlap in verified viewports.
- [ ] Replay test confirms state changes and at least one handoff animation.
- [ ] Source traceability check confirms at least 95% of visible operational facts have source refs or explicit `not_recorded`.
- [ ] Delivery notes include run commands, known limitations, and follow-up issues.

## Dependency Order

1. Slice 1: Snapshot Exporter For One Trace
2. Slice 3: Graph Normalization And Semantic Styling Metadata
3. Slice 2: Local Snapshot Server And Polling API
4. Slice 4: Three.js Scene Skeleton With Five Operating Surfaces
5. Slice 5: Node Runtime State Projection
6. Slice 6: Handoff Block Animation And Context Inspector
7. Slice 7: Policy Gates, Candidate Decisions, And Blocked Reasons
8. Slice 8: Ledger Timeline, Replay, And Live Poll Reconciliation
9. Slice 10: Learning Surface And Graph Evolution Signals
10. Slice 11: Demo Trace Selection And First-Run Experience
11. Slice 9: Object Inspectors, Filters, And Evidence Copy
12. Slice 12: Verification Harness And Delivery Proof

## Follow-Ups

- Decide whether the first production app lives under `apps/org-visualizer/`, `visualizer/`, or an existing frontend package.
- Decide the canonical demo trace after the current run converges.
- Define the first live transport upgrade after polling: SSE, WebSocket, or LangGraph event bridge.
- Decide whether graph editing will remain permanently out of scope or become a separate authenticated control-plane product.
- Define retention and privacy rules for artifact previews if future versions expose full artifact text in the inspector.

## Cross-Cut Acceptance Checklist

- [ ] Ledger remains the source of truth for operational state.
- [ ] Rendering components consume normalized snapshots and do not parse raw YAML directly.
- [ ] The UI never presents private runtime reasoning as fact unless recorded in Ledger, artifacts, handoffs, or reports.
- [ ] Graph, Policy, Ledger, Runtime, and Learning remain visible as distinct operating surfaces.
- [ ] Context-only edges are never styled as direct activation paths.
- [ ] Handoff blocks expose context digest and retained context, not just movement.
- [ ] Missing optional data renders as `not recorded`.
- [ ] The app supports trace replay without an active runtime.
- [ ] Local polling is compatible with future streaming without changing the frontend state schema.
- [ ] Verification includes data, UI, replay, source-ref, desktop, and mobile checks.

## Completion Report

```yaml
completion_report:
  what_was_done: >
    Decomposed the Three.js Silicon Org operations visualizer PRD into
    independently grabbable implementation slices covering snapshot export,
    local polling server, graph normalization, Three.js scene, node state
    projection, handoff/context-block inspection, policy gates, ledger replay,
    learning surface, demo mode, inspectors, and verification.
  key_decisions:
    - decision: "Start implementation with a normalized snapshot exporter."
      rationale: "It protects Ledger as source of truth and gives frontend, server, replay, and verification a stable contract."
    - decision: "Separate graph semantic normalization from scene rendering."
      rationale: "Activation capability and context-only relation semantics are Policy/Graph facts that should be tested before visual styling."
    - decision: "Make handoff/context-block inspection a dedicated vertical slice."
      rationale: "The user's continuity concern depends on seeing block contents and digest chains, not only animated movement."
    - decision: "Use polling and replay through one normalized event model."
      rationale: "This supports the MVP realtime requirement while preserving an upgrade path to SSE, WebSocket, or LangGraph events."
  handoff_focus:
    - "Senior frontend can start after snapshot/export and graph semantic fixtures exist."
    - "API/server work should keep all endpoints read-only in v1."
    - "Delivery proof should verify nonblank canvas, mobile/desktop layout, replay, handoff animation, and source traceability."
  open_questions:
    - "Where should the production visualizer app live in the repository?"
    - "Which trace should be the canonical demo trace once this run converges?"
    - "Which live transport should follow polling: SSE, WebSocket, or LangGraph event bridge?"
  known_constraints:
    - "Do not make the visualizer a source of truth for Graph, Policy, Ledger, Runtime, or Learning."
    - "Do not show supports, constrains, complements, augments, or precedes as direct activation edges."
    - "Do not add graph editing, policy decisions, artifact approval, or node execution controls in MVP."
  confidence_differential: 0.04
  dissent_if_alone: null
  iteration_context: null
```
