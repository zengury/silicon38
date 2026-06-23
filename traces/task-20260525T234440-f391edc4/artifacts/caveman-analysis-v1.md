# Caveman Analysis — 机器人车队运维监控面板

## Plain-Language Explanation

**What it is**: A screen that shows the health of many walking robots, all at once. Like a hospital nurse station, but for robots instead of patients. Each robot has a card showing its vitals (battery, joint heat, brain load, connection speed, what it's doing, where it is). When something goes wrong — a robot falls, a joint goes silent, the battery gets too low — the screen lights up red and makes noise until a human responds.

**Why it matters**: These robots cost money. When one is down, it's not doing work. When one is about to fail, catching it early saves the repair cost. When many run at once, no human can watch them all without a dashboard.

**How the data flows**: Robot pings home with its status → data arrives in different shapes (some JSON, some not) → a normalizer makes them all the same shape → the dashboard draws them → if something looks bad, an alert fires → engineer sees it and acts.

## Minimum Viable Version

**What would actually work for one shift**: One page. A table of robots. Each row shows: name, online/offline dot, battery %, one alert count. Click a row → detail panel with all vitals. That's it.

**What the minimum does NOT need**:
- No drag-and-drop layout (table is fine)
- No team comments (use Slack)
- No PDF export (screenshot the table)
- No dark mode, no i18n (one language, one theme)
- No historical curves (look at right now, act right now)

Everything else — charts, themes, collaboration, export — is gravy on top of the table. Good gravy. But gravy.

## Complexity Assessment

### Justified Complexity

| Feature | Justification |
|---------|--------------|
| Heterogeneous data normalizer | Robots come from different vendors/generations. Can't change firmware on all of them. Normalizer is the price of heterogeneity. |
| Real-time push (WebSocket/SSE) | Robot falls → 5s polling latency is too slow. Push is required, not optional. |
| Multiple chart types (ring/line/heatmap) | Battery is a single number → ring chart suits it. Temperature over time → line chart. Fleet geography → heatmap. Different data shapes demand different views. One chart type can't serve all. |
| Historical 30-day curves | "Was this robot slowly getting worse or did it just break?" Without history, you can't answer this. 30 days covers one maintenance cycle. |
| Alert severity levels | "Battery at 20%" vs "Robot fell over" are not the same urgency. Two levels (warning/critical) is the minimum useful distinction. Three would be overkill. |
| Per-robot config thresholds | A robot in a cold warehouse has different safe temperature range than one in a hot factory. One threshold for all would create noise (false alarms) or silence (missed alarms). |
| Team collaboration (@mentions, claim) | Two engineers both digging into the same robot is wasted time. Claiming prevents this. @mentions route attention. Both are lightweight coordination, not a full chat system. |

### Unnecessary Complexity (Defer)

| Feature | Why Defer |
|---------|-----------|
| Drag-and-drop layout | Nice to have. Default layout (grid of cards) covers 90% of use cases. Make the default good, add customization later. |
| Multi-language i18n | Start with one language (the ops team's language). Add i18n when the second team with a different language joins. |
| Dark/Light theme | Dark mode is essential for 24/7 ops rooms (eye strain). Light mode for daytime offices. This is borderline — implement dark mode from day one, light mode can follow. |

### The Knife

Use the fleet dashboard knife from soul.md: *"In the seconds a machine is failing: which one, what's wrong, how long is left, what to do."* Every feature must serve this act or be questioned. The alert-to-response path is the true act. Chasing layout customization before the alert path is solid is building the roof before the foundation.

## Completion Report

```yaml
completion_report:
  what_was_done: "将 9 项需求的系统用平实语言描述，识别最小可行版本，区分合理复杂度和可推迟复杂度"
  key_decisions:
    - decision: "暗色主题标记为 borderline — 从 day one 实现，亮色主题可推迟"
      rationale: "7×24 运维中心暗色主题是刚需（眼疲劳），不是 aesthetic preference"
    - decision: "拖拽布局标记为可推迟"
      rationale: "默认网格布局覆盖 90% 场景。先做好默认体验，再开放自定义"
    - decision: "告警分级确定为 2 级（warning/critical），不做 3 级"
      rationale: "2 级是最小有用区分；3 级增加认知负荷但收益递减"
  handoff_focus:
    - "architect: 异构数据归一化层是整个系统的咽喉，架构设计必须从这里开始"
    - "to-prd: 明确 '告警→响应' 作为核心用户旅程，所有 feature 围绕它评估优先级"
  open_questions:
    - "异构数据源是 2 种还是 20 种？影响归一化层的复杂度"
    - "车队规模上限是多少？影响 WebSocket 连接数和前端渲染策略"
  known_constraints:
    - "只读监控，不涉及控制指令"
    - "Web 平台，非移动端"
  confidence_differential: 0.0
  dissent_if_alone: null
```
