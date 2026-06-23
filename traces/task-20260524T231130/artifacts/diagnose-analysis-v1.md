# Diagnose Report — TeamUp 编排器卡顿问题

## Phase 1 — 反馈回路

**回路**: 启动服务 → 发送测试消息 → 观察 WebSocket 事件流是否在合理时间内完成

```bash
# 回路脚本
curl -s http://localhost:8000/api/state | jq .active_turn
# 期望: 30s 内 active_turn 从 true 变为 false 且 agent 状态回到 idle
```

## Phase 2 — 复现

通过代码静态分析确定以下卡顿路径（不需要运行时复现，因为根因可通过代码审查确认）：

### 路径 A: LLM 调用超时 → 静默卡死
```
chat_complete() → openai API 超时 → {"error": "..."} 
→ agent.py 返回 error 文本 → orchestrator 当作正常输出 
→ _needs_user_input() 检查 error 文本 → 不含确认词 → 自动推进
→ 下一轮再次失败 → 3 轮耗尽 → 静默结束
```
**影响**: 用户看到 "thinking" → "idle"，无输出，无错误提示

### 路径 B: 工具执行失败 → 唐僧不知
```
子 agent run_task("写代码") → bash 命令失败 → 返回 "命令执行完毕(rc=1)"
→ orchestrator 截取前 200 字符 → "命令执行完毕(rc=1)"
→ 唐僧认为任务完成 → 继续下一步
```

### 路径 C: 停等判断遗漏
```
LLM: "您觉得这个方案可以继续推进吗？"
→ _needs_user_input 检查: ["确认","对吗","可以吗"...] 
→ "可以继续推进吗" 不含上述任一关键词 → 返回 False → 自动推进
```

## Phase 3 — 假设（按可能性排序）

| # | 假设 | 预测 | 置信度 |
|---|------|------|--------|
| 1 | `_needs_user_input` 关键词匹配不够全面 | 增加更多中文确认模式 → 停等准确率提升 | 高 |
| 2 | LLM 失败后无重试机制 | 添加指数退避重试 → 瞬时错误不再导致卡死 | 高 |
| 3 | 3 轮硬上限过早截断 | 替换为任务完成检测 → 长任务正常完成 | 中 |
| 4 | 子 agent 输出截断至 200 字符 | 改为结构化摘要 → 唐僧决策质量提升 | 中 |
| 5 | 状态机未做门控 | 添加阶段检查 → 防止跳步 | 低 |

## Phase 4 — 修复方案

### Fix 1: 加强停等判断 (P0)
将关键词匹配改为结构化输出。唐僧的 system prompt 要求 LLM 在每个回复中包含 `[NEEDS_USER_INPUT: true/false]`，运行时解析此标记。

### Fix 2: LLM 调用重试 (P0)
在 `chat_complete()` 添加 3 次指数退避重试。失败后推送明确的错误事件。

### Fix 3: 动态推进上限 (P1)
移除 `range(3)`，改为：当 `_needs_user_input` 返回 False 且任务未明确完成时继续推进，但最多连续 5 轮后强制要求确认。

### Fix 4: 子 agent 结构化输出 (P1)
子 agent 输出增加状态标记：`[TASK_STATUS: success/failed] [ERRORS: ...]`，orchestrator 解析而非依赖文本预览。

## Phase 5-6 — 在代码更改中完成
