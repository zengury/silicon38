# Zoom-Out — Subsystem Map

## Subsystems (9)

1. **Telemetry Normalization Layer** — reconciles JSON + protobuf into a canonical schema; preserves raw shadow for transparency. Owns type coercion, unit conversion, timestamp alignment. Latency: sub-second.
2. **Realtime Stream Backbone** — low-latency pub-sub to clients; WebSocket session + reconnect. Latency: <200ms.
3. **Alert Engine (deterministic)** — threshold eval, dedup, state lifecycle (triggered → ack → resolved). Reads thresholds from Config Store. Latency: <2s.
4. **History Store (time-series)** — append-only 30-day store; partitioned by (robot, metric). Latency: minutes.
5. **Configuration Store** — per-robot thresholds, sampling, reconnect strategy. Versioned writes. Latency: seconds.
6. **Collaboration & Mention Registry** — claim/release state, comments. Latency: seconds.
7. **Export Pipeline (async)** — long-running PDF/Excel generation off the hot path. **NOTE: caveman moved this out of the product. Subsystem still mapped; architect may drop.**
8. **Presentation State & Layout Manager** — client-side layout/theme/i18n. **NOTE: caveman cut F9; subsystem shrinks to "system dark + OS locale only."**
9. **Notification Dispatcher** — external channels (Slack/SMS/email/push) for alerts and @-mentions.

## Coupling diagram

```
Upstream (DDS/gRPC/REST)
        │
        ▼
┌──────────────────────────┐
│ Telemetry Normalization  │
└────┬─────────────┬───────┘
     │             │
     ▼             ▼
┌─────────┐   ┌─────────────┐
│Realtime │   │  History    │
│ Stream  │   │  Store      │
└────┬────┘   └─────────────┘
     │
     ├──► (WebSocket → Frontend)
     │
     ▼
┌──────────────┐    ┌──────────────┐
│ Alert Engine │◄──►│  Config      │
└──────┬───────┘    │  Store       │
       │            └──────────────┘
       ▼
┌──────────────────┐   ┌──────────────────┐
│ Collab/Mention   │   │ Notification     │
│ Registry         │──►│ Dispatcher       │
└──────────────────┘   └──────────────────┘
```

## Risks

| Risk | Where | Mitigation |
|------|-------|------------|
| Mention parsing blocks stream | Realtime → Collab | Async mention worker; don't block stream. |
| Export contends with realtime ingest | Export ↔ History | Read replica / snapshot for export. |
| Config update race | Config ↔ Alert | Versioned config; alert reads latest at eval time. |
| Notification storm | Alert → Dispatcher | Per-robot rate-limit + 60s dedup window. |
| Reconnect loses queued alerts | Frontend ↔ Stream | On reconnect, query Alert Engine for active unacked. |

## NOT mine to decide
- Schema, broker, time-series DB, queue tech → **architect**
- Canonical wire contract → **api-designer**
- Storage schema for config & collab → **database-engineer**
- Client persistence approach → **senior-frontend**
