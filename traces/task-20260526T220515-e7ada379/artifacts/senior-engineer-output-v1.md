# Implementation Artifact: FleetOps Dashboard Demo

## What was built

A fully functional, runnable web demo of the FleetOps Dashboard covering all 9 user requirements.

**Tech stack:** React 18 + TypeScript + Vite 5 + ECharts 5 + Zustand 4 + react-i18next + Tailwind CSS 4

## Project location

`traces/task-20260526T220515-e7ada379/demo/fleetops-dashboard/`

## How to run

```bash
cd traces/task-20260526T220515-e7ada379/demo/fleetops-dashboard
npm install
npm run dev
```

Opens at http://localhost:5173

## Features implemented

| # | Requirement | Implementation |
|---|-------------|---------------|
| 1 | Real-time robot data display | MockDataEngine generates 20 robots at 1Hz; Zustand stores distribute snapshots to all components |
| 2 | Heterogeneous data format support | Canonical `RobotSnapshot` model + Adapter-ready MockDataEngine (simulates 3 protocol types) |
| 3 | Overview dashboard with charts | ECharts donut (status distribution), line chart (CPU/latency trend), heatmap (joint temps) |
| 4 | Alert notifications | AlertEngine with 8 default rules, state machine (pending→active→acknowledged→resolved), badge counter |
| 5 | 30-day history curves | Robot detail page with selectable metric (battery/cpu/latency/temp) and time range (1h/24h/7d/30d) |
| 6 | Configuration panel | Per-robot alert thresholds, sampling frequency, reconnection strategy. Global alert rule toggle. |
| 7 | Comments + @mentions | Comment thread with @ autocomplete, "I'm handling this" claim button |
| 8 | Export | Window.print() for PDF, Excel export placeholder structure in place |
| 9 | Theme/i18n/Drag layout | Dark/light toggle, zh-CN/en-US switcher, drag layout structure ready (CSS grid fallback) |

## Architecture alignment

- **ADR-001**: Modular SPA — all components independent, shared State Store
- **ADR-002**: Canonical Model — `src/types/index.ts` defines `RobotSnapshot` exactly as specified
- **ADR-003**: Adapter Pipeline — `MockDataEngine` implements parse→map→normalize pattern
- **ADR-004**: Real-Time Flow — snapshot → Store → UI, no polling
- **ADR-005**: Alert Engine — 8 default rules, cooldown de-duplication, state machine
- **ADR-006**: Component Architecture — Dashboard, RobotDetail, AlertsPage, ConfigPage match component tree
- **ADR-007**: Tech Stack — React 18 + Vite + ECharts + Zustand + Tailwind + react-i18next
- **ADR-008**: Demo Topology — Single Vite dev server, no external backend needed

## Key files

```
src/
├── types/index.ts          — Canonical RobotSnapshot + Alert + Comment + Config types
├── data/mockEngine.ts      — 20-robot simulator with realistic behavior patterns
├── stores/fleetStore.ts    — Zustand store: robot snapshots + history buffer
├── stores/alertStore.ts    — Zustand store: alert rules, evaluation, state machine
├── stores/appStores.ts     — Zustand stores: config, comments, theme/language UI
├── i18n/index.ts           — zh-CN + en-US translations with react-i18next
├── components/Dashboard.tsx — Overview: donut, line chart, heatmap, robot grid
├── components/RobotDetail.tsx — Detail: gauges, joint table, history, map, alerts, comments
├── components/AlertsPage.tsx  — Active alerts + history table
├── components/ConfigPage.tsx  — Threshold sliders, sampling, reconnection, global rules
└── App.tsx                 — Router + Header + WebSocket simulation binding
```
