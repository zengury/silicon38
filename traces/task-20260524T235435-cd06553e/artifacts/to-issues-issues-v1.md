# Issue Decomposition: 机器人车队运维监控面板

> Source: PRD (21 user stories, 7 modules) + Architect ADRs (modular monolith BFF)
> Estimation scale: S (2-4h), M (1-2d), L (3-5d)
> Dependency graph: acyclic, verified

---

## Issue Map

```
Phase 1 — Foundation (parallel)
  I-001 Data Pipeline Scaffold          ─┬─ I-002 MQTT Adapter
  I-003 BFF Project Scaffold            ─┬─ I-004 DB Schema + Migrations
  I-005 TSDB Schema + Hypertables        ─┤
  I-006 Design Token System              ─┘

Phase 2 — Core Data (parallel, depends on Phase 1)
  I-007 HTTP Adapter + JSON Normalizer   ← I-001, I-002
  I-008 gRPC Adapter + Protobuf Normal.  ← I-001
  I-009 Schema Mapper Engine             ← I-002, I-003
  I-010 TSDB Writer (batch + events)     ← I-005, I-009
  I-011 Robot Module (BFF CRUD)          ← I-003, I-004

Phase 3 — Real-time (parallel)
  I-012 WebSocket Hub                    ← I-003
  I-013 Fleet Overview API + Aggregation ← I-010, I-011
  I-014 Robot Detail API + Time-series   ← I-010, I-011, I-005

Phase 4 — Alerts & History
  I-015 Alert Rule Engine + State Machine← I-010
  I-016 Alert API + Notification Hub     ← I-015, I-012
  I-017 History Query + Downsampling API ← I-010, I-005

Phase 5 — Config & Collaboration
  I-018 Config Module (CRUD + Sync)      ← I-004, I-011
  I-019 Collaboration Module (comments)  ← I-004, I-012

Phase 6 — Frontend (parallel)
  I-020 Dashboard Shell (Layout/Theme/i18n) ← I-006
  I-021 Fleet Overview Page             ← I-013, I-020
  I-022 Robot Detail Page               ← I-014, I-020
  I-023 Alert Panel + Notification UI   ← I-016, I-020
  I-024 Config Panel                    ← I-018, I-020
  I-025 History Explorer                ← I-017, I-020

Phase 7 — Polish
  I-026 Report Engine (PDF/Excel)       ← I-017
  I-027 Map View + Clustering           ← I-014, I-020
  I-028 Dark Mode + Theme Switching     ← I-006, I-020
  I-029 E2E Tests + Load Testing        ← All Phase 6
  I-030 DevOps: Docker Compose + CI/CD  ← All
```

---

## Issues

### I-001: Data Pipeline Scaffold — S

**Description**: Initialize the data pipeline as an independent service. Set up project structure (Node.js + TypeScript), message queue consumer (Redis Streams), configuration module (adapter registry, shared types), and health check endpoint.

**Acceptance Criteria**:
- [ ] Project boots with `npm start`, connects to Redis, emits "ready" log
- [ ] Configuration loaded from environment + YAML file, validated on startup
- [ ] `GET /health` returns `{ status: "ok", uptime, connected_services }`
- [ ] Shared TypeScript types exported: `RawTelemetry`, `NormalizedTelemetry`, `AlertEvent`
- [ ] Redis Stream consumer group created on startup, consumer reads messages without processing

**Estimated**: S | **Blocked by**: none

---

### I-002: MQTT Protocol Adapter — M

**Description**: Implement the MQTT ingress adapter. Connect to MQTT broker (configurable host/port/topic), subscribe to per-robot telemetry topics (`robot/{id}/telemetry`), parse binary payload into `RawTelemetry`, push to Redis Stream `telemetry:raw`. Handle reconnection with exponential backoff.

**Acceptance Criteria**:
- [ ] Connects to MQTT broker using mqtt.js, subscribes to wildcard topic `robot/+/telemetry`
- [ ] Parses binary payload per topic-specific schema (message format versioned in header)
- [ ] Pushes `RawTelemetry { robot_id, timestamp, source: "mqtt", raw_payload, format_version }` to Redis Stream
- [ ] Reconnection: exponential backoff (1s → 30s max), logs each attempt
- [ ] Graceful shutdown: unsubscribe, close connection, flush pending messages
- [ ] Unit test: mock MQTT broker, verify 3 message types parsed correctly

**Estimated**: M | **Blocked by**: I-001

---

### I-003: BFF Project Scaffold — S

**Description**: Initialize the BFF (Backend For Frontend) as a Fastify + TypeScript modular monolith. Set up module registry, shared middleware (auth stub, request logging, CORS, error handler), configuration, and the Fastify plugin-based module loader.

**Acceptance Criteria**:
- [ ] Fastify server boots on configurable port, returns `{ status: "ok" }` at `GET /api/health`
- [ ] Module loader: each module in `src/modules/<name>/` auto-registers routes via Fastify plugin pattern
- [ ] Shared middleware: request ID injection, structured JSON logging (pino), CORS for dev, global error handler
- [ ] Configuration: `src/config.ts` reads from env vars with Zod validation, typed exports
- [ ] `npm run dev` starts with hot-reload (tsx watch)

**Estimated**: S | **Blocked by**: none

---

### I-004: PostgreSQL Schema + Migrations — M

**Description**: Design and implement the PostgreSQL schema for configuration, users, alerts, and collaboration. Write forward + rollback migrations. Include seed data for development.

**Acceptance Criteria**:
- [ ] Tables: `robots` (id, name, model, config JSONB, status, connected_at), `users` (id, name, email, role), `alert_rules` (id, robot_id FK, metric, operator, threshold, severity), `alert_events` (id, rule_id FK, robot_id FK, triggered_at, acknowledged_at, acknowledged_by FK, dismissed_at, status), `comments` (id, robot_id FK, user_id FK, body, parent_id, created_at), `config_audit_log` (id, robot_id FK, user_id FK, field, old_value, new_value, changed_at)
- [ ] Migrations: numbered, timestamped, with up/down in same file
- [ ] Foreign keys: all relationships explicit, ON DELETE behavior documented
- [ ] Indexes: `robots(status)`, `alert_events(robot_id, status)`, `alert_events(triggered_at DESC)`, `comments(robot_id, created_at)`, `config_audit_log(robot_id, changed_at DESC)`
- [ ] Seed: 5 sample robots with varied configs, 2 users, 3 sample alert rules
- [ ] Rollback migration verified: down migration drops all tables cleanly

**Estimated**: M | **Blocked by**: none

---

### I-005: TimescaleDB Schema + Hypertables — M

**Description**: Design the TimescaleDB schema for robot telemetry time-series data. Create hypertable for normalized telemetry, configure chunk intervals, set up retention and compression policies.

**Acceptance Criteria**:
- [ ] Table `telemetry` (robot_id TEXT, timestamp TIMESTAMPTZ, battery_pct FLOAT, joint_temps JSONB, cpu_pct FLOAT, mem_pct FLOAT, network_latency_ms FLOAT, gps_lat FLOAT, gps_lon FLOAT, task_status TEXT, raw_source TEXT, ingestion_lag_ms INT)
- [ ] Hypertable: `SELECT create_hypertable('telemetry', 'timestamp', chunk_time_interval => INTERVAL '1 day')`
- [ ] Index: `(robot_id, timestamp DESC)` for per-robot queries
- [ ] Compression: enabled on chunks older than 7 days (chunk_time_interval per segmentby robot_id)
- [ ] Retention: auto-drop chunks older than 90 days (configurable)
- [ ] Continuous aggregate: `telemetry_hourly` for downsampled fleet overview queries (AVG battery, AVG cpu, COUNT)
- [ ] Migration file with up/down

**Estimated**: M | **Blocked by**: none

---

### I-006: Design Token System — S

**Description**: Define the design token architecture for the dashboard. Color palette (light + dark modes for fleet monitoring context — high contrast, low eye strain for long shifts), spacing scale, typography scale, component-level tokens (card, badge, alert severity colors), motion tokens.

**Acceptance Criteria**:
- [ ] CSS custom properties file generated: `tokens.css` with `--color-*`, `--spacing-*`, `--font-*`, `--motion-*`, `--shadow-*`
- [ ] Semantic tokens: `--color-status-online` (green), `--color-status-offline` (gray), `--color-status-error` (red), `--color-severity-critical` (red), `--color-severity-warning` (amber), `--color-severity-info` (blue)
- [ ] Dark mode: all tokens have `.dark` variant defined
- [ ] Typography: monospace for data values, sans-serif for UI, sizes 11px–24px
- [ ] Spacing: 4px base unit, scale: 4, 8, 12, 16, 24, 32, 48, 64
- [ ] Motion: `--motion-fast: 150ms`, `--motion-normal: 250ms`, `--motion-slow: 400ms`

**Estimated**: S | **Blocked by**: none

---

### I-007: HTTP Adapter + JSON Normalizer — M

**Description**: Implement HTTP ingress adapter. Accept POST `RawTelemetry`, validate schema, push to Redis Stream. Normalize raw JSON fields to unified schema via mapping configuration.

**Acceptance Criteria**:
- [ ] `POST /ingest/http` accepts JSON body with `robot_id`, `timestamp`, `payload`
- [ ] Request validation: Zod schema, rejects malformed payloads with 400
- [ ] Normalizer reads field mappings from YAML config (e.g., `batt_pct → battery_pct`, multiply by 100 if needed)
- [ ] Output `NormalizedTelemetry` pushed to Redis Stream `telemetry:normalized`
- [ ] Unit test: 3 different raw JSON formats (from 3 robot models) all normalize to same schema
- [ ] Error handling: malformed payload logged but pipeline continues

**Estimated**: M | **Blocked by**: I-001, I-002 (shares Pipeline scaffold + shared types)

---

### I-008: gRPC Adapter + Protobuf Normalizer — M

**Description**: Implement gRPC ingress adapter. Start gRPC server, receive `TelemetryReport` proto messages, deserialize Protobuf, normalize to unified schema, push to Redis Stream.

**Acceptance Criteria**:
- [ ] gRPC server started on configurable port, serves `TelemetryService.ReportTelemetry` RPC
- [ ] Proto file(s) compiled to TypeScript stubs
- [ ] Deserialization handles multiple proto versions (version field in message header → different normalizer)
- [ ] Normalized output identical to HTTP adapter for same robot model
- [ ] Unit test: mock gRPC client, send known proto payload, verify normalized output matches expected
- [ ] Error handling: invalid proto → gRPC error status + logged

**Estimated**: M | **Blocked by**: I-001, I-002

---

### I-009: Schema Mapper Engine — M

**Description**: Implement the configuration-driven normalization engine. Load robot-model-specific field mappings from YAML, apply unit conversions, field renames, and default value injection. This is the core of the data pipeline.

**Acceptance Criteria**:
- [ ] YAML mapping files: `mappings/{robot_model}.yaml` with schema `{ fields: [{ raw_path, target_field, transform?, unit_conversion? }] }`
- [ ] Transforms: `identity`, `multiply(factor)`, `divide(factor)`, `offset(value)`, `enum_map({...})`, `timestamp_parse(format)`
- [ ] Unit conversions: automatic lookup (e.g., `mV→V` divides by 1000, `°F→°C` formula)
- [ ] Mapping validation on load: all target fields exist in `NormalizedTelemetry` type, no duplicate targets
- [ ] Hot-reload: watch mapping directory, reload without restart
- [ ] Unit test: 5 transform types tested, unknown transform → logged error + identity fallback

**Estimated**: M | **Blocked by**: I-001

---

### I-010: TSDB Writer (Batch + Events) — M

**Description**: Implement the TimescaleDB writer. Consume from Redis Stream `telemetry:normalized`, batch-write to TimescaleDB, publish write events to Redis Pub/Sub for WebSocket fan-out.

**Acceptance Criteria**:
- [ ] Consumer reads from `telemetry:normalized` stream in batches of 100 or 500ms window (whichever first)
- [ ] Batch INSERT into TimescaleDB using `INSERT ... ON CONFLICT DO NOTHING`
- [ ] After each batch, publish `{ type: "telemetry_update", robot_ids: [...], count: N }` to Redis channel `events:telemetry`
- [ ] Metrics: batch size, write latency, error count exposed via `/metrics` endpoint
- [ ] Retry: failed batch retried once, then individual rows retried, failures logged
- [ ] Backpressure: if consumer group lag > 1000, skip non-critical fields (task_status) and alert

**Estimated**: M | **Blocked by**: I-005, I-009

---

### I-011: Robot Module (BFF CRUD) — M

**Description**: Implement the Robot management module in BFF. CRUD endpoints for robot registry, status queries, real-time status subscription hooks.

**Acceptance Criteria**:
- [ ] `GET /api/robots` — list all robots with current status, filterable by status/group
- [ ] `GET /api/robots/:id` — single robot with latest telemetry snapshot (from TSDB)
- [ ] `POST /api/robots` — register new robot (generates robot_id, returns registration token for edge gateway)
- [ ] `PATCH /api/robots/:id` — update robot name, group, metadata
- [ ] `DELETE /api/robots/:id` — soft-delete (marks inactive, preserves history)
- [ ] Robot status derived: online (last telemetry < 30s ago), delayed (30s–5min), offline (>5min)
- [ ] Integration test: CRUD cycle passes, status derivation correct for boundary times

**Estimated**: M | **Blocked by**: I-003, I-004

---

### I-012: WebSocket Hub — M

**Description**: Implement the WebSocket hub in BFF. Authenticate connections, manage subscription channels, fan-out telemetry and alert events from Redis Pub/Sub to connected clients.

**Acceptance Criteria**:
- [ ] WebSocket upgrade on `ws://host/ws?token=...` with JWT auth
- [ ] Channels: `fleet:overview` (aggregated stats), `robot:{id}` (per-robot telemetry), `alerts` (all alert events)
- [ ] Client subscribes/unsubscribes via WS message `{ type: "subscribe", channel: "..." }`
- [ ] Redis Pub/Sub listener forwards to subscribed WS clients
- [ ] Heartbeat: server sends ping every 30s, disconnects after 2 missed pongs
- [ ] Connection limit: max 100 concurrent, rejects with 503 if exceeded
- [ ] Metrics: connected clients, messages/sec, dropped messages

**Estimated**: M | **Blocked by**: I-003

---

### I-013: Fleet Overview API + Aggregation — M

**Description**: Build the fleet aggregation layer. Endpoints for fleet-level statistics, time-series aggregations for dashboard charts.

**Acceptance Criteria**:
- [ ] `GET /api/fleet/overview` — returns `{ total, online, offline, error, avg_battery, avg_cpu, alert_count }`
- [ ] `GET /api/fleet/trends?window=1h|6h|24h|7d` — returns time-series arrays: `{ timestamps[], battery_avg[], cpu_avg[], online_count[], alert_count[] }`
- [ ] Uses TimescaleDB continuous aggregates for queries > 1h
- [ ] Response cached in Redis for 15s for fleet overview, 60s for trends
- [ ] Integration test: verify aggregation values match raw data

**Estimated**: M | **Blocked by**: I-010, I-011

---

### I-014: Robot Detail API + Time-series — M

**Description**: Build the per-robot detail API with raw telemetry time-series, status history, alert history.

**Acceptance Criteria**:
- [ ] `GET /api/robots/:id/telemetry?from=&to=&interval=raw|1m|5m|1h` — time-series data points
- [ ] Downsampling: automatic switch to continuous aggregates for wide time ranges
- [ ] `GET /api/robots/:id/alerts?status=active|acknowledged|dismissed` — alert history for robot
- [ ] `GET /api/robots/:id/status-history?from=&to=` — status transitions with timestamps
- [ ] Gap detection: if gap > expected_interval * 2, response marks `{ gap: true, gap_duration_seconds }`
- [ ] Response streaming: for > 1000 data points, use NDJSON streaming

**Estimated**: M | **Blocked by**: I-010, I-011, I-005

---

### I-015: Alert Rule Engine + State Machine — M

**Description**: Implement the alert evaluation engine inside the data pipeline. Evaluate each normalized telemetry point against configured rules, maintain alert state machine.

**Acceptance Criteria**:
- [ ] Rule evaluation: after each NormalizedTelemetry, check all rules for that robot
- [ ] Rule DSL: `{ metric, operator (>, <, ==, !=), threshold, severity (critical|warning|info), cooldown_seconds }`
- [ ] State machine: `dormant → triggered → acknowledged → dismissed`
- [ ] Cooldown: same alert rule fires at most once per cooldown period
- [ ] Deduplication: same (robot, rule) doesn't re-trigger while in `triggered` state
- [ ] Alert event published to Redis Pub/Sub `events:alerts`
- [ ] Unit test: rule triggers, cooldown honored, dedup works, state transitions correct

**Estimated**: M | **Blocked by**: I-010

---

### I-016: Alert API + Notification Hub — M

**Description**: Build the alert management API in BFF + browser notification bridge.

**Acceptance Criteria**:
- [ ] `GET /api/alerts?status=&severity=&robot_id=&page=` — paginated alert list
- [ ] `POST /api/alerts/:id/acknowledge` — marks alert acknowledged by current user
- [ ] `POST /api/alerts/:id/dismiss` — dismisses alert (after resolution)
- [ ] `POST /api/alerts/:id/snooze?duration=5m` — snoozes alert rule for duration
- [ ] WebSocket push: new alert → subscribed clients immediately
- [ ] Sound notification: configurable per severity (critical: alarm, warning: chime, info: silent)
- [ ] Browser Notification API: show notification even when tab is backgrounded
- [ ] Integration test: alert lifecycle: trigger → WS push → acknowledge → dismiss

**Estimated**: M | **Blocked by**: I-015, I-012

---

### I-017: History Query + Downsampling API — M

**Description**: Build the history service for past telemetry queries with automatic downsampling and gap detection.

**Acceptance Criteria**:
- [ ] `GET /api/history/robot/:id?from=&to=&metrics[]=&interval=` — multi-metric time-series
- [ ] Automatic downsampling: raw for < 1h, 1m for < 24h, 5m for < 7d, 1h for < 30d
- [ ] Gap detection: marks data gaps with `null` entries, gap boundaries annotated
- [ ] Multi-robot comparison: `GET /api/history/compare?robots[]=&metric=&from=&to=` — returns aligned time-series
- [ ] Export hints: response includes `total_points, estimated_csv_size_bytes`
- [ ] Performance: < 500ms for 7-day query on single robot

**Estimated**: M | **Blocked by**: I-010, I-005

---

### I-018: Config Module (CRUD + Sync) — M

**Description**: Implement robot configuration management in BFF. CRUD for per-robot configs, audit logging, and edge sync status.

**Acceptance Criteria**:
- [ ] `GET /api/robots/:id/config` — current config with last-modified info
- [ ] `PUT /api/robots/:id/config` — update config (sample_rate, alert_thresholds, etc.), write audit log
- [ ] `GET /api/robots/:id/config/history` — audit trail with who/when/what changed
- [ ] Config sync: `GET /api/robots/:id/config/status` returns `{ applied: bool, applied_at, version }`
- [ ] Validation: thresholds have min/max bounds, sample_rate in [1, 30] seconds
- [ ] Integration test: change config → verify audit log → verify status reflects change

**Estimated**: M | **Blocked by**: I-004, I-011

---

### I-019: Collaboration Module — M

**Description**: Implement commenting and @mention system for robot-specific collaboration threads.

**Acceptance Criteria**:
- [ ] `GET /api/robots/:id/comments?page=` — threaded comments for a robot
- [ ] `POST /api/robots/:id/comments` — create comment, supports `@username` mentions and `parent_id` for replies
- [ ] `PATCH /api/comments/:id` — edit own comment (within 15 min window)
- [ ] `DELETE /api/comments/:id` — soft-delete own comment
- [ ] @mention parsing: extracts `@username`, sends WebSocket notification to mentioned user
- [ ] Activity indicator: `GET /api/robots/:id/activity` returns `{ active_users: [{user, last_action}], comment_count, last_comment_at }`
- [ ] Integration test: create thread → reply → @mention → verify notification delivered

**Estimated**: M | **Blocked by**: I-004, I-012

---

### I-020: Dashboard Shell (Layout/Theme/i18n) — M

**Description**: Build the React SPA shell with layout system, theme provider, i18n framework, and route structure.

**Acceptance Criteria**:
- [ ] React 18 + TypeScript + Vite project scaffolded
- [ ] Layout: sidebar navigation (collapsible), top bar (user info, alert badge), content area
- [ ] Routes: `/` → Fleet Overview, `/robot/:id` → Detail, `/alerts` → Alert Panel, `/config/:id` → Config, `/history/:id` → History Explorer, `/reports` → Reports, `/settings` → Settings
- [ ] Theme: light/dark mode toggle persisted in localStorage, CSS custom properties from design tokens
- [ ] i18n: react-intl setup, Chinese + English, locale switcher persisted
- [ ] Responsive: sidebar collapses to bottom tab bar on mobile (< 768px)
- [ ] Global state: Zustand stores for `auth`, `theme`, `i18n`, `websocket`

**Estimated**: M | **Blocked by**: I-006

---

### I-021: Fleet Overview Page — M

**Description**: Build the fleet overview dashboard page with status ring chart, trend line charts, robot card grid, and map view.

**Acceptance Criteria**:
- [ ] Status ring chart: online/offline/error ratio, clickable sectors → filtered robot list
- [ ] Trend charts: 3 charts (avg battery %, avg CPU %, online count) with time window selector (1h/6h/24h/7d)
- [ ] Robot card grid: responsive grid, each card shows name, status dot, battery bar, CPU %, last seen
- [ ] Search/filter: text search by name, filter by status, sort by battery/cpu/name
- [ ] Real-time: cards update via WebSocket (status dot, battery, CPU change)
- [ ] Map: leaflet or maplibre, robot markers colored by status, cluster at zoom < 12
- [ ] Performance: initial render < 1s, updates via WS without full re-render

**Estimated**: M | **Blocked by**: I-013, I-020

---

### I-022: Robot Detail Page — L

**Description**: Build the per-robot detail page with 6-panel data dashboard, real-time time-series chart, map, alert history, comment thread, and config quick-edit.

**Acceptance Criteria**:
- [ ] 6 metric panels: Battery (gauge), Joint Temps (heatmap grid), CPU (gauge + sparkline), Memory (gauge), Network Latency (sparkline), GPS (mini-map)
- [ ] Time-series chart: interactive (zoom/pan), multi-metric toggle, with gap indicators
- [ ] Map: robot position with trail (last N positions), clickable marker
- [ ] Alert history: inline table, last 20 alerts for this robot
- [ ] Comment thread: below fold, real-time updates
- [ ] Config quick-edit: expandable panel for alert thresholds
- [ ] Responsive: 2-column on tablet, 3-column on desktop, single-column on mobile
- [ ] Performance: detail page load < 1.5s

**Estimated**: L | **Blocked by**: I-014, I-020

---

### I-023: Alert Panel + Notification UI — M

**Description**: Build the alert management page with filterable alert list, alert detail modal, notification toast system, and sound alerts.

**Acceptance Criteria**:
- [ ] Alert list: table with columns (severity icon, time, robot, rule, status, actions), filterable by severity/status/robot
- [ ] Inline actions: acknowledge, dismiss, snooze, jump to robot detail
- [ ] Toast notifications: slide-in from top-right for new critical alerts, auto-dismiss after 10s
- [ ] Sound: Web Audio API tones for critical (250Hz pulse) and warning (440Hz chime)
- [ ] Browser notification: `Notification.requestPermission()` flow, push alert summary
- [ ] Alert count badge in sidebar/topbar, updates via WS
- [ ] Mobile: alert toasts stack at top, swipe-to-dismiss

**Estimated**: M | **Blocked by**: I-016, I-020

---

### I-024: Config Panel — M

**Description**: Build the robot configuration page with form-based threshold editing, audit history, and sync status.

**Acceptance Criteria**:
- [ ] Configuration form: grouped by category (Alert Thresholds, Sampling, Network), sliders + number inputs
- [ ] Validation: client-side bounds checking, range visualization (current value highlighted on range bar)
- [ ] History: table showing who changed what and when, with diff view for each change
- [ ] Sync status: indicator showing config version on robot vs configured version, "Sync Now" button
- [ ] Save: requires confirmation with summary of changes, then `PUT` to API
- [ ] Undo: revert to last saved state within 30s of save

**Estimated**: M | **Blocked by**: I-018, I-020

---

### I-025: History Explorer — M

**Description**: Build the time-series history exploration page with interactive chart, metric selection, comparison mode, and export.

**Acceptance Criteria**:
- [ ] Robot selector: dropdown with search, supports selecting 1 or 2 robots for comparison
- [ ] Metric selector: multi-select checkboxes (battery, CPU, memory, latency, joint temps avg)
- [ ] Time range: date range picker + presets (Last 1h, 6h, 24h, 7d, 30d)
- [ ] Chart: interactive (zoom, pan, tooltip on hover), dual Y-axis for comparison mode
- [ ] Gap visualization: gaps shown as shaded regions or breaks in line
- [ ] Export: download as CSV, or "Copy chart as PNG"
- [ ] Performance: lazy-load data on scroll/zoom, progressive rendering for > 10K points

**Estimated**: M | **Blocked by**: I-017, I-020

---

### I-026: Report Engine (PDF/Excel) — M

**Description**: Implement the report generation engine. Produce snapshot reports (PDF) and data exports (Excel) for fleet and per-robot data.

**Acceptance Criteria**:
- [ ] `POST /api/reports` with body `{ type: "fleet"|"robot", robot_id?, time_range: {from, to} }`
- [ ] Fleet report: summary stats, trend chart image, alert summary table, robot status list
- [ ] Robot report: detail stats, time-series chart image, alert log, config snapshot
- [ ] PDF generation: using puppeteer or pdfkit, styled with dashboard theme
- [ ] Excel export: using exceljs, separate sheets for summary + raw data
- [ ] Async generation: endpoint returns `{ report_id, status: "generating" }`, poll `GET /api/reports/:id` for status, then download URL
- [ ] Report expires: download URL expires after 1 hour

**Estimated**: M | **Blocked by**: I-017

---

### I-027: Map View + Clustering — L

**Description**: Build the fleet map view with real-time position updates, marker clustering, and robot detail overlay.

**Acceptance Criteria**:
- [ ] Full-screen map mode (toggle from fleet overview)
- [ ] Robot markers: colored by status, oriented by heading (optional), click → detail popup
- [ ] Clustering: supercluster or similar, aggregates nearby robots with count badge
- [ ] Real-time: markers move smoothly (interpolate between position updates)
- [ ] Trail lines: show last 10 positions as fading line behind marker
- [ ] Geofence overlay: configurable geofence polygons, alert if robot exits fence
- [ ] Base map: toggle between street/satellite/dark tiles
- [ ] Performance: 100+ robots with clustering at < 30 FPS

**Estimated**: L | **Blocked by**: I-014, I-020

---

### I-028: Dark Mode + Theme Switching — S

**Description**: Implement dark mode theme with smooth transition, persisted preference, and system preference detection.

**Acceptance Criteria**:
- [ ] Theme toggle in top bar (sun/moon icon), smooth CSS transition (200ms) on theme change
- [ ] All components render correctly in both themes (audit every page)
- [ ] Preference chain: localStorage → system preference (`prefers-color-scheme`) → default light
- [ ] Dark-optimized chart colors: higher contrast, dimmer grid lines
- [ ] Alert severity colors remain distinguishable in both modes

**Estimated**: S | **Blocked by**: I-006, I-020

---

### I-029: E2E Tests + Load Testing — L

**Description**: Write end-to-end tests for all critical user journeys and perform load testing on the API.

**Acceptance Criteria**:
- [ ] Playwright E2E tests: 3 user journeys (discover & fix fault, change config, export report)
- [ ] API integration tests: all endpoints, auth, error cases
- [ ] WS integration tests: subscription, message delivery, reconnection
- [ ] Load test: k6 or artillery, simulate 50 concurrent users, 1000 robots reporting every 5s
- [ ] Performance baselines: API p95 < 200ms, WS latency < 500ms, page load < 2s
- [ ] CI integration: tests run in GitHub Actions on PR

**Estimated**: L | **Blocked by**: All Phase 6

---

### I-030: DevOps: Docker Compose + CI/CD — M

**Description**: Containerize all services, write docker-compose for local dev and production-like deployment, set up CI/CD pipeline.

**Acceptance Criteria**:
- [ ] Dockerfiles: BFF (multi-stage Node.js), Data Pipeline (Node.js), Frontend (nginx serving static)
- [ ] docker-compose.yml: postgres + timescaledb + redis + bff + pipeline + frontend, with health checks
- [ ] docker-compose.prod.yml: production overrides (resource limits, restart policies, secrets)
- [ ] GitHub Actions: lint, test, build images, push to registry on main
- [ ] Dev experience: `docker compose up` → full stack running locally in < 60s
- [ ] Seed data: docker compose automatically seeds dev DB with sample robots + 24h of telemetry

**Estimated**: M | **Blocked by**: All

---

## Dependency Validation

```
Acyclic check: PASSED
  Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7
  No reverse edges detected.

Longest chain: I-001 → I-009 → I-010 → I-014 → I-022 (5 hops)
Most dependents: I-020 (6 dependents: I-021, I-022, I-023, I-024, I-025, I-028)

Blocked-by count per phase:
  Phase 1: 0 blocked
  Phase 2: 5 issues, blocked by Phase 1
  Phase 3: 2 issues, blocked by Phase 2
  Phase 4: 2 issues, blocked by Phase 3
  Phase 5: 2 issues, blocked by Phase 3
  Phase 6: 6 issues, blocked by Phases 3-5
  Phase 7: 4 issues, blocked by Phase 6
```

## Completion Report

**what_was_done**: Decomposed PRD's 21 user stories + 7 modules into 30 independently implementable issues across 7 phases, with acceptance criteria, size estimates, and acyclic dependency graph.

**key_decisions**:
- **decision**: 7-phase split (Foundation → Core Data → Real-time → Alerts/History → Config/Collab → Frontend → Polish)
  **rationale**: Maximizes parallelism — Phase 1 items share no dependencies, enabling 5 parallel workstreams from day one
- **decision**: Frontend delayed to Phase 6
  **rationale**: All frontend pages depend on APIs; building UI against mock data would require rewriting all data fetching when APIs diverge. The architecture's modular monolith allows BFF APIs to stabilize before UI work begins.
- **decision**: Data Pipeline and BFF as separate Phase 1 scaffolds
  **rationale**: These services have different scaling profiles and deployment cadences per ADR-001. Independent scaffolds prevent coupling at project structure level.

**handoff_focus**: senior-engineer should start Phase 1 implementation (I-001, I-003 concurrently); database-engineer should cover I-004 + I-005; senior-frontend can prepare design tokens (I-006)

**open_questions**:
- I-026 (Report Engine): PDF generation approach (puppeteer vs pdfkit) depends on whether we need exact visual fidelity to dashboard

**known_constraints**:
- Phase 6 frontend work is blocked on BFF API completion; parallel frontend mock-data development is intentionally de-scoped
