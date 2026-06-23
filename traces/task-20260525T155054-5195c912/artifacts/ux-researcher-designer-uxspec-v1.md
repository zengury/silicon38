# UX Design Spec: 机器人车队运维监控面板

---

## 1. User Personas

### Persona 1: 张伟 (Zhang Wei) — Primary Operator

| Dimension | Detail |
|-----------|--------|
| Role | 中级运维工程师 / Mid-level Fleet Operator |
| Age | 29 |
| Experience | 4年运维, 1.5年机器人运维 |
| Tech Level | 高 — CLI, 脚本, 监控系统熟练 |
| Work Setup | 办公室双显示器 (2560×1440), 偶尔笔记本远程 |
| Shift | 正常班 + 每周1次 On-call |
| Team | 4人同组, 同时在线2-3人 |

**Goals**:
- 10秒判断车队整体状态 — 扫一眼就知道有没有问题
- 从告警到定位问题 ≤ 3次点击
- 知道谁在处理哪台机器人, 避免冲突
- 配置可追溯, 有人改过要知道

**Frustrations**:
- "告警太多, 真正紧急的淹没在warning里"
- "每台机器人的数据格式不一样, 每天花30分钟手动转格式"
- "修一台机器人时同事不知道, 也在同时操作, 配置互相覆盖"

---

### Persona 2: 李明 (Li Ming) — Fleet Manager

| Dimension | Detail |
|-----------|--------|
| Role | 车队经理 / Fleet Manager |
| Age | 36 |
| Experience | 10年运维管理 |
| Tech Level | 中 — 看Dashboard, 不写脚本 |
| Work Setup | 笔记本, 会议室投屏 |
| Shift | 正常班 |
| Team | 管理12人 |

**Goals**:
- 周报一键生成, 不需要手动截图做PPT
- 看全局趋势 — 车队健康度是在变好还是变差
- 会议时投屏仪表盘, 数据一目了然

**Frustrations**:
- "每周五下午都在手动做周报, 无聊且重复"
- "数据有了但缺少上下文 — 不知道这个数字是变好了还是变差了"

---

### Persona 3: 王芳 (Wang Fang) — On-call Engineer (mobile context)

| Dimension | Detail |
|-----------|--------|
| Role | 高级运维工程师 / Senior Operator |
| Age | 31 |
| Experience | 7年运维 |
| Tech Level | 高 |
| Work Setup | 手机为主 (on-call), 桌面为辅 |
| Shift | On-call轮值 |

**Goals**:
- 手机收到告警, 看一眼决定要不要开电脑
- 告警信息足够丰富 — 机器人ID, 位置, 什么故障, 持续时间

**Frustrations**:
- "告警通知只说'机器人故障', 我得爬起来开电脑才知道要不要紧急处理"
- "移动端看不到趋势, 只能看当前快照"

---

## 2. Journey Maps

### Journey 1: 发现故障 → 定位 → 修复 (张伟)

```
Stage:     监控中      →   告警触发      →   定位       →   处理       →   确认
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Action:    扫总览      →   弹窗+声音     →   点进详情   →   看曲线      →   关告警
           环形图          点告警            面板          查日志          标记已处理
Emotion:   😌 平静       😰 警觉          🧐 专注      🤔 分析        😌 放心
Pain:      数据太密       连续告警轰炸      曲线加载慢    缺少上下文      无自动恢复检测
Need:      可配置密度     告警去重+冷却     预加载数据    一键关联日志    自动检测+通知
```

### Journey 2: 周报生成 (李明)

```
Stage:     周五下午     →   选范围        →   生成        →   投屏
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Action:    打开报表页   →   选本周         →   点"生成"    →   全屏
Emotion:   😤 不想做     😊 这么简单       😌 好了        😎 开会
Pain:      手动截图做PPT                   等待太久
Need:      一键生成                        3秒内生成      暗色主题适配投屏
```

### Journey 3: 移动端看告警 (王芳)

```
Stage:    手机震动     →   看通知        →   决定
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Action:   锁屏通知     →   打开/查看     →   不管 or 开电脑
Emotion:  😰 又是告警    🧐 判断严重度     → 决定
Pain:     信息太少       页面不响应式
Need:     通知含详情：   点击连接详情页
          机器人ID,故障,
          位置,持续时间
```

---

## 3. Design Principles

1. **Answer "which robot needs me?" in ≤ 5 seconds.**
   Everthing on the overview dashboard serves this question or doesn't earn its place.

2. **Data first, decoration second.**
   Dark theme reduces eye strain for long shifts. Charts are about accuracy, not beauty.
   Motion is purposeful — status changes animate, everything else stays still.

3. **Mobile-accessible alert triage, desktop-first operations.**
   The phone tells you whether to get up. The desktop lets you fix things.

4. **One action per alert.**
   Acknowledge (I see it), Dismiss (it's fixed), or Snooze (not now). No other states.

5. **Config changes are transactions.**
   Who changed what, when, from what to what. Always visible. Always undoable.

---

## 4. Core Interaction Patterns

### Real-time Updates
- Status dots pulse on change, not continuously
- Changed values flash briefly (300ms highlight), then settle
- Last-update timestamp visible on each robot card
- Stale indicator: border turns amber after 30s without data

### Alert Flow
```
Robot data arrives → rule evaluated → state machine check →
  (if triggered) → sound (critical: pulse tone, warning: chime) +
                   toast notification (top-right, stacks) +
                   browser notification (if tab unfocused) +
                   badge count on sidebar bell icon

User click toast/jump to robot → acknowledge → WS broadcast → remove from count
```

### Layout
- Sidebar (collapsible, 260px): nav + fleet summary + user info
- Top bar (56px): search, alert badge, theme toggle, user menu
- Content: draggable grid (react-grid-layout), layouts saved per user
- Mobile (< 768px): sidebar becomes bottom tab bar, content stacks vertically

---

## 5. Key Screens

### Screen 1: Fleet Overview
```
┌─────────────────────────────────────────────────────┐
│ 🔍 Search robots...         🔔 3  🌙  👤 张伟      │
├────────┬────────────────────────────────────────────┤
│        │  ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│ 🏠 总览 │  │ Fleet    │ │ Battery  │ │ CPU      │   │
│ 🤖 机器人│  │ Status   │ │ Trend    │ │ Trend    │   │
│ 🚨 告警  │  │ Ring     │ │ Line     │ │ Line     │   │
│ 📊 历史  │  └──────────┘ └──────────┘ └──────────┘   │
│ ⚙️ 配置  │  ┌──────────────────────────────────┐    │
│ 📝 报表  │  │ Robot Card Grid (auto-fill)       │    │
│          │  │ ┌────┐ ┌────┐ ┌────┐ ┌────┐      │    │
│ 在线: 12 │  │ │G1-A│ │G1-B│ │X2-C│ │X2-D│ ...  │    │
│ 离线: 1  │  │ └────┘ └────┘ └────┘ └────┘      │    │
│ 异常: 1  │  └──────────────────────────────────┘    │
└────────┴────────────────────────────────────────────┘
```

### Screen 2: Robot Detail
```
┌─────────────────────────────────────────────────────┐
│ ← 返回车队    G1-Alpha · 🟢 Online    上次更新: 3s  │
├─────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐  │
│  │ Battery │ │ CPU     │ │ Memory  │ │ Network  │  │
│  │  87%    │ │  34%    │ │  62%    │ │  12ms    │  │
│  │ ████▌   │ │ ██▌     │ │ ███▌    │ │ ▏        │  │
│  └─────────┘ └─────────┘ └─────────┘ └──────────┘  │
│  ┌──────────────┐ ┌─────────────┐                   │
│  │ Joint Temps  │ │ GPS/Map     │                   │
│  │ ┌─┬─┬─┬─┐   │ │  📍 31.23N  │                   │
│  │ │42│38│45│41│ │ │     121.47E │                   │
│  │ └─┴─┴─┴─┘   │ │             │                   │
│  └──────────────┘ └─────────────┘                   │
│  ┌──────────────────────────────────────────────┐   │
│  │ Time-series Chart (30-day range selector)    │   │
│  │ ╱╲  ╱╲  ___  ╱╲   ← battery                 │   │
│  │/  ╲/  ╲/   ╲/  ╲  ← cpu                     │   │
│  └──────────────────────────────────────────────┘   │
│  ┌──────────────┐ ┌─────────────┐                   │
│  │ Alert History│ │ Comments    │                   │
│  │ (last 20)    │ │ 💬 张伟:    │                   │
│  │              │ │ 关节温度偏高 │                   │
│  └──────────────┘ └─────────────┘                   │
└─────────────────────────────────────────────────────┘
```

---

## Completion Report

**what_was_done**: Produced UX design spec with 3 personas (operator, manager, on-call), 3 journey maps (fault handling, report generation, mobile alert triage), 5 design principles, interaction patterns for real-time updates and alerts, 2 key screen wireframes (fleet overview + robot detail).

**chain_entry**: "3 personas: 张伟(operator, needs 10s status read), 李明(manager, needs one-click reports), 王芳(on-call, needs mobile alert triage). Core interaction: alert state machine → toast + sound + badge. Draggable grid layout with collapsible sidebar."
