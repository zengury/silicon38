# Task Triage Report

## Classification

| 维度 | 判定 |
|------|------|
| **类别** | `bug` + `enhancement` (复合) |
| **严重度** | 🔴 Critical — 执行卡顿导致系统不可靠 |
| **UI 改动** | 🟡 Major — 视觉主题彻底改造 |

## Issue Breakdown

### Bug #1: 编排器静默卡死
- **症状**: 团队在某个环节停止推进，无错误反馈，UI 显示 "thinking" 持续
- **触发条件**: LLM API 超时/限流、子 agent 工具执行失败、`_needs_user_input` 误判
- **影响**: 用户不知道系统是在工作还是卡死了

### Bug #2: 自动推进提前截断
- **症状**: 复杂任务在 3 轮自动推进后静默结束，工作未完成
- **触发条件**: `range(3)` 硬上限
- **影响**: 产出不完整，用户以为完成了

### Bug #3: 子 agent 失败不可见
- **症状**: 八戒/猴哥工作失败，唐僧不知道，继续下一步
- **触发条件**: 工具错误被吞没，输出被截断到 200 字符
- **影响**: 基于失败产出做后续决策

### Enhancement: Cyberpunk UI 改造
- **范围**: 整个前端 (HTML + CSS + JS) + agent 角色设定
- **约束**: 保持 5 agent 结构、WebSocket 事件流、文件管理功能不变

## Priority

1. **P0 — 立即**: 修复反馈回路（LLM 超时重试 + 错误可见 + 停等判断加强）
2. **P1 — 同时**: Cyberpunk UI 改造（与 P0 无依赖）
3. **P2 — 后续**: 状态机门控、模块解耦

## Entry Nodes Selected
→ zoom-out (完成), ux-researcher-designer (完成), triage (当前), caveman (并行)
