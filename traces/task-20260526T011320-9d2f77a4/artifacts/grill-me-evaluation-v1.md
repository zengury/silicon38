# Grill-Me: Architecture Challenge

## Verdict: ROBUST — Minor issues to address

Architecture is well-grounded. No fatal flaws. Three concerns worth addressing before implementation.

---

## Challenges

### Challenge 1: Adapter Format Detection is a Hidden Assumption

**Assumption**: `FormatDetector` can reliably identify the data format from raw payload.

**Failure condition**: Two different robot firmware versions produce JSON with identical top-level structure but different internal field names. FormatDetector misclassifies → wrong Adapter applied → corrupted RobotTelemetry (e.g., voltage interpreted as percentage).

**Severity**: **Major**

**Recommendation**: Don't auto-detect. The robot format should be an explicit field in the WS message envelope:
```json
{ "format": "g1-v2", "robotId": "R01", "payload": { ... } }
```
If that's not possible (legacy robots), add a `format` field to the mock message protocol and note that production should use explicit format tagging.

### Challenge 2: Alert Dedup Window Doesn't Handle Flapping

**Assumption**: 5-minute dedup window prevents alert storms.

**Failure condition**: A joint communication oscillates LOST→OK→LOST every 6 minutes. Each cycle produces a new alert. Engineer gets a new CRITICAL notification every 6 minutes for the same underlying issue. This is "flapping" — a well-known ops problem.

**Severity**: **Minor** (Demo scope. Production would need flapping detection.)

**Recommendation**: Add a note in the ADR: "Production consideration: flapping detection (if alert resolves and re-fires N times within M minutes, suppress and escalate as 'intermittent fault')."

### Challenge 3: Single WebSocket Topic Architecture May Not Scale

**Assumption**: Topic multiplexing over a single WS connection is sufficient.

**Failure condition**: (Production concern) 50 robots × 1 telemetry/sec = 50 messages/sec over one WS. Each message triggers DataNormalizer → AlertEngine → Store update. At scale, this becomes a bottleneck. Topic-level subscription (`"telemetry"` receives ALL robot data) means every component re-evaluates on every message even if only one robot changed.

**Severity**: **Minor** (Demo has 6 robots. Not a problem at this scale.)

**Recommendation**: The architecture is correct for Demo. Production version should consider:
- Per-robot topics: `"telemetry/R01"`, `"telemetry/R02"` for selective subscription
- Batch updates: WS sends array of telemetry frames per tick
- Web Worker: Move DataNormalizer + AlertEngine off main thread

### Challenge 4: Mock Data Generator Has No Error Injection API

**Assumption**: `injectAnomaly()` covers all demo scenarios.

**Failure condition**: The demo needs to show the full alert lifecycle (trigger → acknowledge → resolve). But `injectAnomaly` only triggers. There's no `resolveAnomaly()` to show recovery. The demo presenter would need to wait for the simulator to naturally recover, breaking the narrative flow.

**Severity**: **Minor**

**Recommendation**: Add `resolveAnomaly(robotId, type)` that immediately sets the robot back to normal state. This enables demo scripts: inject fault → show alert → acknowledge → resolve fault → show recovery.

### Challenge 5: Config Panel "Instant Apply" Has No Rollback

**Assumption**: Optimistic config updates are safe because they're local.

**Failure condition**: Engineer accidentally drags the "battery low threshold" slider from 20% to 80%. All 6 robots immediately fire low-battery alerts. No undo. In production, this is a self-DoS.

**Severity**: **Minor** (Demo has no real consequences.)

**Recommendation**: Add a 3-second undo toast on config changes: "Threshold updated — Undo?" Production would need confirmation dialogs for threshold changes that affect active alerts.

---

## Architecture Strengths Noted

1. **Adapter pattern for data normalization is the right call.** Extensible without touching existing code. Testable in isolation.
2. **CSS Variables for theming is clean.** Zero runtime cost, no re-renders for theme changes.
3. **Client-side mock server with WebSocket interface is pragmatic.** Enables full demo without backend. The same frontend code works with real WS backend later.
4. **Plain rule objects for AlertEngine.** DSL would be over-engineering for 3 rules. Keep simple.
5. **Zustand over Redux.** Correct choice for this scale and real-time nature.

---

## Summary

| Metric | Assessment |
|--------|-----------|
| Architecture soundness | ✅ Solid |
| Missing error states | ✅ Covered |
| Scale assumptions | ⚠️ Noted (Demo-appropriate) |
| Testability | ✅ Deep modules are isolatable |
| Demo feasibility | ✅ Single-page HTML viable |

**Go build it.**

---

## Completion Report

- **what_was_done**: Stress-tested architecture against 5 specific challenges: format detection ambiguity, alert flapping, WS scaling, mock error injection, and config rollback. Found 1 major concern (format detection), 4 minor. Verdict: ROBUST.
- **key_decisions**: [(1) Format detection should use explicit tagging, not heuristics, (2) Add `resolveAnomaly()` to demo mock for narrative control, (3) Add undo toast for config changes, (4) Document production considerations for flapping and scaling]
- **handoff_focus**: senior-engineer should implement explicit format field in WS messages, add `resolveAnomaly()` to mock, and include undo toast on config changes
- **open_questions**: None
- **known_constraints**: Demo scale (6 robots) doesn't surface production scaling concerns
- **confidence_differential**: 0.90
