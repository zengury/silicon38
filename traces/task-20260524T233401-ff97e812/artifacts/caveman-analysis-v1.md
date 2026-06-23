# Caveman Output — task-20260524T233401-ff97e812

## Plain-Language Explanation

### What WisglowAgent Is
A big brain that answers questions and does tasks for companies. You type or speak, it thinks, uses tools, gives answers.

### How It Works (simple)
1. **You ask** → question goes to FastAPI server
2. **Router decides** what kind of question: chitchat, workflow step, memory recall, tool use
3. **LLM thinks** → picks tools → calls them → gets results → thinks more → gives answer
4. **Answer streams back** to you in real-time (SSE)

### Key Pieces
| Piece | What it does | One sentence |
|-------|-------------|-------------|
| **SessionOrchestrator** | Traffic controller | Decides which engine handles your request |
| **ReAct Engine** | Tool-using loop | Think → Act → Observe → repeat until done |
| **PE Engine** | Plan-Execute | Plans steps first, then runs them one by one |
| **SBS Loop Engine** | Step-by-step | Runs predefined skill DAGs with human checkpoints |
| **MCP Client** | Tool connector | Talks to external tools via standard protocol |
| **Skill System** | Reusable abilities | Pre-packaged capabilities with prompts, tools, workflows |
| **Workflow Instance** | State machine | Tracks long-running multi-step processes with checkpoints |
| **Ontology** | Knowledge graph | Structured domain knowledge for reasoning |

### What's Missing
- **No phone interface**. Everything is built for desktop screens.
- **Three engines doing similar things**. DAG, PE, SBS — each runs steps. Why three?

## Minimum Viable Version
The simplest version that works:
- One conversation loop (ReAct engine alone)
- One LLM provider
- Web API + basic HTML chat interface
- No workflows, no ontology, no multi-tenancy, no payments

## Complexity Assessment

### Justified Complexity
- **Session gateway (entry_gate)** — needed, 7+ entry modes is real product complexity
- **Multi-model LLM routing** — enterprise requirement, different models for different tasks
- **Tenant isolation** — B2B SaaS must-have
- **Checkpoint/resume** — long workflows need this, not optional
- **MCP standard** — industry standard, using it is correct

### Unnecessary Complexity
- **Three execution engines (DAG / PE / SBS)** — all run steps in sequence or DAG. Codebase has comments saying Phase 2 aims to converge them. Current state: duplicated state management, duplicated streaming logic, duplicated error handling.
- **`agent/session` ↔ `agent/workflow` circular-ish dependency** — code has Phase 2 comments acknowledging this. Adds fragility.
- **`storage` importing `agent`** — persistence layer knowing about orchestration. Violates layered architecture.
- **165K lines for what is essentially LLM + tools + workflow** — high line count suggests abstraction overhead.

### Caveman Verdict
> System do 3 things: route request, run LLM+tools, stream answer.
> Line count 165K. Three engines do same thing.
> Frontend desktop-only. Phone user left out.
> Fix: one engine, mobile client, clean imports.

---

## Completion Report
```yaml
completion_report:
  what_was_done: "对 WisglowAgent 进行第一性原理拆解，识别核心结构、必要复杂度与不必要复杂度"
  key_decisions:
    - decision: "三引擎并存是当前最大架构债务"
      rationale: "DAG/PE/SBS 三套引擎均执行步骤编排，共享 70%+ 概念（状态管理、流式输出、错误处理），注释已标注 Phase 2 收敛目标"
    - decision: "最小可用版本仅为 ReAct 引擎 + 单一模型 + HTML 对话界面"
      rationale: "说明当前 165K 行中存在大量可减法空间"
  handoff_focus:
    - "architect 需重点评估三引擎收敛方案"
    - "移动端构建无需完整架构理解，仅需 API 层和对话 SSE"
    - "import 循环是低风险高收益的清理项"
  open_questions:
    - "三引擎的用户场景是否真有不可合并的差异"
    - "Phase 2 注释是否已在某分支实现"
  known_constraints:
    - "LangGraph checkpoint 机制绑定执行引擎设计，合并不只是代码重构"
    - "向后兼容约束：已有 workflow_instance 依赖 PE/SBS 语义"
```
