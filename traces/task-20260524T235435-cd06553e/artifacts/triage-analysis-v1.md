# Triage Analysis: 机器人车队运维监控面板

## Task Classification

**Task Type**: `architecture` (primary) + `design` (secondary)

**Rationale**: The request spans architecture design (data pipeline, modular monolith, TSDB schema) and UI/UX design (dashboard layout, real-time visualizations, alert flows, configuration panels, theming). The output is a design package — architecture decision records, UX specifications, design system, and implementation scaffold — not a fully built product.

## Scope

### In Scope (9 requirements parsed)

1. Real-time telemetry monitoring dashboard (fleet overview + per-robot detail)
2. Heterogeneous data ingestion & normalization (MQTT/HTTP/gRPC → unified schema)
3. Fleet-level aggregation (health stats, trends, ring chart)
4. Alert engine (rule evaluation, state machine, notification)
5. Historical time-series query & visualization
6. Robot configuration management (CRUD + audit + sync)
7. Collaboration (comments, @mentions, activity indicators)
8. Report engine (PDF/Excel export)
9. Theming (dark/light) + i18n (Chinese/English)

### Out of Scope (explicitly excluded)

- Actual robot hardware integration — assume data arrives at edge gateway
- Authentication system (stub only — assume existing SSO/OAuth)
- Mobile native app — web-only dashboard (responsive)
- Robot control/command — monitoring only, no actuation
- Billing/subscription — single-team ops tool

## Severity/Complexity

**Complexity: High** — 9 functional domains, 2 databases (PostgreSQL + TimescaleDB), 3 ingestion protocols, real-time WebSocket, stateful alert engine. Multi-module architecture required.

**Risk Areas**:
- Heterogeneous data normalization: schema evolution across robot models is the hardest technical problem
- Real-time WebSocket at scale: 1000 robots × 5s interval = 200 msg/s. Needs backpressure design.
- Alert dedup & cooldown: state machine correctness under concurrent evaluation

## Entry Node Selection

Per ENCODER.md:
- `architecture` → `zoom-out` + `architect`
- `design` (secondary) → `ux-researcher-designer`

However, given the task is complex/multi-part with 9 domains:
- `triage` (entry for complex/multi-part) — classify and simplify first
- `caveman` (parallel entry for complex/multi-part) — reduce to first principles

## Recommendation

Activate triage + caveman as entry nodes. They will:
1. Triage: confirm scope boundaries, identify out-of-scope items
2. Caveman: distill 9 requirements to 3-4 core invariants

Then propagate:
- to-prd (from triage) → formal PRD
- ux-researcher-designer (from triage may_trigger, condition: "user-facing interface") → UX spec
- architect (from zoom-out supports) → ADRs
