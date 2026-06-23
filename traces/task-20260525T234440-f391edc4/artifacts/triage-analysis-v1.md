# Triage Analysis — 机器人车队运维监控面板

## Problem Statement

运维工程师需要一套 Web 运维面板，实时监控一批人形机器人的运行状态，并在异常发生时快速响应。车队中的机器人回传数据格式不统一（JSON / Protobuf 衍生，字段名和单位不一致），面板需要统一呈现。工程师还需要历史数据回溯、团队协作、报表导出、个性化配置等辅助能力。

**Falsifiable**: 若面板无法在机器人异常发生后 5 秒内触发告警、或无法同时展示 50 台以上机器人的实时数据、或无法正确归一化至少 2 种异构数据格式，则面板未达到可用标准。

## Scope

### In Scope
1. 实时状态面板：电量、关节温度、CPU、网络延迟、当前任务、地理位置 — 每台机器人独立卡片/行展示
2. 异构数据归一化层：统一不同格式（JSON/Protobuf 衍生）和不同字段名/单位到标准 schema
3. 总览仪表盘：环形图（健康度占比）、折线图（时序趋势）、热力图（车队分布）
4. 异常告警系统：摔倒、关节失联、电量过低 → 实时推送 + 分级（warning/critical）
5. 历史曲线查询：每台机器人过去 30 天的时序数据，支持缩放和对比
6. 配置面板：告警阈值、采样频率、重连策略 — 按机器人独立配置
7. 团队协作：机器人级留言、@同事、标记「我在处理」→ 防止重复响应
8. 报表导出：PDF / Excel，可选时间范围和机器人筛选
9. 主题切换（暗色/亮色）、国际化、可拖拽自定义布局

### Out of Scope
- 机器人控制 / 远程操作 / 下发指令（只读监控，不写控制）
- 硬件部署 / 网络拓扑规划
- 计费 / 权限管理系统（假定已有 SSO）
- 移动端 App（本次仅 Web）
- 实际代码实现（本次产出为架构方案 + 界面设计）

## Recommended Agent Team

| Priority | Role | Rationale |
|----------|------|-----------|
| 1 | `to-prd` | 将 9 项需求转为可验证的产品需求文档 |
| 2 | `ux-researcher-designer` | 运维工程师用户画像、关键旅程映射（告警响应路径） |
| 3 | `architect` | 系统架构：数据管线、实时推送、存储分层、前端架构 |
| 4 | `ui-design-system` | 设计系统：组件库、设计 Token、暗色/亮色主题 |
| 5 | `senior-frontend` | 前端技术选型、组件拆分、状态管理方案 |
| 6 | `grill-me` | 架构和设计方案的对抗性审查 |
| 7 | `code-reviewer` | 最终交付物质量把关 |

## Blocking Questions

_None._ 用户需求描述清晰，9 个功能点具体、可验证。无歧义阻塞项。

## Priority

**High.** 9 大功能领域，跨数据工程、实时系统、前端可视化、协作工具四个技术域。不经过系统化架构分解直接开工将导致返工和集成冲突。

## Completion Report

```yaml
completion_report:
  what_was_done: "分类用户请求为 structured work item，界定范围，推荐 agent 团队"
  key_decisions:
    - decision: "任务类型 complex/multi-part，入口 triage + caveman"
      rationale: "跨 feature + design + architecture 三个域，必须双入口并行以减少遗漏"
    - decision: "将机器人控制标记为 out-of-scope"
      rationale: "用户需求描述中无控制指令，运维面板天然是只读监控系统；控制引入会显著增加安全审查和测试成本"
    - decision: "优先 to-prd → ux-researcher-designer → architect 作为 Layer 2 第一波激活"
      rationale: "需求文档 + 用户调研 + 架构设计构成不可压缩的前置阶段，跳过任何一环会导致下游返工"
  handoff_focus:
    - "to-prd: 将 9 项需求转为可测试的产品规格，明确验收条件"
    - "ux-researcher-designer: 运维场景用户旅程，特别是告警响应和协作流程"
  open_questions: []
  known_constraints:
    - "异构数据格式归一化是整个系统的入口瓶颈，架构设计必须优先解决"
    - "不涉及机器人控制命令下发"
  confidence_differential: 0.05
  dissent_if_alone: null
```
