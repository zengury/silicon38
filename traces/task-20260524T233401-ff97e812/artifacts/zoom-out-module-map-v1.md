# Zoom-Out Output — task-20260524T233401-ff97e812

## Module Map: WisglowAgent (wisglow-agent v1.0.0)

### Top-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      web/ (FastAPI)                         │
│  main.py → api/v1/{30+ routers} → middleware, scheduler     │
│  ag_ui/  (AG-UI protocol)                                   │
└───────────────────────┬─────────────────────────────────────┘
                        │ calls
┌───────────────────────▼─────────────────────────────────────┐
│                   agent/ (Orchestration)                     │
│  orchestrator.py  ──►  session/  ──►  workflow/             │
│  execute_loop/   mcp/   skill/   llm/   memory/  ontology/  │
└────────┬──────────────┬─────────────────────────────────────┘
         │              │
    ┌────▼───┐     ┌───▼──────────┐
    │storage/│     │   utils/     │
    │ DAL    │     │ config/cache │
    └────────┘     └──────────────┘
```

### Layer Responsibilities

| Layer | Module | Responsibility | Line Count (est.) |
|-------|--------|---------------|-------------------|
| **API** | `web/` | FastAPI HTTP/SSE入口，鉴权，30+ API 模块，AG-UI 协议 | ~8,000 |
| **Orch** | `agent/orchestrator.py` | 应用级编排入口，参数校验，委托 session | ~200 |
| **Session** | `agent/session/` | 单次请求生命周期：entry_gate 阶段分发，conversation/workflow/react/exploration 模块 | ~3,000 |
| **Workflow** | `agent/workflow/` | **核心**：六层架构 (service→scheduler→domain→engine→infra→contracts) | ~30,000 |
| **Execute Loop** | `agent/execute_loop/` | ReAct 引擎、工具注册表、tool-call 算子、rails 护栏 | ~5,000 |
| **Sub Agents** | `agent/sub_agents/` | 子代理系统：委托、prompt 变量、工作讨论 | ~2,000 |
| **LLM** | `agent/llm/` | 多模型路由、场景配置、prompt 管理、结构化输出 | ~8,000 |
| **MCP** | `agent/mcp/` | MCP 客户端池、配置服务、用户固定参数 | ~3,000 |
| **Skill** | `agent/skill/` | 技能加载、工作区技能、资源加载、可执行资源 | ~2,000 |
| **Memory** | `agent/memory/` | 跨会话向量索引、记忆网关 | ~1,000 |
| **Ontology** | `agent/ontology/` | 本体推理、关系类型 | ~1,000 |
| **Persistence** | `storage/` | DALFactory + PostgreSQL DAL | ~3,000 |
| **Cross-cut** | `utils/` | 配置管理、CacheManager、阻塞执行器、日志 | ~2,000 |
| **Payments** | `payments/` | 支付宝支付集成 | ~500 |
| **Frontend** | `frontend/react/` | React 工作台：对话、工作流、技能实验室、知识库、管理 | ~51,000 |
| **Platform** | `frontend/platform/` | 平台管理端 | ~3,000 |

### Call Graph (simplified)

```
HTTP Request
  → web/api/v1/conversations.py (or agents.py, etc.)
    → agent/orchestrator.py :: AgentOrchestrator.process_query()
      → agent/session/modules/workflow_turn.py :: run_conversation_turn()
        → agent/session/core/entry_gate.py :: run_entry()
          ├─ [lifecycle] → agent/workflow/service/
          ├─ [react_direct] → agent/execute_loop/engine.py :: ReActEngine
          ├─ [plan_execute] → agent/workflow/service/workflow_execution_entry.py
          ├─ [explore] → agent/session/modules/exploration.py
          ├─ [conversation] → agent/session/modules/conversation.py
          └─ [step_by_step] → agent/workflow/engine/sbs_loop/
            └─ agent/workflow/engine/executor/dag_runner.py
              └─ agent/workflow/engine/executor/kernel_graph_runner.py
                └─ LangGraph compiled graph (checkpoints via PostgreSQL)
```

### Engine Layer Deep-Dive

`agent/workflow/engine/` contains **three execution engines**:

| Engine | Path | Purpose | Key Files |
|--------|------|---------|-----------|
| **DAG Executor** | `engine/executor/` | LangGraph 编译 + DAG 执行 + checkpoint/resume | `dag_runner.py`, `kernel_graph_runner.py`, `checkpoint*.py` |
| **PE Engine** | `engine/pe_engine/` | Plan-Execute：先规划步骤再执行 | `planner.py`, `step_runtime.py`, `dag.py`, `instance.py` |
| **SBS Loop** | `engine/sbs_loop/` | Step-by-Step：预定义 Skill DAG + 人工检查点 | `engine.py`, `graph.py`, `dag_runner.py`, `planner.py` |

**Shared infra across engines**: `engine/runtime/` (SSE投影), `engine/workflow_graph/` (DSL物化)

### Import Dependency Analysis

```
Direction        Status    Count   Issues
───────────────  ────────  ──────  ──────────────────────────
agent internal   OK        489     Expected: high internal cohesion
agent → storage  OK         69     Correct: orchestration uses DAL
agent → utils    OK         —      Correct: uses cross-cutting
web → agent      OK         —      Correct: API calls orchestration
storage → agent  ❌ BAD       4     Phase 2: storage must not import agent
agent/workflow   ⚠️ WARN    —     Phase 2: must not import agent/session
  → agent/session
```

### Frontend Architecture

**React Workbench** (`frontend/react/` — 51K lines):
```
App.tsx → router/ → features/
  ├─ chat/        (核心对话界面)
  ├─ workflow/    (工作流可视化)
  ├─ skillLab/    (技能管理)
  ├─ knowledge/   (知识库)
  ├─ admin/       (管理面板)
  ├─ app/         (应用中心)
  ├─ membership/  (会员管理)
  ├─ personalDb/  (个人数据库)
  ├─ scheduler/   (定时任务)
  ├─ profile/     (用户设置)
  └─ notifications/
  
components/
  ├─ layout/      (MainLayout, Sidebar, Header — DESKTOP ONLY)
  ├─ Login/       (认证)
  ├─ common/      (LoadingIndicator, etc.)
  ├─ media/       (文件上传/展示)
  └─ ui/          (通用 UI 组件)
```

**Mobile readiness**: ❌ NONE
- No responsive breakpoints
- No mobile layout components
- No touch-optimized interactions
- Sidebar navigation cannot collapse to mobile
- Chat UI designed for wide screens

### External Dependencies

| Category | Technologies |
|----------|-------------|
| **LLM** | OpenAI, Qwen/DashScope, DeepSeek (via langchain-openai) |
| **Vector** | FAISS-CPU, Chroma (embedded) |
| **DB** | PostgreSQL (via psycopg + langgraph-checkpoint-postgres) |
| **Cache** | Redis (optional, via aiocache[redis]) |
| **Messaging** | Feishu/Lark (via lark-oapi) |
| **Payments** | Alipay (via alipay-sdk-python) |
| **MCP** | mcp + fastmcp (official) |
| **Web** | FastAPI + Uvicorn + httpx |
| **Search** | DuckDuckGo, Baidu, Google |

---

## Completion Report
```yaml
completion_report:
  what_was_done: "完整映射了 WisglowAgent 165K 行代码库：14 个顶层模块、6 层 workflow 架构、3 套执行引擎、import 依赖链、前端结构、外部依赖"
  key_decisions:
    - decision: "识别出三引擎 (DAG/PE/SBS) 共享 runtime/infra 层但各有独立执行器"
      rationale: "说明合并可行性高 — 共享层已存在，仅执行器差异需收敛"
    - decision: "识别出 4 处 storage→agent 反向 import 和 session↔workflow 环"
      rationale: "Phase 2 清理目标明确，修复成本低"
    - decision: "前端 51K 行完全无移动端适配"
      rationale: "无响应式断点、无移动布局组件、无触摸优化 — 需独立构建或大幅改造"
  handoff_focus:
    - "architect: engine 层三合一方案、移动端架构选型 (独立 PWA vs 响应式改造)"
    - "ux-researcher-designer: 移动端对话交互与桌面端核心差异"
    - "senior-frontend: 评估现有组件复用度、构建移动端组件树"
  open_questions:
    - "PE engine 和 SBS loop 是否有用户场景不可合并的差异"
  known_constraints:
    - "LangGraph checkpoint 机制深度绑定各引擎实现"
    - "前端无设计系统可移动端复用，需从 DESIGN.md 扩展"
```
