# Fleet Ops Dashboard — Wire Contract v1

---

## 1. Canonical Telemetry Frame

**Resolution of PRD Open Question 3 (raw-shadow serialization):** Raw shadow ships **inline** in every telemetry frame, not hydrated on hover. Reasoning: hover-hydrated means a second round-trip that breaks the 500ms alert budget (FR-001) when an operator's first glance lands on the raw value. Bandwidth delta per frame at 12 robots × 2s cadence is negligible (<4 KB/s total). The frontend hover layer reads inline fields — no extra fetch required.

```typescript
// All timestamps: ISO-8601 UTC string, millisecond precision.
// canonical_* fields are always in SI/display units.
// raw_* fields carry the wire value exactly as the robot emitted it.

type Unit = string;  // e.g. "celsius", "fahrenheit", "percent", "ratio_0_1", "UNKNOWN:<original>"

interface RawShadow<T> {
  raw_value: T;
  raw_unit: Unit;
}

interface JointThermal {
  joint_id: string;             // e.g. "left_knee", "right_shoulder_pitch"
  canonical_temp_c: number | null;  // always Celsius; null if conversion failed (see §5)
  raw: RawShadow<number>;
  status: "ok" | "warning" | "critical";  // warning >50°C, critical >65°C
}

interface Battery {
  canonical_pct: number;        // 0–100 float
  raw: RawShadow<number | string>;
}

interface Network {
  rtt_ms: number | null;        // null = no ping response in last interval
  stale_age_s: number;          // seconds since last successful telemetry receipt; 0 if current
}

interface Geo {
  lat: number;
  lon: number;
  accuracy_m: number;
}

interface TelemetryFrame {
  schema_version: "1";          // string literal; increment on breaking change
  robot_id: string;
  timestamp: string;            // ISO-8601 UTC ms
  battery: Battery;
  joints: JointThermal[];       // one entry per reporting joint; sparse OK
  cpu_load: number;             // 0.0–1.0 ratio
  network: Network;
  current_task: string | null;  // free text from robot task manager; null if idle
  geo: Geo | null;              // null if GPS unavailable
}
```

---

## 2. Wire Endpoints

### `WS /fleet/stream`
Server-push only. Multiplexes two event types:
```typescript
type StreamMessage =
  | { type: "telemetry"; payload: TelemetryFrame }
  | { type: "alert";     payload: AlertEvent };
```
Clients MUST ignore unknown `type` values. Status codes (HTTP upgrade): `101` | `401` | `429`

### `POST /alerts/{id}/ack`
Body: `{ operator_id: string }` — `204` | `404` | `409 Conflict` (already archived)

### `POST /alerts/{id}/claim`
Body: `{ operator_id: string }` — `200 { claimed_by, claimed_at }` | **`409 Conflict { claimed_by, claimed_at }`** (FR-004 concurrency error: first write wins; loser receives winner's identity immediately, no retry)

### `POST /alerts/{id}/escalate`
Body: `{ operator_id: string; reason: string }` — `200 { escalated_at }` | `404`

### `GET /robots/{id}/history?from=&to=&metrics=`
`metrics` values: `battery|cpu_load|joint_temp|network_rtt` (comma-separated). Max window 30 days; default last 15 minutes.
Response: `200 { robot_id, schema_version, samples: TelemetryFrame[] }` | `400` | `404`

### `PUT /robots/{id}/config`
```typescript
interface ConfigWrite {
  expected_version: number;     // required; current server version; optimistic concurrency lock
  thresholds?: { joint_temp_warning_c?: number; joint_temp_critical_c?: number; battery_warning_pct?: number; cpu_load_warning?: number };
  sample_rate_ms?: number;
  reconnect_timeout_ms?: number;
}
```
`200 { config_version: number }` | `409 Conflict { current_version: number }` (stale write, FR-006) | `400`

### `POST /robots/{id}/incidents/{iid}/notes`
Body: `{ operator_id: string; text: string }` (max 500 chars) — `201 { note_id, created_at }` | `404`

### `GET /fleet/health`
`200 { schema_version, computed_at, total_robots, healthy, degraded, critical, offline }` — aggregate only, no per-robot detail.

---

## 3. Alert Event Envelope

```typescript
type AlertType = "fall" | "joint_lost" | "low_battery" | "cpu_overload" | "network_stale" | "joint_thermal_warning" | "joint_thermal_critical" | "other";

interface AlertEvent {
  schema_version: "1";
  alert_id: string;             // UUID
  robot_id: string;
  type: AlertType;
  severity: "warning" | "critical";
  breached_metric: {
    metric_name: string;
    canonical_value: number | null;
    canonical_unit: string;
    raw_value: number | string;
    raw_unit: Unit;
  };
  occurred_at: string;          // ISO-8601 UTC ms; time of threshold breach
  dedup_key: string;            // server-computed opaque hash; stable within breach window (FR-007)
  suppressed_count_since_last_ack: number;  // 0 on first fire; increments until ACK
}
```

**Example:**
```json
{
  "schema_version": "1", "alert_id": "a3f8c2d1-...", "robot_id": "g1-unit-07",
  "type": "joint_thermal_critical", "severity": "critical",
  "breached_metric": { "metric_name": "joint_temp", "canonical_value": 71.3, "canonical_unit": "celsius", "raw_value": 344.45, "raw_unit": "kelvin" },
  "occurred_at": "2026-05-26T02:14:07.312Z",
  "dedup_key": "g1-unit-07:joint_thermal_critical:joint_temp:left_knee",
  "suppressed_count_since_last_ack": 4
}
```

---

## 4. Versioning

`schema_version` is a string literal in every top-level frame and event. **Forward-compatibility rule:** clients MUST silently ignore unknown fields at any nesting depth and MUST NOT fail on unknown `AlertType` values (treat as `"other"`). Breaking changes (field removal, type change, rename) require a version increment; old versions served ≥30 days before retirement. `raw_unit` changes propagate immediately — the conversion table updates server-side, `canonical_*` remains stable, clients display `raw_unit` verbatim with no changes required.

---

## 5. Unit Drift Contract

**Canonical conversion happens server-side only**, in the manastone-diagnostic normalization layer, before frames reach the WebSocket. Clients never implement conversion logic.

**Conversion table:** `unit_conversions.yaml`, owned by the **backend team**, loaded at service startup. Maps `(raw_unit, metric_name) → (conversion_fn, canonical_unit)`. Single source of truth; no conversion logic in frontend or alert engine.

**Unknown unit — quarantine (not refuse, not pass-through):**
- `canonical_*` set to `null`; `raw_unit` set to `"UNKNOWN:<original>"`
- Frame is emitted — not dropped
- Alert engine treats `null` canonical values as indeterminate: no threshold evaluated, no alert fires on that metric
- A `{ type: "diagnostic" }` stream event is emitted once per newly-seen unknown unit so operators know the robot is not silently healthy

---

## 6. Hard Constraints

**For senior-frontend:**
1. Never derive canonical values client-side. If `canonical_*` is `null`, display "—" with raw value and unit verbatim. No conversion, no inference.
2. On `POST /alerts/{id}/claim` returning `409`, immediately render the winner's name read-only. No retry affordance.
3. `suppressed_count_since_last_ack` is server-authoritative and monotonically increasing until ACK. Never decrement or reset locally.

**For senior-engineer:**
1. `expected_version` on `PUT /robots/{id}/config` is non-optional. Reject missing field with `400` — no default-to-current convenience; callers must have read current config before writing.
2. Normalization completes before alert engine evaluation. The 500ms budget (FR-001) is measured from DDS receipt to WebSocket emit; the conversion pipeline is on the critical path and may not be deferred.
3. `dedup_key` is computed server-side and opaque. Do not expose construction logic in any client-facing documentation or SDK.

---

*Artifact: api-wire-contract-v1 | Producer: api-designer | Task: task-20260525T235013-4207a413*
