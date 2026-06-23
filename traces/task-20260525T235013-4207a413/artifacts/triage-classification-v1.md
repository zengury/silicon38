# Triage — Fleet Ops Dashboard

**Task Type:** `feature` + `ambiguous` (compound)
**Severity:** HIGH — multi-subsystem; customer expectation conflicts with soul-knife discipline.

## Problem statement
Customer requests a 9-area Web monitoring dashboard. soul.md declares this is "a room you must refuse to build." The true act: "in the seconds a machine is failing — which one, what's wrong, how long left, what to do." User has confirmed soul-knife discipline governs.

## Scope
**In scope**
- Diagnostic triage UX (critical failures, root cause, remediation)
- Realtime telemetry ingest (DDS/protobuf bridge already exists in manastone)
- Alerting (fall, joint-lost, low-battery)
- State visualization at max signal-to-noise

**Out of scope (decoration / not on hot path)**
- Full 9-area parity as written
- 30-day historical charting as foreground
- Elaborate config panel
- Collab as primary surface (kept as minimal claim/comment, not threading)
- PDF/Excel export
- Theme switch, i18n, draggable layout as goals

## Ambiguities (named)
1. Soul vs customer "completeness" — resolved: soul wins (user confirmed).
2. Realtime latency SLA — recommend <500ms alert path, <2s telemetry refresh.
3. Data normalization layer — recommend canonical schema with raw shadow.
4. Alert rule inventory — fall / joint-lost / low-battery as MVP, schema-driven for additions.

## Recommended next nodes
- Wave 2 (Layer 1): `to-prd` (triggered by triage, prob 0.70)
- Wave 3 (Layer 2): `architect`, `api-designer`, `ux-researcher-designer`, `senior-frontend`
- Wave 4 (Layer 3): `grill-me`, `code-reviewer`
- Skip: `diagnose`, `prototype`, `improve-codebase-architecture`, `to-issues`, `epic-design`, `apple-hig-expert`, `release-manager`, `technical-writer`, `dependency-auditor`, `devops-engineer`.
