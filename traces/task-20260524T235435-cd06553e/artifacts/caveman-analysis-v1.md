# Caveman Simplification: 机器人车队运维监控面板

## Reduce to First Principles

9 requirements → 4 core invariants:

### Invariant 1: Every robot is a stream of numbers.
All 9 requirements collapse to: receive numbers → store numbers → show numbers → alert on numbers. The "heterogeneous data" requirement is just: receive arbitrary-packet → map-to-uniform-numbers before anything else.

### Invariant 2: The operator's job is to answer one question fast.
"Which robot needs my attention right now?"
Everything else (history, reports, config, comments) is secondary to this one question. The dashboard must answer it in ≤ 10 seconds.

### Invariant 3: Alerts are only useful if they fire ONCE per incident.
Alert dedup + cooldown + state machine is the entire alert system. Not rules. Not thresholds. Not notifications. Those are configuration. The architecture IS the state machine: `dormant → triggered → acknowledged → dismissed`.

### Invariant 4: Config is audit trail, not CRUD.
The value of configuration management is knowing WHO changed WHAT and WHEN — not the form fields. CRUD is trivial. Audit log with diff is the actual feature.

## What the System IS

```
Robots → [Numbers] → [Store] → [Show + Alert] → Operator
                         ↑
                    [Config + Audit]
```

## What the System is NOT

- Not a robot control panel (no actuation commands)
- Not an analytics platform (no ML/predictive)
- Not a fleet management system (no mission planning)
- Not a CI/CD pipeline (no software deployment to robots)

## Risk: Scope creep into "we should also..."

The biggest risk is adding features before the core loop works:
1. Get numbers flowing (MQTT → Redis → TSDB) ← DO THIS FIRST
2. Show numbers on screen (WebSocket → React) ← DO THIS SECOND
3. Alert on numbers (rule eval → WS push → toast) ← THEN THIS
4. THEN config, history, reports, comments, etc.

## Recommendation

Architect for all 9 domains but IMPLEMENT in exactly this order. Every domain after #3 is nice-to-have. If the core loop (ingest → show → alert) doesn't work in Week 1, nothing else matters.
