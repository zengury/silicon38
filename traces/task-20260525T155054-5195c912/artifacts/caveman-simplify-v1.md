# First Principles: 机器人车队运维监控面板

## What The System Actually Is

```
Robots → [receive numbers] → [unify numbers] → [store numbers] → [show numbers + alert on numbers]
```

That's it. 12 requirements collapse to 4 operations on a stream of numbers. Everything else is UX wrapping.

## Core Invariants

### Invariant 1: Every robot is a stream of numbers.
Battery = number. Joint temp = number. GPS = two numbers. Task = string (which is a category number to a computer). The heterogeneity problem is: robots send these numbers in different wrappers (JSON, Protobuf). Solution: unwrap → normalize to one schema → everything downstream only sees the normalized form.

### Invariant 2: The operator's job is: "Which robot needs me NOW?"
Alerts, overview dashboard, status cards — these all serve one question. If the dashboard can't answer it in under 5 seconds, it fails. The ring chart, the alert toast, the status dot — they all work for this question or they don't earn their place.

### Invariant 3: An alert that fires twice for the same incident is worse than no alert.
Alert state machine: `dormant → triggered → acknowledged → dismissed`. Cooldown per rule. Dedup. This is the entire alert architecture. The thresholds and conditions are configuration. The state machine IS the feature.

### Invariant 4: Config without audit is dangerous.
You can change thresholds today, forget tomorrow, and spend hours debugging why alerts aren't firing. Every config change must log: WHO, WHAT field, OLD value, NEW value, WHEN.

## What To Build First

```
Week 1: Ingest one robot's numbers → normalize → show on screen.
Week 2: Show all robots → add status dots → add basic alerts.
Week 3: History curves → config panel → alert refinement.
Week 4: Collaboration → reports → themes → i18n → layout.
```

If Week 1 doesn't work, nothing else matters. The core loop (ingest → normalize → show) must work before any dashboard widget.

## What This System Is NOT

- NOT a robot controller (no actuation commands)
- NOT a predictive analytics platform (no ML)
- NOT a fleet mission planner (no path planning)
- NOT a data warehouse (90-day retention, not years)

## Simplest Possible Version

```
One web page. One table. Rows = robots. Columns = battery, joint temp, CPU, latency, task, GPS, status.
Data arrives via HTTP POST from edge gateway. Refreshes every 5 seconds. No WebSocket.
Alerts: browser Notification API. No sound. No toast.
Config: edit threshold values inline in the table.

THEN add: WebSocket real-time, ring chart, alert toasts, history curves, collaboration, themes.
```

This is the benchmark. Every feature added to the final system must justify why the simplest version isn't enough.

## Completion Report

**what_was_done**: Reduced 12 requirements to 4 invariants and a 4-week build order. Identified the simplest possible version as a benchmark — every added feature must earn its place against it.

**chain_entry**: "Core loop: ingest→normalize→show must work in Week 1. Alert state machine IS the architecture. Config requires audit trail. Build simplest version first as benchmark."
