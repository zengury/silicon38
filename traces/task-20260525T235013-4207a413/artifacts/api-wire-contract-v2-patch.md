# API Wire Contract — v2 Patch

## What changed and why
Code-review CRITICAL #1 (missing `GET /alerts/active`), CRITICAL #2 (WS event set incomplete — no ACK/COLLAB variants), HIGH #3 (modal payload not reconstructable from a single `alert` event), HIGH #6 (`alert_id` vs `incident_id` undefined). This patch is additive on top of v1; v1 readers see new types as unknown and ignore per §4 forward-compat rule.

## 1. New endpoint: `GET /api/alerts/active`
Returns every alert in `triggered` or `acked-not-resolved` state across the fleet. Used by the client on WS open (and on reconnect) as the canonical bootstrap.

```typescript
// 200 OK
type Response = ActiveAlert[];

interface ActiveAlert {
  alert_id: string;          // == incident_id (see §4)
  robot_id: string;
  type: "fall" | "joint_lost" | "low_battery" | "joint_overtemp" | "other";
  severity: "critical" | "warning";
  breached_metric: { name: string; canonical_value: number | null; canonical_unit: string; raw_value: string; raw_unit: string };
  occurred_at: number;       // ms epoch
  dedup_key: string;
  suppressed_count_since_last_ack: number;
  state: "triggered" | "acked";
  acked_by: string | null;
  acked_at: number | null;
  claimed_by: string | null;
  note: string | null;
  vitals_snapshot: TelemetryFrame;   // sufficient to render the modal without further fetch
}
```
Empty case: `200 OK []`. Never `404`.

## 2. Expanded WS message envelope
Every frame on `/fleet/stream` carries `{ type, schema_version: 2, ... }`. v1 readers ignore unknown `type`.

### `type: "telemetry"` (unchanged)
Trigger: per-robot vitals tick (≤2s cadence per FR-002). Idempotent on `{robot_id, ts_ms}`.

### `type: "alert"` (expanded — now self-sufficient)
```typescript
interface AlertWS {
  type: "alert";
  schema_version: 2;
  alert: ActiveAlert;        // full ActiveAlert payload from §1 — vitals_snapshot + claimed_by inline
}
```
Idempotent on `alert_id`; resend allowed if dedup window resets.

### `type: "alert_acked"` (new)
```typescript
interface AlertAckedWS {
  type: "alert_acked";
  schema_version: 2;
  alert_id: string;
  acked_by: string;
  acked_at: number;
}
```
Idempotent on `alert_id` — late receivers ignore if already in `acked` state.

### `type: "collab_updated"` (new)
```typescript
interface CollabUpdatedWS {
  type: "collab_updated";
  schema_version: 2;
  alert_id: string;
  claimed_by: string | null;
  note: string | null;
  updated_by: string;
  updated_at: number;
  resolved: boolean;             // true → client archives card
}
```
Idempotent on `(alert_id, updated_at)`. Highest `updated_at` wins.

## 3. Mutation endpoints — response + broadcast contract

| Endpoint | HTTP response | WS broadcast |
|----------|---------------|--------------|
| `POST /alerts/{id}/ack`     | `204` (or `409` if already acked) | `alert_acked` |
| `POST /alerts/{id}/claim`   | `204` (winner) / `409 { winner }` (loser) | `collab_updated` (claim) |
| `POST /alerts/{id}/escalate`| `204` | `collab_updated` (note) |
| `POST /incidents/{iid}/notes` | `204` | `collab_updated` (note) |
| `POST /alerts/{id}/resolve` | `204` | `collab_updated` (resolved:true) |

This makes architect §6 constraint 5 wire-true.

## 4. `alert_id ↔ incident_id` mapping
**Rule: `incident_id == alert_id`.** One alert = one incident for v1. `/incidents/{iid}/notes` resolves to the same identifier; server canonicalizes. Future multi-alert incidents will get `/incidents/{iid}` carrying `alert_ids: string[]`; until then, identity.

## 5. Backward compatibility
- `schema_version: 1 → 2`.
- v1 readers ignore `alert_acked` and `collab_updated` per existing forward-compat rule.
- v1 `alert` consumers still parse v2 because new fields are additive.
- `GET /api/alerts/active` is a server addition; no client harm.
