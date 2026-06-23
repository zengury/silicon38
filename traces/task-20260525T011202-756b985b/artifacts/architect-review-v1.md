# Architect Review — Engine Facade + Data Flow Refactoring

## Verdict: APPROVED (advisory)

## ADR Review

### ADR-001: Engine facade (`agent/engine.py`) — APPROVED
- **Design**: Single `Engine` class with `async run() → AsyncIterator[EngineEvent]`. Three modes (DAG, PLAN_EXECUTE, STEP_BY_STEP) handled internally.
- **Esherick compliance**: ✓ One deep interface. 8 event types cover all three modes. Internal dispatch to legacy engines is hidden.
- **Risk**: Low. New file, no existing callers changed. Legacy engines untouched.
- **Concern**: `_plan` method has a fallback to PE planner via try/except. Need explicit documentation that this is temporary — when Step 4 (shared planner) completes, this becomes the single path.
- **Suggestion**: Add `Engine.resume()` for human gate continuation. Currently HumanGateEvent is yielded but no resume path defined.

### ADR-002: ConversationRuntime explicit fields — APPROVED
- **Design**: Added 6 previously hidden fields as Optional with defaults. `extra="allow"` retained for backward compat.
- **Kimbell compliance**: ✓ Data flow now visible. IDE autocompletes. Type checker sees fields.
- **Risk**: Very low. Additive change — new fields with defaults, old dict access still works.
- **Suggestion**: Mark `extra="allow"` with `# Phase 3: tighten to extra="forbid"` comment.

### ADR-003: WorkflowContextKeys in entry_gate — APPROVED
- **Design**: Replaced raw string dict keys with WFK constants.
- **Esherick compliance**: ✓ Served/servant now talk through named contract.
- **Risk**: Zero. Constants resolve to same strings. No behavior change.
- **Note**: `intent_type`, `active_phase`, `workflow_mode`, `current_process` don't have WFK constants — future work to add them.

## Rejected Alternatives
- ❌ Combine all three engines now → Too risky. Need separate cycle.
- ❌ Remove extra="allow" immediately → Breaks backward compat. Phase 3.

---

## Completion Report
```yaml
completion_report:
  what_was_done: "审查 Engine facade、ConversationRuntime 显式字段、entry_gate WFK 常量三项重构"
  key_decisions:
    - decision: "全部 APPROVED — 架构方向正确，风险可控"
      rationale: "三项均为低风险增量改进。Engine facade 是 Esherick 厚墙，数据显式化是 Kimbell 光，WFK 常量是 served/servant 契约"
  handoff_focus:
    - "senior-engineer: Engine.resume() 需要实现以支持人工门控恢复"
    - "tdd: 为 Engine facade 编写集成测试"
    - "code-reviewer: 审查 entry_gate.py 的 WFK 常量替换是否完整"
  open_questions:
    - "Engine._plan 的 try/except 回退何时替换为共享 planner"
  known_constraints:
    - "extra='allow' 暂时保留 — Phase 3 收紧"
```
