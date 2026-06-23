# UX Design Spec: Robot Fleet Ops Dashboard

## User Profile: 运维工程师 (Fleet Ops Engineer)

**Context**: 在中国/国际化机器人公司的运维中心工作。盯着一批人形机器人的实时状态，需要快速发现和处理异常。可能是轮班制（24/7），需要在暗光环境下工作。

**Key attributes**:
- 技术能力强：能理解关节温度、网络延迟等技术指标
- 信息过载：同时监控 6-50 台机器人，需要从噪声中快速提取信号
- 时间敏感：机器人摔倒/失联需要秒级响应
- 需要协作：团队多人轮班，需要交接上下文

**Pain points addressed**:
- 当前需要在多个终端/工具之间切换
- 异常发现滞后（人工巡检）
- 交接时信息丢失

---

## Journey Map: 异常响应流程

```
┌─────────────────────────────────────────────────────────┐
│ TIME    │ ACTION              │ TOUCHPOINT    │ EMOTION  │
├─────────┼─────────────────────┼───────────────┼──────────┤
│ T+0s    │ 机器人摔倒          │ —             │ —        │
│ T+1s    │ 告警触发            │ 侧边栏高亮    │ 警觉     │
│         │ CRITICAL 红色闪烁   │ + 声音提示    │          │
│ T+2s    │ 点击告警/卡片       │ 打开详情面板  │ 专注     │
│ T+5s    │ 查看关节状态        │ 传感器表格    │ 分析     │
│         │ 确认是机械故障      │ 失联关节标红  │          │
│ T+10s   │ 标记"我在处理"      │ 详情面板按钮  │ 控制     │
│         │ 留言 @同事          │ 评论区        │ 协作     │
│ T+30s   │ 确认告警            │ 侧边栏→归档   │ 缓解     │
│ T+5min  │ 查看历史曲线        │ 详情面板图表  │ 复盘     │
│         │ 对比近7天温度趋势   │              │          │
│ T+10min │ 导出报表            │ 导出→CSV     │ 完成     │
└─────────────────────────────────────────────────────────┘
```

---

## Interaction Design: 三层信息架构

### Layer 1: Glance (一瞥) — 3秒判断全局
- 顶部状态条：`6台在线 / 6台总数` + 活跃告警计数
- 环形图：在线(绿) / 离线(灰) / 异常(红) 比例
- **关键设计**：不滚动即可看到全体状态。屏幕上半部分 = 无须交互。

### Layer 2: Scan (扫视) — 10秒定位异常
- 机器人卡片网格，按状态排序（异常 → 警告 → 正常 → 离线）
- 异常卡片自动置顶 + 红色边框脉冲动画
- 卡片内容精简：名字、电量条、状态灯、最后上报时间、告警计数徽章
- **关键设计**：异常不应被正常信息淹没。视觉层次引导眼神。

### Layer 3: Deep Dive (深入) — 点击展开详情
- 侧滑面板（Drawer）展示完整传感器数据
- 关节温度表：每行一个关节，温度值 + 色条（绿→黄→红渐变）
- 历史曲线：默认展示过去 24h，可切换时间范围
- 评论区在面板底部，不遮挡数据

---

## Layout Design

```
┌──────────────────────────────────────────────────────────┐
│  HEADER: [Logo] Fleet Ops   [6/6 Online] [⚠ 2]  🌙 🌐 ⚙ │
├───────────┬──────────────────────────────────────────────┤
│           │  ┌──────────────────────────────────────┐    │
│  ALERT    │  │  DASHBOARD OVERVIEW (collapsible)    │    │
│  PANEL    │  │  ┌────┐ ┌──────────────┐ ┌───────┐ │    │
│           │  │  │Ring│ │  Line Chart  │ │Heatmap│ │    │
│ ⚠ Robot3 │  │  │    │ │  Battery 1h  │ │ Joint │ │    │
│   摔倒    │  │  └────┘ └──────────────┘ │  Temp │ │    │
│           │  │  ┌──────────────────────┐└───────┘ │    │
│ ⚠ Robot5 │  │  │      Robot Map       │          │    │
│   电量低  │  │  └──────────────────────┘          │    │
│           │  └──────────────────────────────────────┘    │
│ (可收起)  │                                              │
│           │  ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│           │  │ Robot 1 │ │ Robot 2 │ │ Robot 3 │  ⚠     │
│           │  │ ████ 85%│ │ ████ 72%│ │ ██░░ 34%│        │
│           │  │ ● Online│ │ ● Online│ │ ● ERROR │        │
│           │  │ 12s ago │ │ 5s ago  │ │ just now│        │
│           │  └─────────┘ └─────────┘ └─────────┘        │
│           │  ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│           │  │ Robot 4 │ │ Robot 5 │ │ Robot 6 │        │
│           │  │ ████ 91%│ │ ██░░ 18%│ │ ░░░░ OFF│  ⚠     │
│           │  │ ● Online│ │ ⚠ LowBat│ │ ● Offline│       │
│           │  │ 3s ago  │ │ 8s ago  │ │ 2m ago  │        │
│           │  └─────────┘ └─────────┘ └─────────┘        │
└───────────┴──────────────────────────────────────────────┘
```

---

## Color System

| Semantic | Color | Hex | Usage |
|----------|-------|-----|-------|
| Normal/Online | Green | #22c55e | Status dot, normal temp cells |
| Warning | Amber | #f59e0b | Low battery, elevated temp |
| Critical/Error | Red | #ef4444 | Fallen, joint lost, alert badge |
| Offline | Grey | #94a3b8 | Offline card, muted text |
| Info/Neutral | Blue | #3b82f6 | Charts, interactive elements |

**Accessibility**: 所有颜色状态同时用图标/形状表达（色盲友好）。状态灯不仅是颜色，还有形状差异：● 在线、◐ 降级、○ 离线。

---

## Motion Design

| Element | Animation | Purpose |
|---------|-----------|---------|
| Alert notification | Red border pulse (2s loop, fade) | 吸引注意力但不遮挡数据 |
| Card reorder | Smooth FLIP transition (300ms) | 异常卡片升至顶部时保持空间感知 |
| Chart update | Data point slide-in (no animation on axis) | 新数据进入不破坏阅读 |
| Theme toggle | Background color crossfade (400ms) | 舒适的明暗切换 |
| Detail drawer | Slide from right (250ms ease-out) | 建立空间模型：详情在右侧 |

**Motion constraint**: 所有动画 < 400ms，可通过 `prefers-reduced-motion` 禁用。

---

## Interaction Patterns

### Alert Flow
1. 新告警 → 侧边栏顶部插入红色条 + 声音提示
2. 对应机器人卡片红色边框脉冲
3. 点击告警 → 展开机器人详情
4. 确认 → 告警状态变为"已确认"（黄色），5min 后自动归档
5. 解决 → 告警状态变为"已解决"（灰色），移至归档

### Robot Card States
| State | Visual | Interaction |
|-------|--------|-------------|
| Online, normal | 绿色状态灯, 正常边框 | 点击→详情 |
| Online, warning | 黄色状态灯, 告警徽章 | 点击→详情(自动滚动到告警指标) |
| Error/Critical | 红色状态灯, 脉冲边框, 自动置顶 | 点击→详情(自动展开异常关节) |
| Offline | 灰色状态灯, 卡片半透明 | 点击→详情(显示最后已知状态) |

### Config Panel
- 从详情面板进入（齿轮图标）
- 每个配置项旁边显示当前值 + 默认值对比
- 滑块控件用于阈值调整（可视化比例关系）
- 修改后即时生效，无需保存按钮（乐观更新）

---

## Empty & Error States

| Scenario | Visual |
|----------|--------|
| 无机器人连接 | 空状态插画 + "Waiting for robot connection..." 文本 + 模拟连接按钮 |
| 数据流中断 | 顶部横幅 "Data stream interrupted — reconnecting..." + 旋转图标 + 卡片显示最后已知数据（灰色叠加 "stale" 标记） |
| 无历史数据 | 图表区域显示 "No historical data available yet — collecting..." |
| 无告警 | 侧边栏显示绿色勾 "No active alerts" |
| 导出失败 | Toast 通知 "Export failed — retry?" |

---

## Completion Report

- **what_was_done**: Produced UX design spec covering user profile, journey map, 3-layer information architecture, layout design, color system, motion design, interaction patterns, and empty/error states
- **key_decisions**: [(1) 3-layer info hierarchy (glance/scan/deep-dive) — ops engineers need progressive disclosure, (2) Color + shape dual encoding for accessibility, (3) Anomalous cards auto-sort to top — reduces scan time, (4) Motion < 400ms with reduced-motion support — respect user preferences, (5) Optimistic config updates — instant feedback for power users]
- **handoff_focus**: ui-design-system should implement the color tokens and component primitives; senior-frontend should implement the 3-layer layout and interaction patterns; epic-design should enhance the dashboard overview with cinematic chart transitions
- **open_questions**: None
- **known_constraints**: Demo is single-page; no multi-tab or cross-session state persistence
- **confidence_differential**: 0.88
