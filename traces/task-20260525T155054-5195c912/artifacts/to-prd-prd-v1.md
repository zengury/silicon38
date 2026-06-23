# PRD: 机器人车队运维监控面板 (Robot Fleet Ops Dashboard)

> Source: Triage (12 reqs, P0-P2) + Caveman (4 invariants) + UX Spec (3 personas)

---

## Product Vision

A web dashboard that lets fleet operators answer "which robot needs me right now?" in ≤ 5 seconds, and do everything else without leaving the tool.

## User Stories

### P0 — Real-time Monitoring (Must have in Week 1)

**US-01**: As an operator, I see all robots as cards showing battery %, joint temps, CPU %, network latency, current task, and GPS location, so I know each robot's status at a glance.

**US-02**: As an operator, I see each robot's connection state (online/delayed/offline) as a colored status dot, so I know if missing data means the robot is down or just delayed.

**US-03**: As an operator, when there are 10+ robots, clustered map markers prevent visual overload; zooming in dissolves clusters.

**US-04**: As an operator, data refreshes in ≤ 2 seconds so I see changes near-real-time.

### P0 — Data Normalization

**US-05**: As an operator, I don't care what format the robot sends — the dashboard shows all robots' data in a unified format with consistent field names and units.

**US-06**: As an admin, when a new robot model joins, I add its data mapping via a YAML config file (not code change), and its data appears normalized immediately.

### P0 — Fleet Overview

**US-07**: As an operator, I see a ring chart (online/offline/error ratio), a battery trend line chart, and a CPU trend line chart on the main dashboard, so I can assess fleet health in ≤ 10 seconds.

**US-08**: As an operator, clicking the "error" sector of the ring chart jumps me to the list of error-state robots.

**US-09**: As an operator, I can select time windows (1h/6h/24h/7d) for trend charts, and they refresh automatically.

### P0 — Alerts

**US-10**: As an operator, when a robot falls, I get an immediate popup + sound alert with robot ID, time, and GPS coordinates.

**US-11**: As an operator, alerts have three actions: Acknowledge (I see it), Snooze (mute this rule for 5 min), Dismiss (problem fixed).

**US-12**: As an operator, the same alert doesn't fire again within 30 seconds of the first trigger (dedup + cooldown).

### P1 — History

**US-13**: As an operator, I can view any robot's battery, temperature, CPU, and latency as time-series charts for any window in the last 30 days.

**US-14**: As an operator, I can zoom/pan on charts, compare two robots' metrics side-by-side, and gaps in data are shown as breaks rather than connected lines.

### P1 — Configuration

**US-15**: As an operator, I can set per-robot alert thresholds (battery < X%, temp > Y°C, latency > Zms) via sliders and number inputs.

**US-16**: As an operator, I can adjust per-robot sampling frequency (1s/5s/10s/30s), and the dashboard reduces frequency automatically when battery is low.

**US-17**: As an operator, every config change is logged with WHO changed WHAT from OLD to NEW and WHEN, and I can view this history.

### P2 — Collaboration

**US-18**: As an operator, I can comment on a robot's page, reply to comments (threaded), and @mention a colleague who gets notified.

**US-19**: As an operator, when I click "I'm handling this" on a robot, other operators see a badge showing I'm working on it.

### P2 — Reports

**US-20**: As a manager, I click "Generate Report" → select time range → get a PDF with summary stats, trend charts, and alert log. No manual screenshotting.

**US-21**: As a manager, I can export fleet data as Excel with separate sheets for summary and raw data.

### P2 — Shell

**US-22**: As an operator, I toggle between dark and light themes, and my preference is remembered. Dark mode reduces eye strain during long monitoring shifts.

**US-23**: As an operator, I switch the dashboard language between Chinese and English, and all UI text and data labels update.

**US-24**: As an operator, I rearrange dashboard widgets by dragging them, and my layout is saved per user.

## Module Summary

| Module | Stories | Depth |
|--------|---------|-------|
| Data Pipeline | US-05, US-06 | Deep — complex internal (protocol adapters, mapping engine) |
| Real-time Telemetry | US-01–US-04 | Shallow — WebSocket + cache |
| Fleet Overview | US-07–US-09 | Shallow — aggregation queries |
| Alert Engine | US-10–US-12 | Deep — state machine + dedup |
| History Service | US-13–US-14 | Shallow — TSDB query proxy |
| Config Service | US-15–US-17 | Moderate — CRUD + audit |
| Collaboration | US-18–US-19 | Shallow |
| Report Engine | US-20–US-21 | Moderate — async PDF/Excel |
| Shell | US-22–US-24 | Thin shell |

## Non-Functional Requirements

- **Latency**: Real-time data ≤ 2s from robot report to screen
- **Scale**: 200 robots, each reporting every 5s = 40 msg/s. Design for 1000 robots (200 msg/s).
- **Availability**: Dashboard available during partial robot outages. No single point of failure blocks monitoring.
- **Data retention**: 30 days full resolution, 90 days aggregated (hourly)
- **Browser**: Chrome, Firefox, Edge latest 2 versions. Responsive ≥ 768px, functional on mobile (alert triage).

## Completion Report

**what_was_done**: Produced formal PRD with 24 user stories across P0-P2 priorities, 9 modules, 5 non-functional requirements. Stories map to all 12 original requirements.

**chain_entry**: "24 user stories (P0: 12 real-time+normalize+overview+alert. P1: 5 history+config. P2: 7 collab+report+shell). 9 modules, 3 depths (Deep: pipeline+alert. Shallow: telemetry+overview+history+collab. Moderate: config+report)."
