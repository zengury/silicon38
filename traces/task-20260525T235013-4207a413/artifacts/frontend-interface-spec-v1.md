# Fleet Ops Dashboard — Frontend Interface Spec v1

---

## 1. Stack

| Layer | Choice | Justification |
|-------|--------|---------------|
| Framework | React 18 (Concurrent Mode) | `startTransition` + `useDeferredValue` isolate WS message processing from modal mount; Suspense boundaries protect triage canvas from slow drawer loads. Serves FR-001 because modal state updates are never batched behind deferred work. |
| State | Zustand (single store, sliced) | Flat subscription model maps cleanly to the three independent state regions (triage canvas, drawer, fleet health). No context waterfall; WS message handler writes to store without React lifecycle involvement. |
| WS client | Native `WebSocket` API, singleton module | No library needed at this scale; one socket per session; reconnect logic is ~30 lines; avoids dependency footprint. |
| Chart lib | Recharts (lazy-imported, drawer-only) | Never on the critical path — loaded only when History drawer opens. Zero impact on FR-001/FR-002. |
| Bundle budget | **≤ 300 KB gzipped JS** (app-tier) | This is an ops app, not a landing page. 300KB budget per performance.md app-page rule. Recharts (~60KB gz) is deferred; core canvas bundle targets ≤ 120KB gz. |

---

## 2. Route + Tab Map

Single SPA. React Router v6. Two routes, one layout shell.

| URL | In-memory state | URL holds |
|-----|----------------|-----------|
| `/triage` | active alert queue, vitals map, dwell timer state, modal queue index | nothing (canvas state is live WS truth) |
| `/triage?drawer=history&robot=<id>` | same + history query results | drawer identity + robot target |
| `/triage?drawer=config&robot=<id>` | same + config form state | drawer identity + robot target |
| `/fleet-health` | fleet summary snapshot | nothing |

Tab state (Triage / Fleet Health) is URL-driven. Modal queue (`1 of 3` header) is in-memory only — it does not survive reload, which is correct: on reload the reconnect sequence re-fetches active alerts.

---

## 3. Component Tree

```
<App>                          — mounts WS singleton, owns Zustand store provider
  <LayoutShell>                — two tabs pinned top; incident badge on Fleet Health tab
    <TriageCanvas>             — subscribes: alertQueue[], vitalsMap; renders empty state or cards
      <SystemStatusLine>       — renders robot-online count + last-seen; token: --color-text-recessive
      <TriageCard>             — one per active alert; subscribes: alert, vitals, collab
        <FailureTypeHeading>   — renders alert.type + joint_id; token: --type-size-failure
        <VitalsSlab>           — renders 4 vitals in urgency order; emits: onVitalHover(metric, raw)
          <VitalCell>          — renders canonical value + label; emits: onDwellStart, onDwellEnd
        <ClaimStrip>           — renders CLAIM button or claimer name; emits: onClaim
        <RawShadowTooltip>     — portal into body; subscribes: dwellState from store
      <AlertModal>             — portal; subscribes: modalQueue[0]; emits: onAck, onClaim, onEscalate
    <DrawerPanel>              — slides in from right; subscribes: URL drawer params
      <HistoryView>            — lazy; fetches /robots/{id}/history on mount
      <ConfigView>             — lazy; fetches + patches /robots/{id}/config
    <FleetHealthView>          — fetches /fleet/health on tab focus; renders donut + heatmap
```

---

## 4. WebSocket Lifecycle

**Connect:** on `<App>` mount, `new WebSocket('wss://<host>/fleet/stream')`.

**On open:**
1. Fire `GET /api/alerts/active` — populate `alertQueue` in store with any in-flight alerts before subscribing to stream. Mandatory per architect §6 constraint 3.
2. Begin processing incoming stream messages.

**Message types handled** (from api-wire-contract-v1 §2):
- `type: "telemetry"` → update `vitalsMap[robot_id]` in store; reset stale timer for that robot.
- `type: "alert"` → push `AlertEvent` to `alertQueue`; open modal if queue was empty.
- Unknown `type` → silently ignored per api §4 forward-compatibility rule.

**Stale-data marker:** each robot entry in `vitalsMap` carries a `lastSeenMs` timestamp. A `setInterval` running every 1s checks all entries. Any entry with `Date.now() - lastSeenMs > 5000` sets `stale: true` on that entry. `VitalCell` reads `stale` and renders "last seen: Xm ago" using `--color-text-recessive` + `--type-family-mono`.

**On close (any code):** exponential backoff — initial delay 1s, multiply 2× per attempt, cap at 30s. On each successful reconnect, repeat the `GET /api/alerts/active` bootstrap before processing stream.

---

## 5. Triage Card and Alert Modal — Full Component Spec

### `<TriageCard>`

**Props:**
```typescript
interface TriageCardProps {
  alert: AlertEvent;
  vitals: TelemetryFrame | null;
  collab: { claimed_by: string | null; note: string | null };
  state: "INCIDENT" | "HANDOFF" | "RESOLVED";
}
```

**DOM structure:**
```
article[data-state, role="region", aria-label="Alert: {type} — {robot_id}"]
  header
    h2.failure-type          — tokens: --type-size-failure, --type-weight-failure, --color-critical (INCIDENT) or --color-warning (HANDOFF)
    p.robot-id               — tokens: --type-size-robot-id, --color-text-primary
  section.vitals-slab        — tokens: --space-vitals-gap; border-top 1px --color-divider
    [VitalCell × 4]          — urgency order: breached metric first
  footer.claim-strip         — token: --space-gutter-top
    button.claim-btn | span.claimer-name
    input.note-field[type="text", maxlength="500"]
  [RawShadowTooltip]         — conditionally rendered via portal when dwellState.active
```

**Border:** `--color-critical` at `INCIDENT`; swaps to `--color-warning` at `HANDOFF` via `data-state` CSS attribute selector. Card background: `--color-canvas-raised`. Rim fill: `--color-critical-muted` at `INCIDENT`, `--color-warning-muted` at `HANDOFF`.

**Entrance animation:** `transform: translateY(40px)` → `translateY(0)` over `--motion-enter-duration` with `--motion-enter-easing`.  
**Exit animation:** `translateY(0)` → `translateY(-60px)` + `opacity 1→0` over `--motion-exit-duration` with `--motion-exit-easing`.

**Keyboard:** `Tab` cycles through VitalCells, CLAIM button, note field. `Enter` on CLAIM fires claim action. No other bindings on card.

**Accessibility:** `aria-label` on `article` includes robot ID and alert type. `aria-live="polite"` on `.claimer-name` span — updates when another operator claims. `aria-describedby` on each `VitalCell` points to its label element.

---

### `<AlertModal>`

**Props:**
```typescript
interface AlertModalProps {
  alert: AlertEvent;
  queueLength: number;
  queueIndex: number;   // 0-based
  onAck: (alertId: string) => void;
  onClaim: (alertId: string) => void;
  onEscalate: (alertId: string, reason: string) => void;
}
```

**DOM structure:**
```
div[role="dialog", aria-modal="true", aria-labelledby="modal-title", aria-describedby="modal-body"]
  div.modal-scrim           — token: --color-canvas-overlay; transition --motion-modal-duration/easing
  div.modal-panel
    header
      p.queue-counter        — "1 of {queueLength}"; tokens: --type-size-vitals-label, --color-text-recessive
      h1#modal-title         — alert type; tokens: --type-size-failure, --color-critical
      p.robot-id             — tokens: --type-size-robot-id, --color-text-primary
    section#modal-body
      div.vitals-snapshot    — same VitalCell layout as card
      p.suppressed-badge     — "+N more since ACK" if suppressed_count > 0; token: --color-text-recessive
    footer.modal-actions
      button#btn-ack         — "ACK"; default focus on open; leftmost
      button#btn-claim       — "CLAIM"; center
      button#btn-escalate    — "ESCALATE"; rightmost; requires reason text before enabling
    button.prev-alert[aria-label="Previous alert"]  — visible only when queueLength > 1
    button.next-alert[aria-label="Next alert"]
```

**Focus trap:** on mount, focus moves to `#btn-ack`. `Tab` cycles within modal. `Escape` fires ACK (smallest commitment per ux §4).

**`aria-live="assertive"`** on `div.modal-panel` — announces modal to screen readers immediately (this IS an interrupt).

**Claim 409 handling:** on `POST /alerts/{id}/claim` returning `409`, immediately replace CLAIM button with `span.claimer-name` showing winner's name read-only. No retry affordance per api §6 constraint 2.

**`suppressed_count_since_last_ack`:** displayed verbatim from `AlertEvent`; never decremented client-side per api §6 constraint 3.

---

## 6. Hover Raw-Shadow

**Dwell timer:** 200ms. Implemented as a `useRef` holding a `setTimeout` handle inside `<VitalCell>`. Dwell state lives in the Zustand `ui` slice:

```typescript
interface DwellState {
  active: boolean;
  metric: string;
  rawValue: number | string;
  rawUnit: string;
  anchorRect: DOMRect | null;
}
```

Global state ensures only one tooltip exists at a time across all `VitalCell` instances.

**Pointer leave:** `clearTimeout` on the ref; set `dwellState.active = false`. Tooltip disappears immediately — no transition.

**Single tooltip primitive:** `<RawShadowTooltip>` renders once as a portal into `document.body`. Reads `dwellState` from store. Position: `position: fixed` calculated from `anchorRect`. Content: `raw: {rawValue} {rawUnit}` in `--type-family-mono`, `--type-size-mono`, `--color-text-recessive` on `--color-canvas-raised` background, `1px solid --color-divider` border.

**Canonical null:** if `canonical_temp_c` is `null`, display "—" in canonical slot; still show `rawValue` + `"UNKNOWN:<unit>"` in raw shadow per api §6 constraint 1.

**Tooltip suppression:** `dwellState.active` is set to `false` on modal open. No raw shadow appears while a modal is in the queue.

---

## 7. Performance Posture

**Three things measured:**
1. **Modal mount time** — `performance.mark('modal-open-start')` at WS `"alert"` message receipt; `performance.measure('modal-mount', 'modal-open-start')` in modal's `useLayoutEffect`. Target ≤50ms (architect §3 budget).
2. **WS message handler time** — `performance.now()` diff around the store write; `console.warn` if >10ms (indicates store write contention).
3. **Time to first meaningful paint** — Lighthouse CI measuring the moment `<SystemStatusLine>` is visible and populated.

**Where to profile:** Chrome DevTools Performance tab with WS traffic replayed from a recorded HAR; React DevTools Profiler flamegraphs during INCIDENT state entry.

**Deliberate non-goal:** drawer chart render time. History forensics are explicitly the slow path (architect §1). Recharts rendering 30 days of downsampled data is not optimized in v1.

---

## 8. Three Implementation Risks

1. **Modal queue starvation under alert storm.** Eight simultaneous robot alerts → queue depth 8; operator must ACK sequentially while vitals continue updating behind the modal. **Mitigation:** cards beneath the scrim remain live (vitals update in store); scrim uses `--color-canvas-overlay` (88% opacity, not opaque) so card motion is perceptible. Queue counter `"1 of 8"` communicates depth.

2. **WS reconnect race with `GET /api/alerts/active`.** After a long disconnect, REST response may include an alert already resolved on the server. Ghost card appears. **Mitigation:** implement a `reconciling: boolean` flag on store for 500ms post-reconnect. Any `type: "alert"` WS message with `suppressed_count_since_last_ack > 0` received during this window causes the card to be added; any WS `ALERT_ACKED` equivalent removes it. REST snapshot and stream are merged in the window, then `reconciling` clears.

3. **Raw-shadow tooltip layering above modal.** Portal-rendered tooltip at `Z_TOOLTIP = 200` may appear above `Z_MODAL = 300` if stacking contexts are inconsistent. **Mitigation:** define two named z-index constants (`Z_TOOLTIP = 200`, `Z_MODAL = 300`). Suppress `dwellState.active` entirely when `modalQueue.length > 0`. A `VitalCell` inside the modal uses an in-portal tooltip rendered within the modal's own stacking context at `Z_TOOLTIP`, not at root.

---

## 9. What Is OUT of v1

- **Theme toggle** — `prefers-color-scheme` CSS only; no toggle in UI. PRD §5 non-goal.
- **i18n / localization** — English hardcoded; no translation infrastructure. PRD §5 non-goal.
- **Draggable / configurable layout** — card stack order is severity-then-time, fixed. PRD §5 non-goal.
- **PDF / Excel export** — separate Reports product per PRD §3. No download affordance.
- **External notifications (Slack / email / SMS / push)** — architect Cut 2; deferred to v2.
- **@-mention threading** — claim + one-line note is the complete handoff surface. PRD §5.
- **Sound volume / mute control** — single tone fires on modal open; no settings panel in scope.
- **Geo / map view** — `TelemetryFrame.geo` field received and stored; map widget not rendered.

---

```yaml
completion_report:
  what_was_done: >
    Produced engineer-ready frontend interface specification for the Fleet Ops Dashboard,
    integrating PRD, UX interaction design, UI tokens, architecture, and API wire contract.
    Defined stack with bundle budgets, routing model, component tree, WS lifecycle,
    full component specs for TriageCard and AlertModal, raw-shadow implementation,
    performance measurement posture, implementation risks with mitigations, and explicit v1 cuts.
  key_decisions:
    - decision: React 18 Concurrent Mode + Zustand
      rationale: >
        startTransition isolates WS writes from modal render path, serving FR-001.
        Zustand flat subscription avoids React context re-render cascades across
        independent state regions.
    - decision: Native WebSocket API, no library
      rationale: >
        One socket, 4 message types, ≤10 sessions. Library adds complexity without benefit.
    - decision: dwellState in global Zustand ui slice, single portal tooltip
      rationale: >
        Single tooltip primitive prevents z-index conflicts and ensures mutual exclusion
        across all VitalCell instances including those inside the modal.
    - decision: Modal queue in-memory only, not URL-persisted
      rationale: >
        Alert state is idempotent live truth; reload re-fetches via GET /api/alerts/active.
        URL-persisted alert IDs create stale-URL problems after ACK.
  handoff_focus:
    - "WS reconnect sequence is mandatory: GET /api/alerts/active fires before stream subscribe, not after"
    - "Claim 409: immediately render winner name read-only; no retry affordance per api §6"
    - "canonical_* null: render '—' + raw value verbatim; never convert client-side per api §6"
    - "Z_TOOLTIP=200 / Z_MODAL=300 constants must be defined before any portal work"
    - "suppressed_count_since_last_ack: never decrement locally; server-authoritative per api §6"
  open_questions:
    - "Browser autoplay policy may block the single modal-open tone without prior user gesture. Does the ops environment guarantee a prior interaction, or is a user-gesture unlock flow needed?"
    - "GET /api/alerts/active endpoint: api artifact documents POST /alerts/{id}/ack and GET /robots/{id}/history but does not explicitly define GET /api/alerts/active. Backend must confirm this endpoint exists, its response schema (AlertEvent[]), and its auth requirements."
  known_constraints:
    - "All palette, type, spacing, and motion values reference ui-tokens-v1.md tokens only; no inline values"
    - "raw_shadow fields are display-only; never used in client logic or state transitions per architect §6 constraint 4"
    - "Claim write is REST POST, not WS; client is receive-only on WS per architect §6 constraint 5"
    - "No conversion logic in frontend; canonical_* null → '—' per api §6 constraint 1"
  iteration_context: null
```
