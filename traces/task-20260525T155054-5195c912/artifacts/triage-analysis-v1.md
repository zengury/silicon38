# Triage Analysis: 机器人车队运维监控面板

## Classification

**Task Type**: `architecture` (primary) + `design` (secondary) — `complex/multi-part`

The request asks for architecture方案 AND 主界面设计 (architecture scheme AND main UI design). It spans 12 functional requirements across backend infrastructure, frontend visualization, real-time systems, and collaboration features. This is not a single-feature request — it's a product definition + architecture + design package.

## Scope

### In Scope (12 requirements mapped)

| # | Requirement | Domain | Priority |
|---|-------------|--------|----------|
| 1 | Real-time telemetry display (battery, joint temp, CPU, network, task, GPS) | Monitoring | P0 |
| 2 | Heterogeneous data normalization (JSON/Protobuf → unified schema) | Data Pipeline | P0 |
| 3 | Fleet overview dashboard (ring chart, line chart, heatmap) | Visualization | P0 |
| 4 | Alerting (fall, joint disconnect, low battery) | Alerting | P0 |
| 5 | 30-day history curves per robot | History | P1 |
| 6 | Configuration panel (thresholds, sampling rate, reconnect strategy) | Config | P1 |
| 7 | Engineer collaboration (comments, @mentions, "I'm handling this") | Collaboration | P2 |
| 8 | Report export (PDF/Excel) | Reporting | P2 |
| 9 | Dark/light theme toggle | Theming | P2 |
| 10 | Multi-language (i18n) | i18n | P2 |
| 11 | Draggable custom layout | Layout | P2 |
| 12 | Customer wants feature-complete | Meta | — |

### Out of Scope (explicitly excluded)

- Robot control/command: monitoring only, no actuation
- Mobile native app: web dashboard only (responsive)
- Authentication system: assume existing SSO/OAuth integration point
- Robot hardware integration: edge gateway is a black box — data arrives as messages
- Real-time video streaming from robot cameras
- Predictive maintenance or ML-based anomaly detection
- Billing/subscription/multi-tenancy

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Heterogeneous data normalization — hardest technical problem, no standard robot telemetry schema | Critical | Config-driven mapping engine, model-specific adapters, not hardcoded |
| Real-time at scale — 1000 robots × 5s = 200 msg/s | High | Redis Streams buffering, TSDB batching, WebSocket selective fan-out |
| Alert dedup — same fault firing repeatedly floods the UI | High | State machine: dormant→triggered→acknowledged→dismissed, cooldown per rule |
| Scope creep — 12 requirements, customer wants "feature-complete" | Medium | Phase delivery: P0 first, P1 second, P2 last |

## Recommended Entry Nodes

Per ENCODER.md — `complex/multi-part`:
- `triage` (self — this analysis)
- `caveman` — reduce to first principles

Additional:
- `zoom-out` — map the problem space before architecture decisions
- `ux-researcher-designer` — 12 requirements have heavy UI surface; user research first

Do NOT activate architect yet. Architect needs zoom-out's map and triage's scope as input.

## Downstream Activation Path

```
triage ──→ to-prd (product requirements)
caveman ──→ architect (evaluates: first-principles challenge)
zoom-out ──→ architect (supports: context map)
ux-researcher-designer ──→ ui-design-system (supports)
                         ──→ prototype (triggers: validate dashboard UX)
```

## Completion Report

**what_was_done**: Classified task as complex/multi-part architecture+design with 12 requirements across 8 domains. Defined explicit in-scope (12 items, P0-P2) and out-of-scope (8 items). Identified 3 critical risks with mitigations. Selected 3 entry nodes + self.

**chain_entry**: "12 requirements, 8 domains, P0-P2 priority: normalize data first, show telemetry second, alert third — then config, history, collaboration, export, theming, layout."
