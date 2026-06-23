# Architecture Improvement Roadmap — WisglowAgent

## Current Problems

### P1: Three shallow engines around one deep DAG executor
- **Affected modules**: `agent/workflow/engine/executor/`, `pe_engine/`, `sbs_loop/`
- **Consequence**: 2,322 + 1,183 = 3,505 lines of shallow wrappers. PE planner and SBS planner share identical `_build_planning_input` / `_invoke_planning_llm` patterns. Adding a feature (e.g. retry) requires changes in 3 places.
- **Deletion test**: Delete PE engine → complexity reappears in entry_gate (need to call DAG executor directly with an LLM-planned DAG). Delete SBS loop → same. Both are thin planners over the same executor.

### P2: Hidden data flow via extra="allow"
- **Affected modules**: `agent/session/runtime.py` (ConversationRuntime), `agent/session/core/entry_gate.py`
- **Consequence**: 6+ fields injected as raw dict keys with no type checking. `workflow_instance`, `current_process`, `agent_skill`, `downstream_instruction` — invisible to IDE, type checker, and new engineers reading the code.
- **Deletion test**: Make all fields explicit → complexity concentrates in the model definition. Call sites get autocomplete and type errors for misuse.

### P3: Raw string dict keys between served and servant
- **Affected modules**: `agent/session/core/entry_gate.py` ↔ `agent/contracts/workflow/context_contract.py`
- **Consequence**: `WorkflowContextKeys` exists (412 lines of key constants!) but entry_gate uses raw strings like `"workflow_instance"`, `"downstream_instruction"`. The contract exists but isn't enforced.
- **Deletion test**: Replace raw strings with WFK constants → no complexity change, just safety.

### P4: No Engine abstraction — callers reach into executor internals
- **Affected modules**: `agent/session/core/entry_gate.py`, `agent/session/modules/workflow.py`, `agent/session/modules/workflow_turn.py`
- **Consequence**: Session layer imports from 5+ workflow submodules directly. Changing engine internals requires changing session code.
- **Deletion test**: Create `agent/engine.py` as single facade → session modules import from ONE place. Engine internals change freely behind the wall.

---

## Improvement Roadmap (ordered by impact-to-risk)

### Step 1: Create Engine facade (`agent/engine.py`) — RISK: LOW
- **Change**: Single `Engine` class with `async run() → AsyncIterator[EngineEvent]`. Internally delegates to existing DAG/PE/SBS.
- **Rationale**: Esherick principle — one deep interface hiding three implementations. Callers import one module.
- **Unlocks**: Steps 2-4 can change engine internals without touching session code.
- **Files**: NEW `agent/engine.py` (~200 lines), UPDATE `entry_gate.py` (use Engine, ~10 lines changed)

### Step 2: Explicit ConversationRuntime fields — RISK: LOW
- **Change**: Add `workflow_instance`, `current_process`, `agent_skill`, `use_process_flow`, `execute_from_memory_applied`, `downstream_instruction` as Optional fields with defaults.
- **Rationale**: Kimbell principle — data must be visible. `extra="allow"` stays for backward compat but main fields are explicit.
- **Unlocks**: Type checker catches misuse. IDE autocompletes.
- **Files**: UPDATE `agent/session/runtime.py` (~30 lines added)

### Step 3: Replace raw strings with WorkflowContextKeys — RISK: VERY LOW
- **Change**: entry_gate uses `WFK.Workflow.WORKFLOW_INSTANCE` instead of `"workflow_instance"`.
- **Rationale**: Esherick principle — served/servant talk through a named contract.
- **Unlocks**: Renaming a key becomes a single-constant change.
- **Files**: UPDATE `agent/session/core/entry_gate.py` (~20 lines changed)

### Step 4: Extract shared planner from PE + SBS — RISK: MEDIUM
- **Change**: Create `agent/workflow/engine/planner.py` with unified `plan_workflow_steps()`. PE and SBS call it instead of their own `_build_planning_input` / `_invoke_planning_llm`.
- **Rationale**: Salk principle — subtraction. Two planners → one.
- **Unlocks**: Single place to improve planning logic (better prompts, retry, streaming plans).
- **Files**: NEW `agent/workflow/engine/planner.py`, UPDATE `pe_engine/planner.py`, `sbs_loop/planner.py` (delegate to shared)

### Step 5: Collapse PE + SBS into Engine modes — RISK: HIGH (future cycle)
- **Change**: Engine.run(mode=PLAN_EXECUTE | STEP_BY_STEP) handles the difference internally. PE and SBS become implementation details, not top-level modules.
- **Rationale**: Full convergence. The deletion test says: delete PE engine → nothing breaks because Engine handles it.
- **Risk**: Requires migrating all callers and test expectations. Do in a dedicated cycle with full test coverage.

---

## Priority Justification

Why Steps 1-3 before Steps 4-5:
1. Steps 1-3 are **independent** — each can ship without the others
2. Steps 1-3 are **low risk** — additive changes (new facade, new fields, constant replacements)
3. Steps 1-3 **unlock** Steps 4-5 by creating the abstraction that makes convergence safe
4. Step 4 is medium risk (touches LLM planning paths) but high reward (single planner)
5. Step 5 is the final convergence — needs its own cycle with full regression suite

---

## Completion Report
```yaml
completion_report:
  what_was_done: "识别 4 个具体架构问题，产出 5 步优先级改进路线图，每步独立可部署"
  key_decisions:
    - decision: "Engine facade (Step 1) 优先级最高"
      rationale: "Esherick 原则：一面厚墙。创建 facade 后，Step 2-4 都在墙内完成，不影响调用方"
    - decision: "引擎完全合并 (Step 5) 推迟到未来 cycle"
      rationale: "高风险，需要专门测试周期。Step 1-4 完成后 Step 5 变成纯粹的内部重构"
    - decision: "Step 3 (WFK 常量替换) 虽然收益最小但风险为 0"
      rationale: "纯文本替换，不影响任何行为。放 Step 3 做热身，为 Step 4 建立信心"
  handoff_focus:
    - "refactor-specialist: 执行 Step 1 (Engine facade) — 新建 agent/engine.py"
    - "architect: 审查 Engine facade 的事件类型设计，确保覆盖三种模式"
    - "senior-engineer: Step 2 (ConversationRuntime 显式字段) + Step 3 (WFK 常量替换)"
  open_questions:
    - "Engine facade 是否需要支持 checkpoint resume（当前仅 DAG executor 有 checkpoint）"
  known_constraints:
    - "不能引入新依赖"
    - "所有现有测试必须通过"
```
