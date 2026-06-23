# Zoom-Out Output v2 — Refactoring Focus

## Target: Engine Layer (6,500 lines across 3 engines + shared)

```
agent/workflow/engine/
├── executor/         1,387 lines  — DAG runner, kernel graph, checkpoint
├── pe_engine/        2,322 lines  — Planner, step runtime, state adapter
├── sbs_loop/         1,183 lines  — Step-by-step planner, act subgraph
├── runtime/            585 lines  — SSE projection, session, hooks
├── workflow_graph/   1,041 lines  — DSL graph, subgraph, ability enricher
└── adapters/            80 lines  — Mainflow context adapter
```

### Shared Concepts (the overlap)

| Concept | executor | pe_engine | sbs_loop | runtime |
|---------|----------|-----------|----------|---------|
| Plan/Step DAG | ✓ dag_runner | ✓ dag.py | ✓ dag_runner | — |
| LLM Planning | — | ✓ planner | ✓ planner | — |
| Step Execution | ✓ kernel_graph | ✓ step_runtime | ✓ sbs_act_subgraph | — |
| Human Gate | ✓ hitl.py | ✓ human_nl_gate | — (in graph) | — |
| Checkpoint/Resume | ✓ checkpoint* | — (via executor) | — (via executor) | — |
| SSE Streaming | — | — | — | ✓ session |
| State Projection | — | — | — | ✓ projector |
| Error Handling | ✓ error_mapping | — (in step_runtime) | — (in graph) | — |

### The Deletion Test

Delete one engine. Does complexity vanish or reappear in callers?

- **Delete DAG executor**: PE and SBS both use it as underlying runner → complexity reappears in both. *Verdict: DAG executor is the servant to PE and SBS.*
- **Delete PE engine**: Only `entry_gate.py` calls it for `plan_execute` mode. Complexity doesn't reappear elsewhere. *Verdict: PE is shallow — its planning logic duplicates SBS planning.*
- **Delete SBS loop**: Only `entry_gate.py` calls it for `step_by_step` mode. Complexity doesn't reappear. *Verdict: SBS loop is shallow — its only difference from PE is human gates between every step.*

### Served/Servant Bleed

```
agent/session/core/entry_gate.py  (served space)
  ├── directly constructs workflow_instance dicts
  ├── directly sets downstream_instruction with OP_NEW/CONTINUE
  ├── directly calls execute_workflow_layer_operation
  └── uses raw strings for all context keys

agent/workflow/domain/lifecycle/  (servant space)
  └── operation_contract.py has OP_NEW, OP_CONTINUE, OP_SWITCH
      → but entry_gate imports these directly, not through a contract
```

### Data Flow Blindness

`ConversationRuntime` has `extra="allow"` — 6+ fields injected as raw dict keys:
- `workflow_instance`, `current_process`, `agent_skill`, `downstream_instruction`
- `use_process_flow`, `execute_from_memory_applied`
- None visible in the type system. IDE can't autocomplete. Type checker can't catch misuse.

---

## Completion Report
```yaml
completion_report:
  what_was_done: "精确测量三引擎重叠度：DAG executor 是底层 servant，PE/SBS 是浅层包装，重复 LLM planning 逻辑"
  key_decisions:
    - decision: "PE engine 和 SBS loop 的差异仅是人工门控频率，核心 planning+execution 逻辑一致"
      rationale: "两个 planner 都是 _build_planning_input → _invoke_planning_llm，仅 prompt 不同"
  handoff_focus:
    - "improve-codebase-architecture: 三引擎收敛为单一 Engine facade 的优先级最高"
    - "entry_gate 的 raw string dict writes 需要替换为 WorkflowContextKeys 契约常量"
    - "ConversationRuntime 的 extra='allow' 需要收窄为显式字段"
  open_questions: []
  known_constraints:
    - "LangGraph checkpoint 绑定 executor 层，合并不只是代码合并"
    - "已有测试 (test_peor_*, test_sbs_*) 依赖 PE/SBS 语义，需保持通过"
```
