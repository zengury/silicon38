# Architecture Decision Records: 机器人车队运维监控面板

> Source: Zoom-out (9 modules, 3 databases, 5 open decisions) + Caveman (4 invariants) + PRD (24 stories)

---

## ADR-001: Architecture Paradigm — Modular Monolith BFF + Data Pipeline Microservice

### Context
9 functional domains. PRD classifies 3 as Deep (pipeline, alert, config), 4 as Shallow. Need to choose between monolith and microservices for a team of 3-6 engineers.

### Decision
**Modular Monolith BFF + independent Data Pipeline microservice.**

```
Browser (React SPA)
      │ REST + WebSocket
      ▼
┌─────────────────────────────────┐
│  BFF (Node.js / Fastify)        │
│  ┌────────┬────────┬────────┐  │
│  │ Robot  │ Fleet  │ Alert  │  │
│  │ Module │ Module │ Module │  │
│  ├────────┼────────┼────────┤  │
│  │ Config │ History│ Collab │  │
│  │ Module │ Module │ Module │  │
│  ├────────┼────────┼────────┤  │
│  │ Report │ Export │  Auth  │  │
│  │ Module │ Module │ Module │  │
│  └────────┴────────┴────────┘  │
│  Shared: WS Hub, i18n, Cache   │
└──┬──────────────┬──────────────┘
   │              │
   ▼              ▼
┌──────────┐ ┌──────────┐
│PostgreSQL│ │TimescaleDB│
└──────────┘ └────▲─────┘
                  │
┌─────────────────┴───────────────┐
│  Data Pipeline (独立服务)       │
│  MQTT/HTTP/gRPC → Normalize →  │
│  Batch Write TSDB + Pub Events  │
│  Alert Evaluator (嵌入Pipeline) │
└─────────────────────────────────┘
```

### Rationale
- BFF Monolith: 9 modules in early stages have fuzzy boundaries. Monolith allows refactoring before premature microservice extraction.
- Pipeline independent: Compute-intensive normalization must scale separately from Web layer. Different deployment cadence.
- Alert evaluator embedded in Pipeline: Evaluates at data ingest point — no polling TSDB, no extra network hop.

### Alternatives Rejected
| Option | Why Rejected |
|--------|-------------|
| Full microservices (9 services) | 3-6 person team can't operate 9 services in Year 1 |
| Full monolith (pipeline in BFF) | Data normalization competes for CPU with API serving under load |
| Serverless (Lambda) | WebSocket long connections incompatible with Lambda pricing |

---

## ADR-002: Database — PostgreSQL + TimescaleDB + Redis

### Context
Three data categories: operational (robots, users, configs, comments), time-series (telemetry), real-time (latest snapshots, pub/sub).

### Decision
- **PostgreSQL 16**: Operational data. Tables: robots, users, alert_rules, alert_events, comments, config_audit_log.
- **TimescaleDB 2.x**: Telemetry. Hypertable partitioned by 1-day chunks. Compression after 7 days. Retention after 90 days. Continuous aggregates at 1-hour and 1-day granularity.
- **Redis 7**: Latest telemetry cache (5s TTL), Pub/Sub for WebSocket fan-out, alert dedup window (30s TTL).

### Rationale
- TimescaleDB over InfluxDB: PostgreSQL-compatible — same tooling, same team knowledge, joins with operational data when needed.
- Redis over in-memory state: Survives BFF restarts. Shared state across multiple BFF instances.
- Decoupled: Pipeline writes to TimescaleDB + Redis. BFF reads from both. No cross-DB joins required at query time.

---

## ADR-003: Data Pipeline — Config-Driven Normalization

### Context
Robots send telemetry in different formats (JSON, Protobuf, MQTT binary). Field names and units vary by robot model. New robot models must be added without code changes.

### Decision
**Protocol adapters → config-driven schema mapper → unified output.**

```
MQTT (binary) → MQTT Adapter ─┐
HTTP (JSON)   → HTTP Adapter  ─┼→ Schema Mapper → NormalizedTelemetry
gRPC (Protobuf)→ gRPC Adapter ─┘   (YAML rules)
```

Mapping rules per robot model, stored as YAML:
```yaml
robot_model: unitree_g1
fields:
  - raw_path: payload.battery.percentage
    target_field: battery_pct
    transform: multiply(0.01)
  - raw_path: payload.joints.left_hip.temperature
    target_field: joint_temps.left_hip_pitch
    unit_conversion: celsius_to_celsius  # identity
```

### Rationale
- New robot model = new YAML file. No pipeline restart (hot-reload via file watcher).
- Transforms are composable: multiply + offset + enum_map. Covers known variability.
- Mappings validated on load: all target fields must exist in `NormalizedTelemetry` type. Catch config errors at startup, not at 3am.

---

## ADR-004: Frontend — React + TypeScript + Vite

### Context
Dashboard SPA with 8+ pages, real-time updates, draggable layouts, dark/light themes, i18n.

### Decision
**React 18 + TypeScript + Vite.** State: Zustand. Charts: Recharts. Map: Leaflet. Layout: react-grid-layout. Theme: CSS custom properties. i18n: react-intl.

### Rationale
- React: Largest ecosystem for dashboard-like UIs. Zustand over Redux — simpler for WebSocket-driven state.
- Recharts over D3: Declarative React components vs imperative SVG. Faster to build charts. Fall back to D3 if Recharts can't handle real-time streaming.
- CSS custom properties for theming: No build-time theme compilation. Toggle `data-theme="dark"` on `<html>`, all colors switch instantly.

---

## ADR-005: Real-time Transport — WebSocket

### Context
Telemetry updates every 5 seconds per robot. 200 robots = 40 updates/sec. Need push to browser without polling overhead.

### Decision
**WebSocket (ws library on Fastify) with Redis Pub/Sub fan-out.** Channels: `fleet:overview` (aggregated stats), `robot:{id}` (per-robot telemetry), `alerts` (all alert events). Client subscribes to channels on connect.

### Rationale
- WebSocket over SSE: Bidirectional — client can send subscribe/unsubscribe messages. SSE is server→client only.
- WebSocket over polling: 40 msg/s polling every 2 seconds = 80 requests/s. WebSocket: persistent connection, 0 polling overhead.
- Redis Pub/Sub for horizontal scaling: Multiple BFF instances subscribe to same Redis channels. Message delivered once to each instance, fanned out to their connected clients.

---

## ADR-006: Alert Engine — Embedded State Machine

### Context
Alerts must fire once per incident (dedup), must not flood the operator (cooldown), and must track lifecycle (dormant→triggered→acknowledged→dismissed).

### Decision
**State machine embedded in Data Pipeline, evaluated on each normalized data point.**

```
State:      dormant → triggered → acknowledged → dismissed
Trigger:    rule eval (metric > threshold) → alert event + WS push
Cooldown:   same (robot, rule) won't re-trigger for N seconds after triggered
Dedup:      if alert is in 'triggered' state, new evaluation is no-op
```

### Rationale
- Evaluate at ingest point: No polling TSDB. Alert fires within milliseconds of data arrival.
- State in Redis: Alert state stored with 30s TTL (dedup window). Survives pipeline restarts.
- Rule DSL: `{ metric, operator, threshold, severity, cooldown_seconds }`. Simple enough for YAML config, powerful enough for all PRD alert scenarios.

---

## ADR-007: Config Service — CRUD + Audit

### Context
Operators change robot thresholds. Configs must be auditable: who changed what, when, from what to what.

### Decision
**CRUD endpoints on BFF Config Module. Every write creates a `config_audit_log` row.** Old + new values stored as JSONB for diff rendering. Config synced to edge gateway via a version counter — robot checks its config version against server on each telemetry report.

### Rationale
- Audit log in PostgreSQL: Queryable, joinable with user table, no separate audit system needed.
- JSONB for old/new values: Schema-free — works for any config structure without migration.
- Version-based sync: Robot compares local config version with server. Only downloads new config if version differs. Avoids pushing config to every robot on every change.

---

## ADR-008: Collaboration — Thin Layer on PostgreSQL

### Context
Operators need threaded comments, @mentions, and "I'm handling this" markers per robot.

### Decision
**PostgreSQL `comments` table with `parent_id` for threading.** @mentions parsed on write, stored in `mentioned_users UUID[]` array. "I'm handling this" is a special comment type. WebSocket broadcasts new comments to subscribed clients.

### Rationale
- Not a real-time chat system — async comments with threading is a solved database problem. Don't introduce a chat protocol.
- @mention array enables: "show me all threads where I'm mentioned" without full-text search.
- WebSocket for comment delivery: Keeps the collaboration feel real-time without making it a chat system.

---

## Completion Report

**what_was_done**: Produced 8 ADRs resolving all architectural decisions: Modular Monolith BFF + Pipeline µService, PostgreSQL+TimescaleDB+Redis, Config-driven normalization, React+TS+Vite frontend, WebSocket real-time, Embedded alert state machine, CRUD+Audit config, Thin collab layer.

**chain_entry**: "ADR-001: Modular Monolith BFF + independent Data Pipeline µService. ADR-002: PostgreSQL+TimescaleDB+Redis stack. ADR-003: Config-driven normalization (YAML per robot model). ADR-006: Alert state machine embedded in Pipeline, evaluated at ingest."
