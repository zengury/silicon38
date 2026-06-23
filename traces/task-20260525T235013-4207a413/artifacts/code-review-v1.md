# Cross-Artifact Review — Fleet Ops Dashboard Design

## 1. Verdict

**CHANGES_REQUIRED** — the design is coherent and soul-aligned at the level of intent, but three contract-level inconsistencies between the API artifact and what architecture/frontend assume will silently break the alert hot path if code is written from this set as-is.

## 2. Cross-artifact consistency findings

1. **CRITICAL — `GET /api/alerts/active` is undefined in api-wire-contract.** Architect §6 constraint 3 and frontend §4 both require this endpoint as the mandatory reconnect bootstrap; senior-frontend self-flagged this in its open questions. The api artifact §2 enumerates `WS /fleet/stream`, `POST /alerts/{id}/{ack,claim,escalate}`, history, config, notes, and `/fleet/health` — but no `GET /api/alerts/active`. *Fix:* add to api §2 with response schema `AlertEvent[]` and document whether dedup state and current claimer are included.

2. **CRITICAL — WS message type names disagree.** Architect §2 enumerates `VITALS_UPDATE`, `ALERT_FIRED`, `ALERT_ACKED`, `COLLAB_UPDATED`. api §2 defines only two: `type: "telemetry"` and `type: "alert"`. Frontend §4 follows api ("telemetry"/"alert") but §5/§8 still references "ALERT_FIRED" / "ALERT_ACKED" semantically. There is no wire-level event for ACK or COLLAB updates — yet frontend risk #2 mitigation depends on a "WS `ALERT_ACKED` equivalent." *Fix:* api must define `alert_acked` and `collab_updated` message variants, or architect §6 constraint 5 (claim broadcast over WS) is unimplementable.

3. **HIGH — `AlertEvent` payload vs. architect's "all modal data in WS message."** Architect §6 constraint 2 says modal must not block on any fetch; all modal data (robot ID, alert type, vitals, claimer) must arrive in the alert message. api `AlertEvent` (§3) carries `breached_metric` but NOT the four vitals the modal renders (frontend §5 `<AlertModal>` shows `div.vitals-snapshot` "same VitalCell layout as card") and NOT `claimed_by`. *Fix:* embed `vitals_snapshot: TelemetryFrame` and `claimed_by: string | null` in `AlertEvent`, or accept the modal will fetch.

4. **HIGH — Card border width is undefined.** Card border *color* is tokenized (`--color-critical`, `--color-warning`); border *width* is not in ui-tokens but is implied by frontend §5 (`1px solid --color-divider` for tooltip, nothing stated for card). *Fix:* add `--border-card-width` token or frontend declares the literal explicitly.

5. **MEDIUM — `POST /alerts/{id}/ack` returns `204` (api §2) but architect §2 hot path shows server fanning out `ALERT_ACKED` to other sessions.** No such WS message exists in api. Other operators won't see the ACK until the next telemetry frame, and FR-004's "others see the claimer's name immediately" hangs on this. *Tied to finding #2.*

6. **MEDIUM — `incidents/{iid}/notes` (api §2) introduces an `incident_id` distinct from `alert_id`.** PRD FR-009 talks about incident lifecycle; api §3 only carries `alert_id`. The mapping is undefined. Frontend §5 stores `collab` as `{claimed_by, note}` but never resolves which ID it posts under. *Fix:* explicit `alert_id ↔ incident_id` relation in api §1.

7. **LOW — Soul check.** Nothing snuck back that the knife removed: theme/i18n/draggable/export all stay out, Fleet Health remains a quiet secondary tab, no decoration crept in. Good.

## 3. What the design refuses to know

- **The WATCH state is unreachable for a distracted operator.** ux §2 places "a soft amber tick at canvas edge" — but if the operator is in the History drawer (covers 40% of canvas, §6) or on the Fleet Health tab, the tick is occluded or off-screen. There is no rule for promoting WATCH across tab/drawer occlusion, nor for surfacing it audibly.
- **The "single tone" is unspecified.** ux §4 says "a single tone, once." No frequency, duration, envelope, or fallback when the browser blocks autoplay (frontend §9 self-flagged this). A tone the operator never hears is worse than no tone.
- **Zero-robot fleet.** PRD §3 says cards appear only when alerts fire; ux §1 reads "12 robots online." What does the canvas say at *zero* robots online? Is that the empty Salk plaza, or itself an alert? The state machine starts at IDLE assuming a healthy fleet; it never models "fleet is gone."

## 4. One thing done unusually well

**ui-tokens §5 "One Thing Refused" — cutting `--color-success`.** This is the soul speaking in CSS. Resolution-as-subtraction (the canvas emptying) is the reward; a green pill at incident close would be paint over a finished wall. The token sheet teaches the next engineer why an *absence* is a decision.

## 5. What's needed before any code is written

1. **api-designer revision** adding `GET /api/alerts/active`, ACK/COLLAB WS message variants, and embedding modal payload (`vitals_snapshot`, `claimed_by`) into `AlertEvent`. Resolves findings #1, #2, #3, #5.
2. **Explicit `alert_id ↔ incident_id` mapping** in api §1 so collab state and notes endpoint can be implemented without guessing.
3. **A two-line spec for the single tone** (asset, duration, autoplay-unlock fallback) plus a rule for WATCH-state surfacing when the operator is in a drawer or on Fleet Health.
