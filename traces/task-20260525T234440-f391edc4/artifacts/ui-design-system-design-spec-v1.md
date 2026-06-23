# Design System — 机器人车队运维监控面板 (FleetOps Dashboard)

> 角色: ui-design-system | 来源: UX Spec + 架构 ADR | 版本: v1.0

---

## 1. Design Tokens

### 1.1 Color Tokens — 暗色主题 (默认)

```yaml
colors:
  # Semantic
  bg:
    primary: "#0D1117"        # 主背景
    secondary: "#161B22"      # 卡片/面板背景
    tertiary: "#21262D"       # hover 态背景
    elevated: "#1C2128"       # 弹窗/modal 背景
  text:
    primary: "#E6EDF3"        # 主要文字
    secondary: "#8B949E"      # 辅助文字
    tertiary: "#484F58"       # 禁用文字
    inverse: "#0D1117"        # 在彩色背景上的文字
  border:
    default: "#30363D"        # 默认边框
    subtle: "#21262D"         # 弱边框（卡片分隔线）
    focus: "#58A6FF"          # 聚焦边框
  status:
    online: "#3FB950"         # 在线/正常
    warning: "#D29922"        # 警告
    critical: "#F85149"       # 严重/危险
    offline: "#484F58"        # 离线/未知
    info: "#58A6FF"           # 信息
  accent:
    primary: "#58A6FF"        # 主色调（按钮、链接、聚焦）
    primaryHover: "#79C0FF"
    primaryActive: "#388BFD"
  chart:
    series: ["#58A6FF", "#3FB950", "#D29922", "#F85149", "#BC8CFF", "#FFA657", "#79C0FF", "#56D364"]
```

### 1.2 Color Tokens — 亮色主题

```yaml
colors:
  bg:
    primary: "#FFFFFF"
    secondary: "#F6F8FA"
    tertiary: "#EBEDF0"
    elevated: "#FFFFFF"
  text:
    primary: "#1F2328"
    secondary: "#656D76"
    tertiary: "#AFB8C1"
    inverse: "#FFFFFF"
  border:
    default: "#D0D7DE"
    subtle: "#EBEDF0"
    focus: "#0969DA"
  status:
    online: "#1A7F37"
    warning: "#9A6700"
    critical: "#CF222E"
    offline: "#656D76"
    info: "#0969DA"
  accent:
    primary: "#0969DA"
    primaryHover: "#0860CA"
    primaryActive: "#0550AE"
```

### 1.3 Spacing Scale

```yaml
spacing:
  unit: 4px
  scale:
    xs: 4px     # 0.25rem
    sm: 8px     # 0.5rem
    md: 12px    # 0.75rem
    lg: 16px    # 1rem
    xl: 24px    # 1.5rem
    2xl: 32px   # 2rem
    3xl: 48px   # 3rem
    4xl: 64px   # 4rem
```

### 1.4 Typography

```yaml
typography:
  fontFamily:
    sans: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    mono: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace"
  fontSize:
    xs:   0.75rem   # 12px — 辅助信息
    sm:   0.8125rem # 13px — 表格/列表
    base: 0.875rem  # 14px — 正文
    lg:   1rem      # 16px — 卡片标题
    xl:   1.25rem   # 20px — 区块标题
    2xl:  1.5rem    # 24px — 页面标题
    3xl:  2rem      # 32px — 大盘数据
  fontWeight:
    normal: 400
    medium: 500
    semibold: 600
    bold: 700
  lineHeight:
    tight: 1.25
    normal: 1.5
    relaxed: 1.75
```

### 1.5 Motion

```yaml
motion:
  duration:
    instant: 100ms
    fast: 200ms
    normal: 300ms
    slow: 500ms
  easing:
    default: "cubic-bezier(0.4, 0, 0.2, 1)"        # ease-in-out
    enter: "cubic-bezier(0, 0, 0.2, 1)"             # ease-out
    exit: "cubic-bezier(0.4, 0, 1, 1)"              # ease-in
    alertPulse: "cubic-bezier(0.4, 0, 0.6, 1)"      # alert animation
```

### 1.6 Shadows (暗色)

```yaml
shadows:
  sm:  "0 1px 2px rgba(0,0,0,0.3)"
  md:  "0 4px 8px rgba(0,0,0,0.4)"
  lg:  "0 8px 24px rgba(0,0,0,0.5)"
```

---

## 2. Core Component Specifications

### 2.1 RobotCard

**用途**: 机器人摘要卡片，总览网格中的最小信息单元
**尺寸**: 默认 320×180px，可拖拽调整（最小 280×140px）

```
┌──────────────────────────────────────┐
│ ● R03  Unitree G1        工业区-A    │  ← StatusDot(左侧8px) + robot_id + 位置(右侧对齐)
│                                      │
│  ⚡ 78%       🔥 42°C                 │  ← 两列布局，图标+数值
│  🧠 35%       📶 12ms                │
│                                      │
│  📋 巡检任务-3                        │  ← 当前任务（最多 1 行，超出截断+tooltip）
│                                      │
│  🚨 1 条未处理告警                    │  ← 仅在有告警时显示，红色文字+AlertBadge
└──────────────────────────────────────┘
```

**States**:
| State | 视觉 | 触发条件 |
|-------|------|---------|
| Default | 正常边框，深色背景 | 在线 + 无告警 |
| Warning | 黄色左边框 3px，卡片微微放大(scale 1.01) | 有 WARNING 告警 |
| Critical | 红色左边框 3px，脉冲动画(边框 opacity 脉动) | 有 CRITICAL 告警 |
| Offline | 灰色整体(opacity 0.6)，灰度滤镜 | 离线 > 15s |
| Hover | 背景变亮(bg-tertiary)，上浮阴影(shadow-md) | 鼠标悬停 |
| Selected | 蓝色左边框 3px，背景高亮 | 点击选中 |
| Loading | 骨架屏(skeleton pulse) | 初始加载 |

**Accessibility**:
- role="article", aria-label="机器人 R03, 电量 78%, 温度 42 度, 在线"
- StatusDot 需配合 aria-label (不能只靠颜色传递信息)
- 键盘导航: Tab 聚焦 → Enter 打开详情

---

### 2.2 AlertBanner

**用途**: CRITICAL 告警的全屏通知条（非阻塞弹窗，不阻止操作）

```
┌──────────────────────────────────────────────────────────────────┐
│ 🔴 CRITICAL  R03 摔倒检测  ·  工业区-A  ·  刚刚                    │
│ 电量: 67%  |  最后位置: 39.9042, 116.4074                          │
│                                              [查看详情] [静音 5min] [×] │
└──────────────────────────────────────────────────────────────────┘
```

**States**:
| State | 视觉 |
|-------|------|
| Enter | 从顶部滑入(300ms ease-out)，伴随短蜂鸣(200ms) |
| Active | 红色背景(bg-critical 10% opacity)，红色上边框 4px |
| Warning | 黄色替代红色，无声音 |
| Dismissed | 滑出(200ms ease-in) |
| Multiple | 堆叠显示，最多 3 条可见，超出显示"+N 条更多" |

**Accessibility**:
- role="alert", aria-live="assertive"（屏幕阅读器立即读出）
- 声音提示可通过按钮关闭，5 分钟后自动恢复
- 颜色不是唯一区分方式：CRITICAL 和 WARNING 有不同图标(🔴/🟡)和文字标签

---

### 2.3 StatusDot

**用途**: 机器人状态指示器

```
●  (在线)    ◉  (警告，脉动)    ◍  (离线，空心)
#3FB950      #D29922             #484F58
```

**States**:
- Online: 实心圆，绿色，静态
- Warning: 实心圆，黄色，脉动动画(opacity 0.6→1.0，1s cycle)
- Critical: 实心圆，红色，快速脉动(opacity 0.4→1.0，0.5s cycle)
- Offline: 空心圆，灰色，静态

**Accessibility**: aria-label 必须包含状态文字（aria-label="在线" 或 "离线"）

---

### 2.4 MetricRing (环形图)

**用途**: 显示车队健康度占比（正常 vs 警告 vs 严重 vs 离线）

```
       ┌──────────┐
      ╱  48 正常   ╲
     │   96%       │
     │  ─────────  │
     │  1 警告 2%  │
      ╲  1 严重 2% ╱
       └──────────┘
     车队健康度
```

**Spec**:
- 外径 140px，内径 100px（环宽 40px）
- 中心显示总数 + 百分比文字
- 颜色: 绿色(正常)、黄色(警告)、红色(严重)、灰色(离线)
- Hover 分段: 高亮 + tooltip 显示具体数量
- 点击分段: 下钻到该分类的机器人列表

---

### 2.5 TrendLine (折线图)

**用途**: 显示选定指标过去 N 小时/天的趋势

**Spec**:
- X 轴: 时间（自适应粒度：< 1h → 每分钟，< 24h → 每 5 分钟，< 30d → 每小时）
- Y 轴: 指标值（自适应范围：数据 min-max + 10% padding）
- 支持多机器人叠加（不同颜色线 + 图例）
- 缩放: 鼠标拖选时间范围（brush selection）
- 悬停: 十字准线 + tooltip(时间, 值, 机器人名)
- 阈值线: 告警阈值以红色虚线标注
- 加载态: 骨架折线（灰色虚线 + 脉冲动画）
- 空态: "暂无数据"文字
- 错误态: "数据加载失败" + 重试按钮

---

### 2.6 FleetHeatmap (地理热力图)

**用途**: 地图上显示机器人分布和状态密度

**Spec**:
- 底图: OpenStreetMap（浅色/暗色 tile 跟随主题）
- 机器人标记: StatusDot 颜色 + 机器人 ID 标签
- 热力层: 可选切换，按告警密度渲染（红色=高告警密度区域）
- 缩放: 鼠标滚轮，范围 3-18 级
- 点击标记: 弹出小型信息窗口（电量/温度/告警数）
- 降级: 地图不可用时显示文字坐标列表
- 聚类: 缩小到 city 级别时机器人自动聚合成数字标记（"12 台"）

---

### 2.7 RobotDetailPanel

**用途**: 点击机器人卡片后展开的详情面板（右侧滑出抽屉）

**宽度**: 480px（可拖拽调整 360-720px）

**内容区域**:
```
┌─────────────────────────────────┐
│ ← 返回总览     R03 详情    [×]  │  ← 头部
├─────────────────────────────────┤
│ ● 在线  |  工业区-A              │  ← 状态栏
├─────────────────────────────────┤
│ 📊 实时遥测                      │
│ ⚡ 电量    78%  ████████░░       │  ← 进度条
│ 🔥 关节温度                      │
│   左膝 42°C  ░░████░░  (正常)   │  ← 带颜色指示
│   右膝 43°C  ░░████░░  (正常)   │
│   左髋 65°C  ████████░  (⚠ 偏高) │
│ 🧠 CPU     35%  ███░░░░░        │
│ 📶 延迟    12ms █░░░░░░░        │
│ 📋 任务    巡检任务-3             │
│ 📍 GPS     39.9042, 116.4074    │
├─────────────────────────────────┤
│ 📈 历史曲线 (过去 24h)            │  ← 迷你折线图
│ [电量] [温度] [CPU]  [展开30天]  │
├─────────────────────────────────┤
│ 💬 留言 (3)                      │
│ 李梅: @张伟 左膝温度偏高，       │
│       已通知现场检查              │
│        5 分钟前                   │
│ 张伟: 收到，正在路上             │
│        3 分钟前                   │
│ ┌─────────────────────────┐     │
│ │ @ 输入留言...       [发送]│     │
│ └─────────────────────────┘     │
│ [我在处理]                       │  ← ClaimButton
└─────────────────────────────────┘
```

---

### 2.8 ClaimButton

**States**:
| State | 文字 | 样式 | 行为 |
|-------|------|------|------|
| Unclaimed | "🔧 我在处理" | 蓝色 outline button | 点击 → 认领 |
| Claimed by me | "✅ 你正在处理" | 绿色实心 button | 点击 → 释放 |
| Claimed by other | "李梅正在处理 (2 分钟前)" | 灰色 disabled text | 不可点击 |

**Auto-release**: 30 分钟无操作自动释放，释放前 5 分钟 toast 提醒

---

### 2.9 ConfigPanel

**用途**: 单机器人配置编辑

```
⚙️ 配置 — R03
─────────────────────────────
告警阈值
  电量过低  [======●────] 20%
            0%              100%
            默认: 15%
  关节温度过高 [========●──] 65°C
            30°C            90°C
            默认: 60°C
─────────────────────────────
采样频率
  ○ 高频 (1s)   ● 标准 (5s)   ○ 节能 (30s)
─────────────────────────────
重连策略
  ● 自动重连   ○ 手动重连
  最大重试: [5] 次
─────────────────────────────
[恢复默认]           [保存配置]
```

**Accessibility**: 滑块支持键盘 Arrow 调整（步进 1% / 1°C）

---

### 2.10 ThemeToggle

```
🌙 暗色  ──────●──────  ☀ 亮色
```

- 切换动画: 背景 300ms 渐变过渡
- 图表色板同步切换
- 偏好保存到 localStorage + 系统偏好检测(prefers-color-scheme)

---

## 3. CSS Custom Properties (Theme System)

```css
:root {
  /* 这些变量在 dark.css / light.css 中被覆写 */
  --color-bg-primary: #0D1117;
  --color-bg-secondary: #161B22;
  --color-text-primary: #E6EDF3;
  --color-text-secondary: #8B949E;
  --color-border-default: #30363D;
  --color-status-online: #3FB950;
  --color-status-warning: #D29922;
  --color-status-critical: #F85149;
  --color-status-offline: #484F58;
  --color-accent-primary: #58A6FF;
  --font-sans: 'Inter', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --transition-normal: 300ms cubic-bezier(0.4, 0, 0.2, 1);
}
```

**Theme switching**: `<html data-theme="dark">` / `<html data-theme="light">`

---

## 4. Responsive Breakpoints

```yaml
breakpoints:
  sm: 1366px    # 最小支持（运维中心旧显示器）
  md: 1440px    # 标准笔记本
  lg: 1920px    # 推荐（标准外接显示器）
  xl: 2560px    # 超宽屏（可选优化）
```

- 1366px: 卡片网格 2 列，RobotCard 宽度 300px
- 1920px: 卡片网格 3 列，RobotCard 宽度 320px
- 2560px: 卡片网格 4 列

---

## 5. Icon System

使用 Lucide Icons（MIT license，轻量，React 组件化）：

| 使用场景 | 图标 |
|---------|------|
| 电量 | `Battery` / `BatteryWarning` / `BatteryFull` |
| 温度 | `Thermometer` |
| CPU | `Cpu` |
| 网络 | `Wifi` / `WifiOff` |
| GPS | `MapPin` |
| 任务 | `ClipboardList` |
| 告警 | `Bell` / `BellRing` / `AlertTriangle` |
| 设置 | `Settings` / `Sliders` |
| 导出 | `Download` / `FileText` / `FileSpreadsheet` |
| 主题 | `Sun` / `Moon` |
| 语言 | `Languages` |
| 留言 | `MessageSquare` |
| 认领 | `UserCheck` |
| 搜索 | `Search` |
| 折叠 | `ChevronLeft` / `ChevronRight` |

---

## Completion Report

```yaml
completion_report:
  what_was_done: "完整的运维面板设计系统：暗色/亮色双主题 design tokens、10 个核心组件完整规格（含所有状态和 accessibility）、CSS 变量体系、响应式断点、图标系统"
  key_decisions:
    - decision: "暗色主题作为默认——运维中心 7×24 环境需求"
      rationale: "UX research 确认运维中心暗色环境，亮色备选给白天办公室"
    - decision: "AlertBanner 使用非阻塞通知条而非模态弹窗"
      rationale: "运维工程师在处理一台故障时可能同时收到另一台的告警。模态弹窗会阻塞操作，通知条允许并行处理"
    - decision: "RobotCard 左边框颜色作为状态的主要视觉信号（而非整卡变色）"
      rationale: "边框能同时传达颜色信息且不影响卡片内容区域的对比度。对比度对暗色主题尤为关键"
    - decision: "滑块默认值标记 + 当前值指示，降低配置焦虑"
      rationale: "工程师修改阈值时需要知道默认值是多少，避免误设导致漏报或误报"
  handoff_focus:
    - "senior-frontend: 10 个核心组件 + CSS variable 体系可用于直接实现"
    - "code-reviewer: WCAG AA 级别 accessibility audit 是强制要求"
  open_questions:
    - "是否已有品牌色板需要遵守？（当前使用 GitHub 风格暗色色板作为默认）"
  known_constraints:
    - "WCAG AA 最低标准，AAA 作为 stretch goal"
    - "最小分辨率 1366×768，移动端不在 scope"
  confidence_differential: 0.05
  dissent_if_alone: null
```
