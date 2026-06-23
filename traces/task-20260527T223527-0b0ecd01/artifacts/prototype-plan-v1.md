# Prototype Plan — Three.js Silicon Org Operations Visualizer

## Prototype Question

Can a minimum Three.js frontend make Silicon Org understandable as a live operating system, not just a static graph, by showing:

- Graph structure: 35 agents and typed weighted relations.
- Runtime activity: nodes becoming active, completed, skipped, or blocked.
- Handoffs: visible block transfers between nodes.
- Context blocks: inspectable payloads containing retained decisions, constraints, assumptions, omissions, and digest references.
- Operating layers: Graph, Policy, Ledger, Runtime, and Learning as distinct but connected parts of the system.

The prototype should answer this visually and interactively before the team commits to production architecture, realtime transport, or a full design system.

## Minimum Runnable Demo

Build a throwaway local route or standalone dev app using Three.js. The first demo does not need true live execution; it can replay the current trace snapshot:

`traces/task-20260527T223527-0b0ecd01/`

The demo proves:

1. The current Silicon Org graph can be rendered in 3D without becoming unreadable.
2. Node state can be overlaid from Ledger trace files.
3. A handoff can animate from producer to consumer with an attached block payload.
4. Clicking a block can reveal digest-linked context summary.
5. The UI can distinguish activation-capable edges from context-only edges.
6. The five-concept operating model remains visible while the scene runs.

The demo does not need editing, auth, hosted deployment, graph mutation, production streaming, or model execution controls.

## Scene Model

### Spatial Layout

Use a layered 3D organization map:

- Center plane: Graph nodes grouped by role domain or layer.
- Upper ring: Policy gates and candidate decisions.
- Lower ring: Ledger artifacts, events, handoffs, and context reports.
- Side rail: Runtime execution status and playback controls.
- Back plane: Learning signals and future weight updates.

Recommended initial layout:

- `Layer 1` entry/intake nodes nearer the front-left.
- `Layer 2` execution/design/engineering nodes across the center.
- `Layer 3` quality/evaluation nodes nearer the back-right.
- Graph/Policy/Ledger/Runtime/Learning represented as stable anchor objects, not merely labels.

This is hardcoded for the prototype because the question is spatial readability, not automatic graph layout quality.

### Nodes

Each Silicon Org node is a small 3D object:

- Sphere or rounded capsule: agent node.
- Color family: domain/group.
- Emissive pulse: active/running.
- Solid glow: completed.
- Dimmed opacity: skipped/deferred.
- Red rim: blocked or failed.
- Small top badge: artifact count.
- Small bottom badge: model profile or runtime default when available.

For the first demo, render at least:

- `triage`
- `caveman`
- `prototype`
- `to-prd`
- `ux-researcher-designer`
- `architect`
- `ui-design-system`
- `senior-frontend`
- `delivery-prover`
- `code-reviewer`

Rendering all 35 nodes is preferred if labels remain legible.

### Edges

Edges must encode relation type accurately:

- `triggers`: bright solid line.
- `may_trigger`: dashed or pulsing line.
- `evaluates`: reverse-arrow review arc.
- `supports`: thin muted context line.
- `constrains`: caution-toned boundary line.
- `complements`: soft paired line.
- `augments`: additive accent line.

The prototype must not show `supports`, `constrains`, `complements`, or `augments` as direct activation edges.

### Handoff Blocks

A handoff is an animated block traveling from producer node to target node.

Block contents shown in the side inspector:

- `from`
- `to`
- `relation_type`
- `artifact_refs`
- `context_block.context_digest`
- retained decisions count
- retained constraints count
- assumptions count
- omitted context count
- quality checks

First replay block:

`handoffs/triage→prototype-20260527-144434.yaml`

It should travel from `triage` to `prototype`, then settle near `prototype` as an inspectable payload.

### Operating Layers

Show five concepts as persistent controls/anchors:

- Graph: static law, nodes and typed weighted relations.
- Policy: legality interpreter over Graph + Ledger.
- Ledger: durable facts from manifest, state, events, artifacts, handoffs.
- Runtime: executor applying legal actions and writing Ledger facts.
- Learning: feedback layer from trace outcomes and weight proposals.

Clicking a concept filters the scene:

- Graph highlights topology and edge types.
- Policy highlights candidates, gates, skipped/deferred decisions.
- Ledger highlights source files and event facts.
- Runtime highlights active execution timeline.
- Learning highlights weights and post-run improvement signals.

## Interaction Checklist

The first runnable demo should support:

- Orbit, pan, and zoom.
- Play/pause trace replay.
- Step forward/back one ledger event or handoff.
- Click node to open node inspector.
- Click edge to see relation type, probability/weight, and activation semantics.
- Click handoff block to see deliverable refs and context block summary.
- Toggle edge type visibility.
- Toggle operating layer: Graph, Policy, Ledger, Runtime, Learning.
- Filter by node state: active, completed, skipped, deferred, blocked.
- Reset camera to overview.

Nice but deferrable:

- Search node by name.
- Mini-map.
- Timeline scrubber with event density.
- Side-by-side artifact markdown preview.
- Live websocket/SSE feed.

## Data Snapshot Shape

The prototype should consume one normalized JSON object generated from the existing repo files. This avoids letting the frontend invent truth.

```json
{
  "task": {
    "task_id": "task-20260527T223527-0b0ecd01",
    "summary": "Build a Three.js realtime Silicon Org 3D operations visualizer",
    "context_block_ref": "org/CONTEXT_BLOCK.md",
    "context_block_sha256": "d82dc247c04f8cd2e797dd394ecd8d9cd927f1e194f2800d4fcf1e2be41f2a66"
  },
  "graph": {
    "nodes": [
      {
        "id": "triage",
        "title": "Triage",
        "domain": "intake",
        "layer": 1,
        "group": "entry"
      }
    ],
    "edges": [
      {
        "from": "triage",
        "to": "prototype",
        "relation_type": "may_trigger",
        "probability": 0.0,
        "activation_capable": true
      }
    ]
  },
  "ledger": {
    "nodes": {
      "triage": {
        "status": "completed",
        "artifact_refs": ["triage-analysis-v1"]
      },
      "prototype": {
        "status": "active",
        "artifact_refs": []
      }
    },
    "artifacts": [
      {
        "artifact_id": "triage-analysis-v1",
        "producer": "triage",
        "type": "analysis",
        "status": "draft",
        "ref": "artifacts/triage-analysis-v1.md"
      }
    ],
    "handoffs": [
      {
        "ref": "handoffs/triage→prototype-20260527-144434.yaml",
        "from": "triage",
        "to": "prototype",
        "relation_type": "may_trigger",
        "artifact_refs": ["triage-analysis-v1"],
        "context_digest": "a81927c22a1c9a22899cec3802a7a8f7f888ca7af0ebdc5bcc278901650fc445",
        "summary_counts": {
          "decisions": 3,
          "constraints": 4,
          "assumptions": 3,
          "open_questions": 0,
          "omitted_context": 4
        }
      }
    ],
    "events": [
      {
        "timestamp": "2026-05-27T14:44:35.011505+00:00",
        "type": "handoff_created",
        "from": "triage",
        "to": "prototype",
        "ref": "handoffs/triage→prototype-20260527-144434.yaml"
      }
    ]
  },
  "policy": {
    "candidates": [
      {
        "from": "triage",
        "to": "prototype",
        "relation_type": "may_trigger",
        "decision": "activate",
        "reason": "Feasibility of 3D interaction is unknown."
      }
    ]
  },
  "learning": {
    "signals": [],
    "proposals": []
  }
}
```

The first demo can hardcode this snapshot because it is testing the visualization model. Production should generate it from `ontology/*.yaml` and `traces/<task_id>/*`.

## Implementation Sketch

Recommended throwaway stack:

- Vite + React + TypeScript.
- Three.js via `@react-three/fiber` for scene composition.
- `@react-three/drei` for orbit controls, labels, and helpers.
- Lightweight in-memory playback store.
- Static snapshot JSON served from the app during prototype.

Prototype route:

`/prototype/silicon-org-ops-3d`

One command:

`pnpm dev`

If the repo does not already have a frontend app, create an isolated demo folder such as `apps/org-visualizer-prototype/` and mark it clearly as throwaway.

## What This Prototype Does Not Tell Us

- Whether true realtime streaming should use file polling, SSE, websocket, or LangGraph event hooks.
- Whether the final app should live inside this repo or as a separate package.
- Whether the 3D layout scales beyond 35 nodes and 122 edges after graph growth.
- Whether the same UI works for non-Silicon-Org multi-agent systems.
- Whether graph editing should ever be allowed from the UI.
- Whether model routing, token cost, and quality signals need a separate operational view.

## Recommended Next Step

Proceed with UX and architecture in parallel:

- UX should refine the mental model, labels, filters, and inspection hierarchy.
- Architect should define snapshot generation, live trace transport, and production data boundaries.
- Senior frontend should implement only after the prototype layout and data shape are accepted.

## Completion Report

```yaml
completion_report:
  what_was_done: >
    Produced a minimum viable prototype plan for a Three.js Silicon Org
    operations visualizer that can replay the current task trace, show node
    activity, animate handoff blocks, and inspect context-block payloads.
  key_decisions:
    - decision: Start with trace replay instead of true realtime transport.
      rationale: >
        The immediate uncertainty is whether the 3D operational model is
        understandable; realtime plumbing can follow once the visual semantics
        are proven.
    - decision: Treat Graph, Policy, Ledger, Runtime, and Learning as persistent scene layers.
      rationale: >
        The visualization exists to preserve Silicon Org's operating model, not
        to produce a generic agent network graphic.
    - decision: Make handoff context blocks inspectable.
      rationale: >
        The user's continuity concern depends on seeing what information moves
        between nodes, not only seeing that a transfer happened.
    - decision: Use a normalized snapshot object for the first demo.
      rationale: >
        This keeps frontend state grounded in Graph and Ledger facts while
        avoiding premature commitment to streaming architecture.
  handoff_focus:
    - Validate spatial readability before production implementation.
    - Preserve edge semantics, especially activation-capable versus context-only relations.
    - Use Ledger facts as the source of displayed runtime truth.
    - Keep context-block payloads visible and inspectable.
  open_questions:
    - Which frontend package or app location should host the throwaway demo?
    - Should the first runnable demo render all 35 nodes or a focused operational subset by default?
    - Should live updates initially use trace polling, SSE, websocket, or LangGraph runtime events?
  known_constraints:
    - Do not make the frontend the source of truth for legality or runtime state.
    - Do not imply supports, constrains, complements, or augments directly activate nodes.
    - Do not replace Graph, Ledger, Policy, Runtime, or Learning.
    - Keep the prototype clearly disposable until its question is answered.
  confidence_differential: 0.05
  dissent_if_alone: null
  iteration_context: null
```
