# UI Design System Spec: Silicon Org 3D Operations Visualizer

## Purpose

Define the visual language, tokens, component contracts, states, themes, and
accessibility rules for the Three.js Silicon Org operations visualizer.

The design system must make the org readable as an operating system:

- Graph is the static law: nodes, typed edges, weights, legality shape.
- Policy is the interpreter: gates, candidates, activate/skip/defer decisions.
- Ledger is fact: events, state, artifacts, handoffs, context reports, digests.
- Runtime is execution: active work and writes to Ledger.
- Learning is feedback: weight deltas, routing signals, graph proposals.

The UI observes and explains. It does not edit Graph, execute nodes, approve
artifacts, or replace Policy.

## Token Architecture

Tokens are split into semantic tokens and component tokens. Three.js materials
and DOM panels must read the same semantic layer so scene, inspector, filters,
and timeline never drift.

```ts
type ThemeMode = "dark" | "light";

type VisualizerTokens = {
  color: ColorTokens;
  surface: SurfaceTokens;
  text: TextTokens;
  node: NodeTokens;
  edge: EdgeTokens;
  block: HandoffBlockTokens;
  gate: PolicyGateTokens;
  concept: ConceptTokens;
  timeline: TimelineTokens;
  motion: MotionTokens;
  space: SpaceTokens;
  radius: RadiusTokens;
  shadow: ShadowTokens;
  z: ZIndexTokens;
};
```

## Color Tokens

### Core Palette

Use a dark operations-console theme by default. Avoid a one-hue dashboard. The
palette deliberately mixes cyan, amber, violet, green, red, and neutral ink so
relation type and state are distinguishable without relying on one color family.

```css
:root {
  --so-black: #05070a;
  --so-ink-950: #0b1017;
  --so-ink-900: #111827;
  --so-ink-800: #1d2733;
  --so-ink-700: #334155;
  --so-ink-500: #64748b;
  --so-ink-300: #cbd5e1;
  --so-ink-100: #f1f5f9;
  --so-white: #ffffff;

  --so-cyan-500: #22d3ee;
  --so-blue-500: #3b82f6;
  --so-violet-500: #8b5cf6;
  --so-amber-500: #f59e0b;
  --so-green-500: #22c55e;
  --so-red-500: #ef4444;
  --so-orange-500: #f97316;
  --so-teal-500: #14b8a6;
  --so-lime-500: #84cc16;
  --so-gold-500: #eab308;
}
```

### Theme Semantic Tokens

```css
[data-theme="dark"] {
  --surface-canvas: #05070a;
  --surface-panel: rgba(11, 16, 23, 0.92);
  --surface-panel-solid: #0b1017;
  --surface-raised: #111827;
  --surface-inset: #070b10;
  --surface-hover: #1d2733;
  --surface-selected: rgba(34, 211, 238, 0.14);

  --text-primary: #f8fafc;
  --text-secondary: #cbd5e1;
  --text-muted: #94a3b8;
  --text-disabled: #64748b;
  --text-inverse: #0b1017;

  --border-subtle: rgba(148, 163, 184, 0.18);
  --border-strong: rgba(203, 213, 225, 0.36);
  --focus-ring: #22d3ee;
}

[data-theme="light"] {
  --surface-canvas: #f8fafc;
  --surface-panel: rgba(255, 255, 255, 0.94);
  --surface-panel-solid: #ffffff;
  --surface-raised: #f1f5f9;
  --surface-inset: #e2e8f0;
  --surface-hover: #e0f2fe;
  --surface-selected: rgba(37, 99, 235, 0.12);

  --text-primary: #0f172a;
  --text-secondary: #334155;
  --text-muted: #64748b;
  --text-disabled: #94a3b8;
  --text-inverse: #ffffff;

  --border-subtle: rgba(15, 23, 42, 0.14);
  --border-strong: rgba(15, 23, 42, 0.28);
  --focus-ring: #2563eb;
}
```

## Concept Tokens

The five operating concepts are persistent anchors in the scene and the left
rail. They are not decorative labels; they are filter modes and explanatory
planes.

| Concept | Meaning | Color | Three.js form | DOM icon cue |
|---|---|---|---|---|
| Graph | Static law and topology | `--concept-graph` #22d3ee | Central node-edge lattice | Network |
| Policy | Legality interpreter | `--concept-policy` #f59e0b | Translucent gates/checkpoints | Gavel/check |
| Ledger | Durable facts | `--concept-ledger` #3b82f6 | Horizontal evidence plane | Book/database |
| Runtime | Executor activity | `--concept-runtime` #22c55e | Vertical activity spine | Play/pulse |
| Learning | Feedback and weight updates | `--concept-learning` #8b5cf6 | Outer halo | Loop/spark |

```css
:root {
  --concept-graph: #22d3ee;
  --concept-policy: #f59e0b;
  --concept-ledger: #3b82f6;
  --concept-runtime: #22c55e;
  --concept-learning: #8b5cf6;
}
```

## Node Status Tokens

Status labels must be identical across scene, inspector, filters, and timeline.

| Status | Meaning | Scene treatment | DOM treatment |
|---|---|---|---|
| idle | Exists in Graph, no run activity | Low-opacity solid sphere/capsule | Neutral chip |
| candidate | Policy can decide | Amber rim, no pulse | Amber outlined chip |
| activated | Ledger records activation | Bright outline, static | Cyan chip |
| running | Execution in progress | Slow breathing emissive pulse | Live pulse dot |
| completed | Required outputs registered | Stable fill, artifact badge | Green check chip |
| skipped | Runtime explicitly skipped | Muted fill, diagonal slash | Muted slash chip |
| deferred | Candidate kept for later | Amber paused ring | Paused amber chip |
| blocked | Missing required facts/gate blocked | Red gate marker | Red warning chip |
| evaluating | Evaluator reviewing artifact | Violet review beam | Violet review chip |
| approved | Artifact/evaluation approved | Green check accent | Approved chip |
| failed | Execution failed | Red pulse + error link | Error chip |
| delivered | Outcome written by deliver | Gold completion ring | Delivered chip |
| invalid | Malformed/missing source | Red-orange broken outline | Invalid source chip |

```css
:root {
  --node-idle: #64748b;
  --node-candidate: #f59e0b;
  --node-activated: #22d3ee;
  --node-running: #22c55e;
  --node-completed: #16a34a;
  --node-skipped: #64748b;
  --node-deferred: #fbbf24;
  --node-blocked: #ef4444;
  --node-evaluating: #8b5cf6;
  --node-approved: #22c55e;
  --node-failed: #dc2626;
  --node-delivered: #eab308;
  --node-invalid: #f97316;
}
```

### Node Material Rules

```ts
type NodeMaterialState = {
  status: NodeStatus;
  baseColor: string;
  emissiveColor: string | null;
  opacity: number;
  rimColor: string | null;
  rimWidthPx: number;
  pulse: "none" | "slow" | "error";
  badge: "none" | "artifactCount" | "warning" | "check" | "paused";
};
```

Rules:

- `running` pulse period: 1600 ms, opacity oscillation 0.74 to 1.0.
- `failed` pulse period: 700 ms, max two loops, then stable error state.
- `candidate` and `deferred` never pulse; they are Policy states, not work.
- `completed` shows artifact count only when Ledger has artifact refs.
- `running` cannot be inferred from private reasoning; require Ledger/runtime
  stream source and mark stream-only status as ephemeral in inspector.

## Edge Type Tokens

Activation-capable and context-only relations must be visually impossible to
confuse.

| Relation | Activation capable | Color | Line style | Arrow behavior |
|---|---:|---|---|---|
| triggers | yes | #22d3ee | solid, bright | from -> to |
| may_trigger | yes | #38bdf8 | dashed, bright | from -> to |
| evaluates | conditional review | #8b5cf6 | solid review arc | handoff producer -> evaluator |
| supports | no | #60a5fa | thin muted | no activation arrow |
| constrains | no | #f97316 | thin caution | no activation arrow |
| complements | no | #14b8a6 | thin paired | no activation arrow |
| augments | no | #84cc16 | thin additive | no activation arrow |
| precedes | no by default | #94a3b8 | dotted order line | order tick only |

```css
:root {
  --edge-triggers: #22d3ee;
  --edge-may-trigger: #38bdf8;
  --edge-evaluates: #8b5cf6;
  --edge-supports: #60a5fa;
  --edge-constrains: #f97316;
  --edge-complements: #14b8a6;
  --edge-augments: #84cc16;
  --edge-precedes: #94a3b8;
}
```

### Edge Material Rules

```ts
type EdgeVisualState = {
  relationType: RelationType;
  activationCapable: boolean;
  linePattern: "solid" | "dash" | "dot";
  color: string;
  opacity: number;
  thicknessPx: number;
  arrow: "activation" | "reviewReverseAware" | "none" | "orderTick";
  recentUseGlow: boolean;
  decisionTick: "none" | "activated" | "skipped" | "deferred" | "blocked";
};
```

Rules:

- `triggers`, `may_trigger`, and reverse-aware `evaluates` may carry bright
  arrows; context-only relation types never do.
- Probability/necessity controls thickness, clamped between 1 px and 5 px.
- Confidence controls opacity, clamped between 0.18 and 1.0.
- Recent successful handoff adds glow for 1800 ms during replay/live update.
- Skip/defer/block decisions appear as small target-side tick markers.

## Policy Gate Tokens

Policy gates are first-class objects placed between a producer and candidate
target when a decision exists or a legality check blocks activation.

| Gate state | Color | Shape | Meaning |
|---|---|---|---|
| pending | Amber | Thin octagon | Candidate awaits activate/skip/defer |
| allowed | Green | Open octagon | Activation legal and chosen |
| skipped | Slate | Slashed octagon | Runtime chose skip |
| deferred | Amber | Paused octagon | Runtime chose defer |
| blocked | Red | Closed octagon | Missing facts or illegal relation |
| advisory | Violet | Soft review diamond | Non-blocking evaluator concern |

Policy gate labels:

- `activate`
- `skip`
- `defer`
- `blocked: context-only relation`
- `blocked: missing artifact`
- `blocked: missing context report`
- `blocked: unresolved candidate`
- `blocked: blocking evaluation open`

## Handoff Block Tokens

A handoff block is a payload object. It is not a particle trail.

### Object Anatomy

```text
┌──────────────────────────────┐
│ relation stripe              │  color = relation type
├────────────┬────────┬────────┤
│ artifact   │ ctx    │ digest │  stacked payload slices
├────────────┴────────┴────────┤
│ optional soul light slit      │
└──────────────────────────────┘
```

| Slice | Token | Scene mark | Inspector tab |
|---|---|---|---|
| Relation | `--block-relation-stripe` | leading color stripe | Summary |
| Deliverable | `--block-deliverable` | document slice | Deliverable |
| Context | `--block-context` | layered cards | Context Block |
| Digest | `--block-digest` | hash pin | Digest Chain |
| Soul | `--block-soul` | narrow light slit | Summary evidence |
| Error | `--block-error` | broken hash/rim | Digest Chain |

```css
:root {
  --block-deliverable: #3b82f6;
  --block-context: #f59e0b;
  --block-digest: #8b5cf6;
  --block-soul: #eab308;
  --block-error: #ef4444;
}
```

### Block States

| State | Meaning | Treatment |
|---|---|---|
| queued | Handoff file exists but replay time not reached | Dim block at source |
| moving | Replay/live event in flight | Moves on edge arc with orientation |
| arrived | Transfer complete | Settles near target node |
| selected | User selected block | White/cyan outline and inspector sync |
| verified | Digest checked | Green hash mark |
| not_checked | Browser cannot verify | Neutral hash mark |
| missing_digest | Digest missing | Orange broken hash |
| mismatch | Digest mismatch | Red broken hash and warning |

Motion:

- Default travel duration: 1200 ms for replay, scaled by timeline speed.
- Reduced motion: no continuous travel; block appears at 0%, 50%, 100% stepped
  positions when stepping through events.
- Selection freezes the selected block in place while inspector is open.

## Typography

Use a compact operations typography scale. Do not use hero-scale type inside
panels, chips, toolbars, timeline rows, or 3D labels.

```css
:root {
  --font-sans: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-mono: "SFMono-Regular", Consolas, "Liberation Mono", monospace;

  --text-xs: 11px;
  --text-sm: 12px;
  --text-md: 14px;
  --text-lg: 16px;
  --text-xl: 20px;

  --line-tight: 1.2;
  --line-normal: 1.45;
  --line-relaxed: 1.6;
}
```

3D label rules:

- Node label max length: 22 characters, middle-ellipsize role ids.
- Labels fade by distance but remain available in inspector/search.
- Labels use a billboard plane or CSS2DRenderer with `--text-xs`.
- Never place long context text inside the Three.js scene.

## Spacing, Radius, Elevation

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;

  --radius-1: 4px;
  --radius-2: 6px;
  --radius-3: 8px;
  --radius-pill: 999px;

  --shadow-panel: 0 16px 40px rgba(0, 0, 0, 0.32);
  --shadow-focus: 0 0 0 3px color-mix(in srgb, var(--focus-ring), transparent 68%);
}
```

Component radius rule: panels and repeated cards use 6 px or 8 px radius;
buttons and chips may use pill radius only for compact status controls.

## Component Specifications

### App Shell

Purpose: fixed operational surface with no landing page.

Regions:

- Top bar: task id, mode, convergence, source truth, model profile.
- Left rail: run summary, gates, filters, search, concept toggles.
- Scene: full-height Three.js canvas with overlay legends.
- Inspector: selected object details with evidence and source refs.
- Timeline: event replay and scrub controls.

States:

- `noTrace`: graph visible, no run activity fabricated.
- `loading`: skeleton panels, scene anchors visible when graph loaded.
- `ready`: normal operation.
- `partial`: source warnings visible, available facts rendered.
- `stale`: live source older than configured threshold.
- `error`: fatal adapter error with source ref and retry.

### Top Bar

Elements:

- Task id monospace chip.
- Mode segmented control: Demo, Replay, Live.
- Convergence badge.
- Source truth badge: Graph + Ledger.
- Model profile chip if available.
- Theme icon button.
- Reduced motion icon toggle.

Convergence badge states:

- Running: cyan outlined.
- Blocked: red filled.
- Converged: green filled.
- Delivered: gold filled.
- Incomplete: slate outlined.

### Concept Toggle Strip

Controls five concept filters:

- Graph highlights nodes and typed edges.
- Policy highlights gates and candidate decisions.
- Ledger highlights evidence plane, source refs, events, artifacts, handoffs.
- Runtime highlights activity spine and node execution timeline.
- Learning highlights outer halo, weight deltas, proposals, confidence.

Each toggle uses icon + text in the left rail; in compact mode use icon buttons
with tooltips.

### Node Glyph

Three.js component:

```ts
type NodeGlyphProps = {
  id: string;
  title: string;
  layer: 1 | 2 | 3 | "meta" | null;
  domain: string | null;
  status: NodeStatus;
  artifactCount: number;
  carriesSoul: boolean;
  selected: boolean;
  focused: boolean;
  sourceRefs: string[];
};
```

Visual parts:

- Body mesh: sphere/capsule.
- Rim mesh: status/selection ring.
- Badge planes: artifact count, warning, approved, paused.
- Label plane: role id.
- Soul marker: small gold slit only when `carriesSoul` true.

Interaction:

- Click selects node.
- Double-click focuses camera.
- Keyboard selection mirrors search/timeline focus.

### Edge Glyph

Three.js component:

```ts
type EdgeGlyphProps = {
  from: string;
  to: string;
  relationType: RelationType;
  activationCapable: boolean;
  weight: number | null;
  confidence: number | null;
  selected: boolean;
  filtered: boolean;
  decisionTick?: "activated" | "skipped" | "deferred" | "blocked";
};
```

Visual parts:

- Curve line: deterministic arc between nodes.
- Arrow/tick: activation arrow, review marker, or order tick.
- Weight band: subtle thickness.
- Decision tick near target.

Context-only safeguards:

- Context-only edges use no bright activation arrow.
- Inspector repeats `Cannot activate` warning.
- If a context-only activation attempt appears in Ledger, attach red Policy gate.

### Policy Gate

Component:

```ts
type PolicyGateProps = {
  candidateId: string;
  from: string;
  to: string;
  relationType: RelationType;
  state: "pending" | "allowed" | "skipped" | "deferred" | "blocked" | "advisory";
  legalChoices: Array<"activate" | "skip" | "defer">;
  reason?: string;
  missingFacts?: string[];
  sourceRef: string;
};
```

Scene:

- Gate sits halfway between from/to, offset upward from edge arc.
- Blocked gate anchors a red line to the missing target or evidence plane.

Inspector:

- Shows why a node may or may not activate.
- Lists legal choices and recorded decision.
- Shows source ref to event, handoff, or validation output.

### Handoff Block

Component:

```ts
type HandoffBlockProps = {
  ref: string;
  from: string;
  to: string;
  relationType: RelationType;
  artifactRefs: string[];
  contextDigest: string | null;
  previousDigests: string[];
  focus: string;
  timestamp: string;
  state: HandoffBlockState;
  digestState: "verified" | "not_checked" | "missing" | "mismatch";
  carriesSoul: boolean;
};
```

Scene:

- Compact rectangular block with stacked visible slices.
- Color stripe inherits relation type.
- Context and digest slices are always visible, even if empty/error.
- Selected block expands 1.08x and pins a short label with digest prefix.

Inspector:

- Summary tab: ref, timestamp, from/to, relation type, focus, digest.
- Deliverable tab: artifact refs, type, version, status, content refs.
- Context Block tab: decisions, constraints, assumptions, open questions,
  omitted context, rationale, quality checks.
- Digest Chain tab: current digest, input handoffs, inherited artifacts,
  verification status.

### Inspector Panel

Panel contract:

```ts
type InspectorSelection =
  | { kind: "empty" }
  | { kind: "node"; id: string }
  | { kind: "edge"; id: string }
  | { kind: "gate"; id: string }
  | { kind: "handoff"; ref: string }
  | { kind: "artifact"; id: string }
  | { kind: "event"; sequence: number }
  | { kind: "concept"; concept: OperatingConcept };
```

Layout:

- Header: selected object id, type icon, source status.
- Status row: state chip, timestamp, source ref.
- Tabs: Summary, Evidence, Context, Digest, Timeline.
- Footer: Copy source refs, focus in scene, show in timeline.

Rules:

- Empty state text: `Select node, edge, block, or event.`
- All operational values include source refs.
- Long markdown/artifact previews are scrollable, not embedded into the scene.
- Missing data is explicit and source-cited.

### Timeline and Replay Controls

Controls:

- Play/pause icon button.
- Step previous/next event icon buttons.
- Speed select: 0.5x, 1x, 2x, 4x.
- Jump menu: first activation, first handoff, first blocked gate, convergence,
  delivery.
- Scrub bar with colored event ticks.

Event tick colors:

- Activation: cyan.
- Handoff: blue.
- Policy decision: amber.
- Artifact: green.
- Evaluation: violet.
- Error/block: red.
- Delivery: gold.

Timeline rules:

- Scrubbing reconstructs scene state at that event.
- Hover previews event metadata; essential data remains accessible on focus.
- Reduced motion uses discrete state jumps.

### Filters and Search

Left rail filters:

- Node layer.
- Node status.
- Relation type.
- Activation-capable only.
- Context-only only.
- Has handoff.
- Has artifact.
- Has open question.
- Has missing digest or failed verification.

Search fields:

- role id
- artifact id
- handoff ref
- context digest prefix
- event id
- relation type

Search result component:

- Type icon.
- Primary id.
- Secondary source ref.
- Status chip.
- Focus action.

## Empty, Partial, Error States

### No Trace Selected

Render Graph structure, relation legend, and concept anchors. Do not show node
activity, handoff blocks, or fake timeline events.

### Partial Trace

Render available facts and show source warnings:

- Missing context report.
- Missing artifact ref.
- Missing handoff file.
- Unknown node id.
- Unknown relation type.
- Unparseable YAML.

### Blocked Candidate

Show candidate node/edge, attach Policy gate, and list missing facts in the
inspector.

### Context-Only Activation Attempt

Use red Policy gate and exact message:

`This relation carries context but cannot activate a node.`

### Digest Mismatch

Keep block visible. Mark digest chain unverified and show the payload plus the
integrity problem together.

## Accessibility and Motion

Keyboard:

- Tab reaches top bar controls, left rail filters, timeline controls,
  inspector tabs, and scene focus manager.
- Arrow keys move through search results and timeline events.
- Enter selects focused node/edge/block/event.
- Escape clears selection or closes expanded preview.
- `0` resets camera when focus is in scene.

2D fallback:

- Node table with status, layer, domain, artifact count, source refs.
- Edge table with relation type, activation capability, weight, confidence.
- Handoff table with ref, from, to, artifact refs, digest state.
- Event table with sequence, timestamp, type, actor, source ref.

Non-color cues:

- Node state uses rim shape, badge, slash/check/pause/warning icons.
- Edge type uses line pattern and arrow style.
- Digest status uses hash/check/broken-hash icons.
- Policy state uses gate shape and text labels.

Contrast:

- DOM text must meet WCAG AA: 4.5:1 normal, 3:1 large text.
- Canvas labels should target AA against their immediate backdrop when visible;
  otherwise inspector/search provides accessible text.

Reduced motion:

- Disable continuous node pulses.
- Replace handoff movement with stepped positions.
- Disable camera auto-focus animation; jump instantly or use 80 ms fade.
- Keep event tick updates and state changes visible without motion.

Motion limits:

- No automatic scene spinning.
- No parallax background.
- No flashing faster than 3 Hz.
- Running pulse amplitude remains subtle; it must not fight timeline reading.

## Implementation Notes for Three.js

Use stable object names:

- `node:<role_id>`
- `edge:<from>:<to>:<relation_type>`
- `gate:<candidate_id>`
- `handoff:<handoff_ref>`
- `concept:<graph|policy|ledger|runtime|learning>`

Material mapping:

- Use shared semantic token object to generate Three.js colors.
- Keep DOM tokens and scene material colors in one TypeScript module.
- Use instanced meshes for node bodies if rendering all 35 nodes with frequent
  status updates.
- Use line geometry that supports dashed and thick lines consistently.
- Prefer deterministic coordinates from the snapshot adapter over client-side
  force layout.

Selection sync:

- One global selection store.
- Scene, inspector, timeline, and search read the same selection.
- Timeline replay can change hover/focus but should not overwrite explicit
  selection unless the selected object disappears from current event state.

## Developer Handoff Checklist

- Implement semantic tokens before component-specific overrides.
- Build dark and light themes from the same token names.
- Render all 35 nodes and 122 edges from Graph data.
- Keep `supports`, `constrains`, `complements`, `augments`, and `precedes`
  visually context-only/order-only.
- Render handoff blocks as inspectable objects with deliverable, context, and
  digest slices.
- Use Ledger/Graph source refs for every operational fact.
- Provide reduced-motion mode and 2D fallback from the first usable prototype.
- Do not add execution, approval, or graph mutation controls in v1.

## Completion Report

```yaml
completion_report:
  what_was_done: >
    Produced design tokens and component/state specifications for the Three.js
    Silicon Org operations visualizer, covering node statuses, edge types,
    handoff blocks, concept planes, inspector panels, replay controls,
    dark/light themes, accessibility, and motion constraints.
  key_decisions:
    - decision: "Use one semantic token layer for both Three.js materials and DOM panels."
      rationale: "Scene, inspector, filters, and timeline must describe the same Graph/Ledger facts without visual drift."
    - decision: "Make activation-capable edges visually impossible to confuse with context-only edges."
      rationale: "The UX handoff explicitly warns that supports/constrains/complements/augments must not look like direct activation routes."
    - decision: "Represent handoff blocks as structured payload objects with deliverable, context, and digest slices."
      rationale: "The user wants block transfer and each block's contents visible during runtime and replay."
    - decision: "Treat reduced motion and 2D fallback as v1 requirements."
      rationale: "The visualizer is an operations tool, so accessibility and legible evidence inspection are not optional polish."
  handoff_focus:
    - "Prototype should implement token-driven node, edge, gate, and handoff materials from this spec."
    - "Senior frontend should keep the normalized snapshot as the component boundary and avoid raw YAML coupling."
    - "Architecture should expose digest verification state explicitly rather than letting UI infer integrity."
  known_constraints:
    - "The visualizer observes and explains; it does not run nodes, edit Graph, or approve artifacts."
    - "Only Graph and Ledger facts may be displayed as operational truth."
    - "Top-level concepts remain Graph, Ledger, Policy, Runtime, and Learning."
    - "No continuous motion is required for users with reduced-motion preference."
  confidence_differential: 0.04
  dissent_if_alone: null
  iteration_context: "ui-design-system node output based on ux-researcher-designer handoff for task-20260527T223527-0b0ecd01."
```
