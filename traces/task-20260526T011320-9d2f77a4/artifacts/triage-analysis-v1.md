# Triage Analysis: Robot Fleet Ops Dashboard

## Problem Statement

运维工程师缺乏统一面板来监控分布式人形机器人车队的实时状态。当前数据源格式不统一（JSON / Protobuf 衍生格式，字段名和单位不一致），异常检测滞后，团队协作碎片化，历史回溯和报表生成依赖手动拼接。需要一个 Web 端统一监控面板，实时展示、告警、协作、配置、导出全闭环。

## Scope

### In Scope
1. 实时遥测面板：电量、关节温度、CPU、网络延迟、当前任务、地理位置
2. 异构数据归一化层：统一不同机器人回传格式（JSON / Protobuf → 统一 schema）
3. 总览仪表盘：环形图、折线图、热力图多维度车队健康度
4. 告警引擎：摔倒、关节失联、电量过低的判定与通知
5. 历史曲线：每台机器人过去 30 天数据回溯与可视化
6. 配置面板：告警阈值、采样频率、重连策略的按机器人调整
7. 协作功能：留言、@同事、"我在处理"标记
8. 报表导出：PDF / Excel
9. 主题与布局：暗/亮色切换、多语言、可拖拽自定义布局
10. 架构设计文档 + 核心界面设计 + 可运行 Demo

### Out of Scope
- 机器人端固件或数据采集逻辑
- 实际部署的 CI/CD 流水线
- 生产级安全审计
- 移动端 App
- 机器人直接控制（只读监控）
- 多租户/组织管理
- 计费或权限体系（RBAC 留接口，不深入实现）

## Recommended Agent Team

| Layer | Role | Rationale |
|-------|------|-----------|
| 1 | to-prd | 将 9 项需求转为可测试的 PRD，明确验收标准 |
| 2 | architect | 系统架构设计：数据流、组件拓扑、技术选型 |
| 2 | ux-researcher-designer | 运维工程师用户画像 + 交互流程设计 |
| 2 | ui-design-system | 组件库 + 设计 Token + 暗/亮主题体系 |
| 2 | senior-frontend | Demo 前端实现 |
| 2 | epic-design | 仪表盘视觉冲击力：动效、环形图、热力图叙事 |
| 2 | database-engineer | 时序数据存储方案（30 天历史） |
| 3 | code-reviewer | Demo 代码审查 |

## Blocking Questions

_None. 需求足够明确，可直接启动。_

## Priority: **High**

车队监控是运维刚需，9 项需求覆盖完整运维闭环。Demo 优先交付架构+核心界面，非关键功能（多语言、报表导出）可在 Demo 阶段简化为占位。
