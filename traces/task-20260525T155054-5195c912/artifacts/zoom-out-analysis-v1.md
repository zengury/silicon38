# Context Map: 机器人车队运维监控面板

## System Boundary

```
┌──────────────────────────────────────────────────────────────┐
│                    Robot Fleet Ops Dashboard                 │
│                                                              │
│  ┌────────────┐  ┌───────────┐  ┌─────────┐  ┌───────────┐ │
│  │ Data       │  │ Real-time │  │ Fleet   │  │ Alert     │ │
│  │ Pipeline   │→ │ Telemetry │→ │ Overview│  │ Engine    │ │
│  │ (ingest +  │  │ (WebSocket│  │ (charts │  │ (rules +  │ │
│  │  normalize)│  │  + cache) │  │  + map) │  │  state)   │ │
│  └────────────┘  └───────────┘  └─────────┘  └───────────┘ │
│                                                              │
│  ┌────────────┐  ┌───────────┐  ┌─────────┐  ┌───────────┐ │
│  │ History    │  │ Config    │  │ Collab- │  │ Report    │ │
│  │ Service    │  │ Service   │  │ oration │  │ Engine    │ │
│  │ (TSDB      │  │ (CRUD +   │  │ (comments│  │ (PDF/     │ │
│  │  queries)  │  │  audit)   │  │  + @)    │  │  Excel)   │ │
│  └────────────┘  └───────────┘  └─────────┘  └───────────┘ │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Shell: Theme/i18n/Layout/Drag                        │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
    ┌────┴────┐         ┌────┴────┐          ┌────┴────┐
    │ Robot   │         │ Timescale│          │ Redis   │
    │ Edge    │         │ DB       │          │ Cache   │
    │ Gateway │         │ (TSDB)   │          │ + Pub/Sub│
    └─────────┘         └─────────┘          └─────────┘
```

## Module Map

| Module | Responsibility | Dependencies | External |
|--------|---------------|--------------|----------|
| Data Pipeline | Receive MQTT/HTTP/gRPC, normalize to unified schema, write to TSDB | — | Robot Edge Gateway, Redis Streams |
| Real-time Telemetry | WebSocket hub, push latest values to browser, Redis cache for snapshots | Data Pipeline | Browser |
| Fleet Overview | Aggregation queries, ring chart data, trend data, heatmap geo-data | Real-time Telemetry, TSDB | — |
| Alert Engine | Rule evaluation per data point, state machine, notification dispatch | Data Pipeline, Real-time Telemetry | — |
| History Service | Time-range queries with downsampling, gap detection | TSDB | — |
| Config Service | CRUD for per-robot thresholds/sampling/reconnect, audit log | PostgreSQL | — |
| Collaboration | Threaded comments, @mention parsing, activity indicators | PostgreSQL, Real-time Telemetry | — |
| Report Engine | Async PDF/Excel generation from aggregated data | TSDB, PostgreSQL | Browser download |
| Shell | Theme provider, i18n framework, drag-drop layout, route structure | All UI modules | Browser |

## Data Flow

```
Robot Edge Gateway
  │  (MQTT topic: robot/{id}/telemetry, binary/JSON/Protobuf)
  ▼
Data Pipeline ──normalize──→ Redis Streams ──batch──→ TimescaleDB
  │                           │
  │                           │ Pub/Sub
  ▼                           ▼
Alert Engine              WebSocket Hub
  │ (alert events)          │ (telemetry updates)
  ▼                           ▼
Redis Pub/Sub              Browser (React SPA)
  │
  ▼
WebSocket Hub → Browser (alert toasts, badge count)
```

## Database Separation

| Database | Purpose | Data |
|----------|---------|------|
| PostgreSQL | Operational data | Robots, users, alert rules, alert events, comments, config audit log |
| TimescaleDB | Time-series telemetry | Per-robot metrics: battery, temps, CPU, latency, GPS, task status |
| Redis | Cache + real-time | Latest telemetry snapshots (5s TTL), Pub/Sub channels, WebSocket sessions |

## Key Decision Points (unresolved, for architect)

1. BFF pattern vs direct DB queries from frontend: 8 modules suggest a BFF.
2. Data Pipeline: separate microservice or embedded in BFF?
3. TSDB: TimescaleDB (PostgreSQL extension) vs InfluxDB vs ClickHouse?
4. Frontend framework: React (ecosystem) vs Vue (simpler for dashboard)?
5. Real-time transport: WebSocket vs Server-Sent Events vs polling?

## Completion Report

**what_was_done**: Mapped the problem space — 9 modules, 3 databases, clear data flow from robot edge gateway to browser, external dependency map, 5 open decision points for architect to resolve.

**chain_entry**: "9 modules, 3 databases (PostgreSQL for ops, TimescaleDB for telemetry, Redis for real-time). Core data flow: MQTT → normalize → Redis Streams → TSDB batch write + WebSocket fan-out. 5 architecture decisions pending."
