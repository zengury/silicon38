# Fleet Ops Dashboard — Architecture

## 1. Architecture Posture

The dashboard is a triage instrument, not a reporting portal. Every architectural choice is evaluated by a single question: does it serve the operator in the seconds a machine is failing? Two subsystems exist to serve that operator directly — the **Triage Canvas** (alert cards, modal interrupts, claim strip) and the **Alert hot path** (detection → fanout → render). All other subsystems — History, Config, Reports — are **servants**: they must never impose latency, failure modes, or cognitive load on the foreground. A History store read failure is background noise; a stalled alert modal is a machine down with no owner. *Served, and servant. Never let them bleed.*

---

## 2. Component Diagram

```
Per-robot edge (Orin NX 192.168.123.164)
┌────────────────────────────────────┐
│  manastone-diagnostic              │
│  ├─ DDS bridge (lowstate, sport,   │
│  │    estimator)                   │
│  ├─ MCP Server :8080 (SSE)         │
│  └─ Redis :6379 (local cache)      │
└───────────────┬────────────────────┘
                │ SSE / REST poll (per robot)
                ▼
┌────────────────────────────────────────────────────────────┐
│            Fleet Aggregator + Backend API (single service) │
│  ├─ Robot registry (which Orins are live)                  │
│  ├─ Telemetry Normalization (canonical + raw shadow)       │  ◄── SLOW PATH
│  ├─ Alert Engine (threshold eval, dedup, state machine)    │  ◄══ HOT PATH
│  ├─ History writer (async, fire-and-forget to Redis ZADD)  │  ◄── SLOW PATH
│  ├─ Config reader (versioned Redis keys)                   │  ◄── SLOW PATH
│  └─ REST API (/alerts, /history, /config, /collab)        │  ◄── SLOW PATH
└────────────┬───────────────────────────────────────────────┘
             │ WebSocket (hot path ══)  │ HTTP REST (slow paths --)
             ▼                          ▼
┌──────────────────────────────────────────────────────────┐
│                      Web Client                          │
│  Triage Canvas   ← WS: ALERT_FIRED, VITALS_UPDATE,      │
│                         ALERT_ACKED, COLLAB_UPDATED      │
│  History Drawer  ← REST GET /history                     │
│  Config Drawer   ← REST GET/POST /config                 │
│  Fleet Health    ← REST GET /fleet/summary               │
└──────────────────────────────────────────────────────────┘

══ HOT PATH ══  DDS breach → Alert Engine → WS fanout → client modal
── SLOW PATH ── history write, config read, collab sync, fleet health
```

---

## 3. Hot Path Budget (FR-001: 500ms edge-to-modal)

| Hop | Budget | Notes |
|-----|--------|-------|
| Edge DDS subscriber detects breach | 50ms | Synchronous in manastone-diagnostic; local pre-filter reduces upstream noise |
| SSE delivery to Fleet Aggregator | 80ms | Push-on-change from Orin; not poll-tick dependent |
| Normalization (in-process) | 20ms | CPU-bound field mapping, no network hop |
| Alert engine eval + Redis dedup check | 30ms | Deterministic compare + pipelined Redis HSETNX |
| WebSocket fanout (≤10 sessions) | 50ms | Single broadcast at fleet scale |
| Client render (modal mount) | 50ms | No async data fetches block render; all payload in WS message |
| **Total used** | **280ms** | |
| **Slack** | **220ms** | Buffer for Redis latency spikes, GC pauses, network jitter |

Where to cut if pressured: throttle poll on idle robots (no active alert) from 80ms to 200ms floor. Not done today — 220ms slack is healthy and adding idle/active state tracking costs more complexity than it saves.

---

## 4. Tech Choices

| Concern | Choice | Rationale |
|---------|--------|-----------|
| **Normalization location** (OQ-1) | Backend, in-process in Fleet Aggregator | Client stays dumb; conversion is deterministic and <20ms in-process; no browser duplication |
| **Canonical schema format** | JSON envelope: `{robot_id, ts_ms, metrics:{}, raw_shadow:{}, alert?:{}}` | Already the wire format from manastone-diagnostic; no extra serialization layer |
| **Realtime transport** | WebSocket (RFC 6455), one connection per browser session | Bidirectional needed for claim writes; SSE is one-way; WS fanout is trivial at ≤10 sessions |
| **Alert engine rule language** | Python conditionals + versioned config dicts from Redis | Deterministic spec needs no DSL; adding a rule is adding a branch and a config key |
| **History store** | Redis sorted sets, 30-day TTL, 1-minute resolution downsampled | Redis already required; no new operational dependency; migrate to TimescaleDB when forensic fidelity is demanded |
| **Config store (versioned)** | Redis monotonic version keys `config:{robot_id}:v{n}` | Sub-millisecond reads on hot path; alert engine always reads latest key at eval time |
| **Collab store** | Redis hash per incident; `HSETNX` for atomic first-write-wins claim | FR-004 concurrency in one command; no separate DB for a two-field struct |
| **Reconnect strategy** (OQ-2) | On WS open, client calls `GET /api/alerts/active`; then subscribes to stream | Alert state is idempotent live state, not a log; no replay buffer complexity |
| **Raw-shadow wire** (OQ-3) | Inline sibling field in every `VITALS_UPDATE` message | At fleet scale (<12 robots, ~10 metrics), overhead is <2KB per message; no hover round-trip |

---

## 5. Cuts (30% complexity reduction)

**Cut 1: Co-locate Fleet Aggregator and REST API as a single service.**
- Lose: independent scaling of aggregator vs. API.
- Gain: no inter-process network hop; one deployment unit; no service mesh config. Fleet is 4–12 robots — independent scaling is premature.

**Cut 2: Drop Notification Dispatcher entirely (no Slack/SMS/email/push).**
- Lose: external alert channels.
- Gain: no external credentials, no webhook failure modes near the alert path, no per-channel formatting logic. The PRD does not require external notifications. The modal is the notification. Add in v2 when ops confirms the need.

**Cut 3: Redis sorted sets for history instead of TimescaleDB.**
- Lose: SQL query power and full-resolution 30-day forensic waveforms.
- Gain: no new operational dependency; Redis already required; implementation is one `ZADD` per metric write. History drawer shows downsampled sparklines. Migrate when forensic fidelity is a stated requirement.

---

## 6. Constraints on Downstream Nodes

### For senior-frontend

1. WebSocket is the sole source of truth for Triage Canvas state. Never derive alert presence from REST.
2. Modal render must not block on any async fetch. All modal data (robot ID, alert type, vitals, claimer) must be present in the WS `ALERT_FIRED` message.
3. Reconnect sequence is mandatory: on WS open, fire `GET /api/alerts/active` before subscribing to the stream. This is not optional UX — missed alerts during disconnect must be shown first.
4. `raw_shadow` fields are display-only hover annotations. Never use them in client logic or state transitions.
5. Claim write is REST `POST /api/collab/{incident_id}/claim`, not a WS message. Client is receive-only on WS; server broadcasts updated collab state after a successful claim.

### For api-designer

1. `GET /api/alerts/active` must return the full payload to render the modal without a follow-up call (robot ID, alert type, vitals, claimer, dedup state).
2. Config writes must include a client-supplied `base_version`; server rejects writes where it does not match current latest. Client retries with refreshed version.
3. WS message types must be enumerated and versioned: at minimum `VITALS_UPDATE`, `ALERT_FIRED`, `ALERT_ACKED`, `COLLAB_UPDATED`. No catch-all event type.
4. `raw_shadow` fields are required (not optional) in every `VITALS_UPDATE` message.
5. History endpoint must accept `?from=<ts_ms>&to=<ts_ms>&resolution=<s>` query params. Frontend drives zoom; API must not assume a fixed window.

---

```yaml
completion_report:
  what_was_done: >
    Produced architecture for Fleet Ops Dashboard. Resolved all three PRD open questions.
    Defined hot path budget (280ms used, 220ms slack). Specified 9 concrete tech choices.
    Named 3 complexity cuts aligned with soul. Issued hard constraints for senior-frontend
    and api-designer.
  key_decisions:
    - decision: Normalization in Fleet Aggregator backend, not client-side
      rationale: Keeps client dumb; deterministic and sub-20ms in-process; avoids browser duplication
    - decision: Raw shadow inline in canonical payload
      rationale: No bandwidth constraint at fleet scale; eliminates hover round-trip latency
    - decision: Reconnect via REST query of active alerts, not event replay
      rationale: Alert state is idempotent live state; replay window adds complexity with no safety gain
    - decision: Redis HSETNX for claim concurrency
      rationale: Atomic first-write-wins in one command; no separate DB for a two-field struct
    - decision: Co-locate Fleet Aggregator with REST API (Cut 1)
      rationale: Fleet scale does not justify independent scaling; removes inter-process hop
  handoff_focus:
    - senior-frontend must implement mandatory reconnect sequence before stream subscribe
    - api-designer must enumerate WS message types and include raw_shadow in every VITALS_UPDATE
    - api-designer must define GET /api/alerts/active returning full modal payload without follow-up call
  open_questions:
    - If fleet grows beyond 12 robots, co-location assumption must be revisited
    - Notification Dispatcher deferred to v2 — ops team should confirm external channel requirements early
    - Redis sorted set history (Cut 3) must be validated against actual forensic fidelity requirements before v1 ships
  known_constraints:
    - DDS domain ID is 0 — must not change
    - manastone-diagnostic is read-only diagnostic; no control tools exposed
    - MCP server on Orin is SSE transport only — aggregator must adapt to SSE pull, not expect WS from edge
  iteration_context: null
```
