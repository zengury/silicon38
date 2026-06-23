# TeamUp Codebase Context Map — zoom-out Analysis

## Module Inventory

```
teamup/
├── server.py              FastAPI 入口，WebSocket 广播，后台工作线程
├── static/
│   ├── index.html         控制台 UI (中式水墨主题)
│   ├── style.css          水墨配色/排版 (rice, ink, vermilion, gold)
│   └── app.js             WebSocket 事件处理 + SVG 流动线
├── teamup_core/
│   ├── config.py          路径/团队定义/环境变量加载
│   ├── agent.py           Agent 对话循环 (工具调用 + 子 agent 执行)
│   ├── llm.py             DeepSeek API 客户端 (流式+非流式，invoke 过滤)
│   ├── orchestrator.py    唐僧编排逻辑 (委派 + 自动推进)
│   ├── session.py         会话/客户端管理 + 状态机
│   └── tools.py           8 个工具实现 (read/write/edit/glob/grep/bash/web)
├── prompts/               Markdown system prompts (唐僧/八戒/猴哥/沙僧/白龙马)
└── agents_yaml/           Agent 配置 (model 选择)
```

## Data Flow

```
用户 → [HTTP POST] → server.py → chat_turn_worker (后台线程)
                                    ↓
                              Orchestrator.run_turn()
                                    ↓
                         唐僧 (Agent.chat_stream_loop)
                          ↕ delegate_task 工具
                    ┌───────┼───────┬────────┐
                   八戒    猴哥    沙僧    白龙马
                  (PRD)  (代码)  (测试) (客户成功)
                    ↓       ↓       ↓        ↓
              结果回传唐僧 → 唐僧判断是否继续 → 推送到 WebSocket
                                                 ↓
                                          app.js 渲染 UI
```

## Friction Points (Execution Fragility)

### 1. `_needs_user_input()` — 过于脆弱的停等判断
**文件**: `orchestrator.py:86-88`
```python
def _needs_user_input(self, text: str) -> bool:
    markers = ["确认", "对吗", "可以吗", "是否", "请确认", "您看", "你选", "请问", "需要您"]
    return any(m in text for m in markers)
```
- 仅依赖关键词匹配，LLM 用同义词（如"您觉得呢""这个方向合适吗"）会漏过
- LLM 不用这些词 → 自动推进 → 跳过确认点 → 产生不符合预期的输出

### 2. 自动推进上限 `range(3)` 无状态感知
**文件**: `orchestrator.py:53`
- 无论任务多复杂，最多自动推 3 轮
- 复杂任务（PRD→代码→测试→修改）在 3 轮内不可能完成
- 3 轮后静默结束，用户不知道是否完成

### 3. LLM 调用无超时/重试
**文件**: `llm.py` — `chat_complete()` 无超时参数
- DeepSeek API 偶尔超时/限流 → 异常被捕获 → 返回 error → 流程中断但 UI 无明确反馈
- Agent 卡在 `thinking` 状态，用户看不到错误

### 4. 工具执行错误静默吞没
**文件**: `agent.py:87` — 工具执行 catch 后只返回文本
- bash 命令失败、文件不存在等错误对用户不可见
- 唐僧不知道子 agent 工作失败，继续委派下一步

### 5. 子 agent 输出被截断
**文件**: `orchestrator.py:115`
```python
preview = result[:200].replace("\n", " ")
```
- 唐僧只看前 200 字符，可能遗漏关键信息
- 没有结构化摘要机制

### 6. Session 状态机未实际驱动流程
**文件**: `session.py:55` — STAGES 定义存在但 orchestrator 未使用
- 状态机定义了 init→prd→tech_spec→code→test→customer_success→done
- 但 orchestrator 只用 `_state["stage"]` 记录当前阶段，不做门控
- 例如：代码未完成就可能跳到测试

## Module Coupling

- `orchestrator.py` 同时处理：委派逻辑、状态判断、历史管理、文件推送 → 单一模块承载过多职责
- `agent.py` 的 `chat_stream_loop` 和 `run_task` 有大量重复的工具执行逻辑
- `server.py` 的全局状态 (`ACTIVE_TURN`, `LAST_STATE`) 通过闭包共享，不可测试

## Summary
核心问题不在功能缺失，而在**反馈回路断裂**：LLM 失败 → 无通知，任务未完成 → 静默结束，子 agent 出错 → 唐僧不知。UI 是表象问题，执行鲁棒性是根因。
