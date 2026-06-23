# Fleet Ops Dashboard — PRD

## 1. Product North Star
The fleet ops dashboard answers **one question in failure seconds: which machine, what's wrong, how long left, what do I do?** Everything else is secondary. A robot falls, a joint burns, a battery dies — the operator sees the failing machine first, vital signs in high contrast, the alert as an unignorable modal, and one field to claim ownership before escalating. No aggregates, no historical charts, no theme picker compete on that moment. The true act is: **in the seconds a machine is failing — which one, what's wrong, how long left, what to do.**

## 2. Personas
**Primary: Fleet Ops Engineer (mid-shift)** — monitors 4–12 G1 robots in real-time during a mission. Decision window <30s per incident. Needs "what failed" and "I'm on it" in two glances.

**Secondary: Shift Handoff** — receives an open incident; must understand what's been attempted. Reads claim + note; rarely changes config. Sessions 2–3 minutes.

## 3. Surface Map

### Foreground: Triage Canvas (always visible)
One card per failing robot (empty until an alert fires). Each card: robot ID, alert type, vital-signs slab (joint temp, battery %, CPU, network) ordered by urgency, canonical + raw-shadow on hover, claim field, one-line note. Alerts render as modals with **ACK / CLAIM / ESCALATE**. On ACK the modal closes; the card stays.

### Drawer: Forensics (history + admin config)
Opens by explicit "View History" or post-ACK. (a) per-robot time-series — default zoom last 15 min, max 30 days; (b) admin config (thresholds, sample rate, reconnect) — usable only in calm periods.

### Tab: Fleet Health (aggregates)
Donut (% healthy) + heatmap (robots × time). Answers "how's the fleet overall." Does NOT drill or alert.

### Explicitly OUT
- **Export (PDF/Excel)** — moved to a separate Reports product; not in dashboard nav.
- **Theme / i18n / draggable layout** — system dark follows OS; English default; layout fixed and canonical.

## 4. Functional Requirements (testable)

| ID | Spec | Acceptance |
|----|------|------------|
| FR-001 | Alert path SLA | Modal renders within 500ms of engine decision; engine decision within 500ms of upstream threshold breach. |
| FR-002 | Telemetry refresh | Vitals update every <2s; "last seen: Xm ago" stale indicator otherwise. |
| FR-003 | Canonical + raw shadow | Canonical unit shown; hover surfaces raw wire value and unit. Never silently coerce. |
| FR-004 | Claim concurrency | First CLAIM wins. Others see the claimer's name immediately (read-only). |
| FR-005 | History default zoom | Drawer opens at last 15 min; scrollable to 30 days within same session. |
| FR-006 | Config write versioning | Threshold edits are versioned; alert engine reads latest version at eval time. |
| FR-007 | Alert dedup window | Identical (robot, type, threshold) alerts suppressed 60s after ACK; "+N more since ACK" badge. |
| FR-008 | Foreground emptiness | Dashboard loads with no cards visible. Cards appear only when an alert fires. |
| FR-009 | Incident lifecycle | Claim + note persist until "Mark Resolved" archives the card. |

## 5. Non-Goals
- 30-day foreground history — triage is last 30 seconds.
- Elaborate config panel — tuning belongs in calm.
- @-mention threading — handoff is claim + one-line note.
- Donut/heatmap in foreground — aggregates bury the failing machine.
- Theme switching — cognitive load.
- i18n — English default unless ops team genuinely multilingual.
- Draggable layout — fixed canonical layout reduces decision friction.

## 6. Open questions for Layer 2
1. **Normalization location**: Telemetry normalization layer in backend (manastone service) or client-side adapter? Affects <500ms alert budget.
2. **Reconnect recovery**: WebSocket disconnect mid-incident — query alert engine on reconnect, or replay from a window?
3. **Raw-shadow serialization**: Inline field in canonical schema, or hydrated on hover (bandwidth concern)?
