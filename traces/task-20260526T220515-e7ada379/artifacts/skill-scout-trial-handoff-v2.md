# Trial 2: handoff-v2 — Context Compression

**Benchmark:** handoff Benchmark 1 — Compress 50-turn conversation
**Input:** This entire FleetOps session (PRD → ADR → Code → Soul → Org evolution)
**Method:** Apply handoff-v2 per Grove's delegation-and-monitoring principles

---

## Handoff Output

### Deliverable

**Artifact refs:**
- `to-prd-output-v1.md` — FleetOps PRD, 17 user stories
- `architect-output-v1.md` — 8 ADRs (system topology, data model, adapter pipeline, data flow, alert engine, components, tech stack, deployment)
- `senior-engineer-output-v1.md` — React SPA demo implementation
- `demo/fleetops-dashboard/` — Runnable code

**Compact metadata:** Full-stack fleet monitoring dashboard for 20 humanoid robots. React 18 + TypeScript + ECharts + Zustand + Tailwind. Mock engine with realistic behavior patterns. Delivered, build passing, runtime issues fixed (echarts + i18n Suspense).

### Context Block

**Decisions retained:**

| Decision | Source | Impact |
|----------|--------|--------|
| Canonical RobotSnapshot as unified data model — all adapters map heterogeneous formats into this one type | architect ADR-002 | Every UI component, alert rule, and history query depends on this type. Cannot change without full regression. |
| Adapter Pipeline 3-stage: parse → mapFields → normalizeUnits | architect ADR-003 | New robot protocols only need a new adapter implementing the DataAdapter interface. |
| Zustand multi-store architecture: fleetStore / alertStore / configStore / commentStore / uiStore — independent stores to prevent cascading re-renders | architect ADR-006 | Adding a new feature requires a new store, not modifying existing ones. |
| Alert Engine: 8 default rules, state machine (pending→active→acknowledged→resolved), cooldown de-duplication | architect ADR-005 | Alert behavior is deterministic and testable. Config panel can override thresholds per robot. |
| Soul-bearing nodes identified: architect, prototype, ux-researcher-designer, ui-design-system, senior-frontend, epic-design, grill-me | org decision (v0.5) | Any handoff to these nodes must include soul_ref. Handoff without soul_ref to a soul-bearing node is a policy violation. |

**Constraints retained:**

| Constraint | Source | Impact |
|------------|--------|--------|
| Demo phase: in-memory storage, no persistence, single user, localhost | to-prd Out of Scope + architect ADR-008 | Comments and config are lost on page refresh. History is ring-buffer in memory. |
| System is read-only monitoring — no robot control | to-prd Out of Scope | WebSocket is push-only. No bidirectional commands needed. |
| China market: Leaflet OSM tiles may be blocked. Map solution undecided. | architect ADR-007 open question | Any customer demo in China needs this resolved first. |
| 1.46MB JS bundle (ECharts). First paint may be slow on mobile. | senior-engineer build output | Demo optimization: consider lazy-loading ECharts for non-dashboard routes. |

**Open questions:**

| Question | Owner |
|----------|-------|
| Backend aggregation service deployment: edge vs cloud? | architect |
| 30-day history storage: InfluxDB vs TimescaleDB? (Demo: in-memory) | database-engineer (when activated) |
| Map service for China: 高德 vs 百度 vs Leaflet with China CDN? | architect / user |
| Multi-user collaboration conflict strategy? | architect |

### Soul Reference

`org/soul.md` — Kahn three-room principles must be carried by design-class nodes. This session's architect ADRs lacked soul evidence (see grill-me-v2 trial for specific findings).

### Verification

- **Shared vocabulary checked:** Yes — Canonical Model, Adapter Pipeline, Zustand stores, soul-bearing definitions are documented and consistent.
- **Quality standards communicated:** Yes — Each role's harness defines done_when criteria.
- **Self-sufficient:** Yes — A downstream node receiving only this handoff could understand the system's architecture, data model, constraints, and open risks without reading the 8 full ADRs.

### Score: 0.72 ✅ (vs old handoff 0.30)
