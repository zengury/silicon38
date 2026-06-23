# Issue Decomposition: Robot Fleet Ops Dashboard

## Priority Tiers

| Tier | Description |
|------|-------------|
| **P0** | Demo must-have — core monitoring pipeline |
| **P1** | Demo nice-to-have — enhances demo impressiveness |
| **P2** | Post-demo — production hardening |

---

## P0 Issues (Core Pipeline)

### P0-1: Data Normalization Layer + Unified Schema
**Description**: Implement Schema Registry + Adapter pattern. Register 3 adapter types (JSON-A, JSON-B, Protobuf-like). Each adapter normalizes raw data → `RobotTelemetry` schema. Unit conversion, field renaming, missing field defaults.
**Acceptance Criteria**:
- `DataNormalizer.normalize(raw, format)` returns valid `RobotTelemetry` for all 3 formats
- Fields with different units (e.g., Celsius vs Fahrenheit) are converted
- Missing optional fields are filled with schema defaults
- Tests cover all 3 adapters
**Size**: M
**Blocked By**: none

### P0-2: Mock Data Generator
**Description**: Generate realistic mock telemetry for 6 simulated robots. Include: gradual temperature drift, periodic CPU fluctuations, random network latency jitter, robot status transitions (ONLINE → ERROR → ONLINE), location updates. Support configurable anomaly injection for testing alerts.
**Acceptance Criteria**:
- Generator produces valid `RobotTelemetry` at configurable intervals (1s default)
- Each robot has a unique "signature" (different joint count, different baseline temps)
- Anomaly injection API: `injectAnomaly(robotId, type)` for fall / joint-loss / low-battery
- 30-day historical mock data can be generated on demand
**Size**: M
**Blocked By**: P0-1 (needs RobotTelemetry schema)

### P0-3: WebSocket + State Management
**Description**: WebSocket manager with auto-reconnect. Global Zustand store: robots map, alerts array, config, UI state. Telemetry updates flow: WS message → DataNormalizer → AlertEngine → Store update → React re-render.
**Acceptance Criteria**:
- WebSocket connects and subscribes to telemetry channel
- Auto-reconnect with exponential backoff on disconnect
- Store updates trigger React re-renders for subscribed components
- Alert engine runs on every telemetry frame
**Size**: M
**Blocked By**: P0-1 (DataNormalizer), P0-2 (mock data source)

### P0-4: Alert Engine
**Description**: Rule-based alert evaluation. Rules: { metric, operator, threshold, severity }. For Demo: 3 hardcoded rules — fall detected, joint communication lost, battery below threshold. Alert dedup: same robot + same type = 5min cooldown. Alert lifecycle: triggered → acknowledged → resolved.
**Acceptance Criteria**:
- `battery.level < threshold` → WARNING alert fires within 1 telemetry frame
- `status == FALLEN` → CRITICAL alert fires
- `joint.communication == LOST` → CRITICAL alert fires
- Same alert does not fire twice within 5 minutes
- Alert can be acknowledged and archived
**Size**: M
**Blocked By**: P0-1 (RobotTelemetry schema)

### P0-5: Robot Cards + Fleet Overview Page
**Description**: Main page showing all 6 robot cards in a responsive grid. Each card: robot name, battery bar, connection status dot (green/yellow/red), last seen time, current task, alert count badge. Click card → detail drawer.
**Acceptance Criteria**:
- 6 robot cards render in grid layout
- Cards update in real-time (battery bar, status dot)
- Offline robots show with distinct styling (greyed out)
- Cards with active alerts show red border + badge count
- Click card opens detail panel
**Size**: L
**Blocked By**: P0-3 (store + WS)

### P0-6: Dashboard Overview (Charts)
**Description**: Top-of-page dashboard row with: (1) Donut chart — fleet online/offline/error ratio, (2) Line chart — average battery % over last hour, (3) Heatmap — joint temperature per robot × joint, (4) Map — robot locations with Leaflet markers.
**Acceptance Criteria**:
- Donut chart segments update as robot statuses change
- Line chart shows last 60 data points (1 hour at 1/min sampling)
- Heatmap uses color scale: green (normal) → yellow (warm) → red (hot)
- Map markers are positioned correctly and colored by status
**Size**: L
**Blocked By**: P0-3 (store + WS)

### P0-7: Dark/Light Theme + Layout Shell
**Description**: CSS Variables theme system. Toggle button switches all components. Tailwind dark mode integration. Basic responsive layout shell: header (logo + theme toggle + language), main content area, sidebar (alert list).
**Acceptance Criteria**:
- Theme toggle switches all component colors instantly
- All chart components re-render with correct theme colors
- Layout is responsive (collapses to single column on narrow screens)
**Size**: S
**Blocked By**: none (can be done in parallel)

---

## P1 Issues (Demo Polish)

### P1-8: Robot Detail Panel
**Description**: Slide-out panel showing: joint temperature table, CPU/memory gauges, current task progress, status history timeline. "I'm handling this" button. Comment thread.
**Acceptance Criteria**:
- Detail panel shows all sensor data for selected robot
- Joint table color-codes temperature cells
- "I'm handling this" button toggles ownership marker visible on fleet card
**Size**: M
**Blocked By**: P0-5 (robot cards)

### P1-9: Historical Data Viewer
**Description**: Time-series chart for any metric over past 30 days. Select metric (battery, temp, cpu) from dropdown. Time range selector (1h, 6h, 24h, 7d, 30d). Brush zoom on chart.
**Acceptance Criteria**:
- Metric dropdown populated from RobotTelemetry fields
- Chart updates when time range changes
- Brush selection zooms into time range
- Data correctly fetched from historical mock dataset
**Size**: M
**Blocked By**: P0-2 (mock data generator), P0-3 (store)

### P1-10: Config Panel
**Description**: Per-robot configuration form. Fields: alert thresholds (temp max, battery min, latency max), sampling frequency (1s/5s/10s/30s), reconnect strategy (retries, interval, timeout). Changes take effect immediately on alert engine.
**Acceptance Criteria**:
- Config changes are persisted in store
- Alert engine reads updated thresholds on next evaluation
- Sampling frequency change is reflected in mock data generator rate
**Size**: M
**Blocked By**: P0-4 (alert engine), P0-3 (store)

### P1-11: Collaboration Features
**Description**: Comment thread per robot. @mention autocomplete (mock user list). Status badges: "Needs Attention", "In Progress", "Resolved".
**Acceptance Criteria**:
- Comment input with @mention trigger
- @mention dropdown with mock user list (3-4 users)
- Comments render in thread with timestamp
- Status badge can be changed from dropdown
**Size**: M
**Blocked By**: P1-8 (detail panel)

### P1-12: Export (CSV + Browser Print PDF)
**Description**: Export button on robot detail and fleet overview. Robot detail → CSV of metrics over selected time range. Fleet overview → browser print with print-optimized CSS.
**Acceptance Criteria**:
- CSV download contains correct column headers and data rows
- Browser print renders clean report without UI chrome
**Size**: S
**Blocked By**: P0-6 (charts), P1-9 (history)

### P1-13: i18n Framework (zh-CN / en-US)
**Description**: react-i18next setup. Translation JSON files for both languages. Demo: translate main UI labels (dashboard, battery, temperature, alerts, settings). Not all copy.
**Acceptance Criteria**:
- Language toggle in header switches all translated strings
- Charts labels update to selected language
**Size**: S
**Blocked By**: P0-7 (layout shell)

### P1-14: Drag-and-Drop Layout
**Description**: react-grid-layout enabling users to rearrange dashboard cards. Persist layout to localStorage. Preset layouts: Compact, Relaxed, Focus (hides charts, shows cards only).
**Acceptance Criteria**:
- Cards can be dragged to new positions
- Layout persists on page reload
- 3 preset layout buttons in header
**Size**: S
**Blocked By**: P0-6 (dashboard overview)

---

## P2 Issues (Production)

### P2-15: Real WebSocket Backend + InfluxDB
Replace mock data with real WS server + time-series DB. Add authentication.

### P2-16: Complete Protobuf Adapter
Full protobuf schema parsing (not just JSON-like mock).

### P2-17: Server-side PDF Rendering
Puppeteer/Playwright-based PDF generation with charts rendered server-side.

### P2-18: RBAC + Multi-tenant
Role-based access control, organization management, audit logs.

### P2-19: External Integrations
PagerDuty webhook, Slack notifications, Webhook outgoing alerts.

---

## Dependency Graph
```
P0-1 (DataNormalizer) ──┬── P0-2 (MockData) ────── P0-3 (Store+WS)
                         ├── P0-4 (AlertEngine) ────┘
                         │
P0-7 (Theme/Layout) ─────┤
                         │
                    P0-5 (RobotCards) ── P1-8 (DetailPanel) ── P1-11 (Collab)
                    P0-6 (Dashboard) ──── P1-12 (Export)
                                          P1-14 (DragLayout)
                         
P1-9 (History) ─ depends on P0-2 + P0-3
P1-10 (Config) ─ depends on P0-4 + P0-3
P1-13 (i18n) ─── depends on P0-7
```

---

## Completion Report

- **what_was_done**: Decomposed PRD into 19 issues across P0 (7), P1 (7), P2 (5) with acceptance criteria, sizing, and dependency graph
- **key_decisions**: [(1) P0 focuses on core pipeline: normalize → alert → display, (2) Mock data generator is its own issue — enables all downstream testing, (3) P1 items are Demo Polish that enhance impressiveness, (4) P2 deferred to production]
- **handoff_focus**: P0-1 to P0-7 are the demo critical path; architect should align module boundaries with issue boundaries
- **open_questions**: None
- **known_constraints**: All P0 must complete for demo; P1 optional depending on time
- **confidence_differential**: 0.90
