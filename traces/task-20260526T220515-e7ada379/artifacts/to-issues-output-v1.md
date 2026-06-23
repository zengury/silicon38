# Issue Breakdown: FleetOps Dashboard

## Parent PRD: Robot fleet monitoring dashboard — architecture, UI design, and demo

---

## Proposed Vertical Slices

### 1. Canonical Data Model + Adapter Pipeline (AFK)
**Type:** AFK
**Blocked by:** None — can start immediately
**User stories covered:** #6 (异构数据适配)

**What to build:**
Define the Canonical RobotSnapshot model in TypeScript, implement the Adapter interface, and build 3 sample adapters (JSON v1, JSON v2, Protobuf v1) that parse raw messages into the canonical form. Include a unit conversion layer (F→C, imperial→metric). The Adapter Registry maps robotId → adapter protocol.

**Acceptance criteria:**
- [ ] `RobotSnapshot` type defined with all fields from PRD
- [ ] `DataAdapter` interface with `parse()` and `normalize()` methods
- [ ] JSON v1 adapter correctly maps `batLevel` → `battery.percent`
- [ ] Protobuf adapter correctly decodes binary → canonical
- [ ] Unit conversion: Fahrenheit → Celsius, inches → meters
- [ ] Adapter Registry: `getAdapter(robotId)` returns correct adapter
- [ ] All adapters pass with 3 fixture datasets each

---

### 2. Mock Data Generator + WebSocket Server (AFK)
**Type:** AFK
**Blocked by:** #1 (Canonical Model)
**User stories covered:** #1, #4 (实时数据流基础)

**What to build:**
Build a WebSocket server (Node.js or Bun) that simulates 20 robots. Each robot emits a `RobotSnapshot` at configurable frequency. The mock generator creates realistic data patterns: battery drains over time, temperature correlates with task activity, occasional spike anomalies. The server accepts client connections and pushes updates.

**Acceptance criteria:**
- [ ] WebSocket server starts on configurable port
- [ ] 20 robots simulated with distinct IDs and behavior profiles
- [ ] Each robot emits at 1Hz (configurable per robot)
- [ ] Battery simulation: drains ~1%/min during tasks, ~0.1%/min idle
- [ ] Temperature simulation: correlates with CPU load and motor activity
- [ ] Random fault injection: 5% chance of joint offline, 2% chance of fall event per hour
- [ ] Client can connect and receive JSON-framed messages
- [ ] Latency simulation: 20-200ms per robot with packet loss

---

### 3. Realtime Engine + State Store (AFK)
**Type:** AFK
**Blocked by:** #1 (Canonical Model), #2 (WebSocket Server)
**User stories covered:** #1 (实时数据)

**What to build:**
Frontend real-time engine: WebSocket client with auto-reconnect, heartbeat, and backoff. Maintains an in-memory state store (Zustand) of all robot snapshots keyed by robotId. Exposes React hooks: `useRobot(robotId)`, `useFleet()`, `useRobotHistory(robotId, metric)`.

**Acceptance criteria:**
- [ ] WebSocket connection with exponential backoff reconnection
- [ ] Heartbeat ping/pong every 15s, disconnect detected at 30s timeout
- [ ] `useRobot(robotId)` returns latest snapshot for one robot
- [ ] `useFleet()` returns all robot snapshots as Map<robotId, RobotSnapshot>
- [ ] State store updates at received frequency without unnecessary re-renders
- [ ] Connection status indicator (connected / reconnecting / disconnected)
- [ ] Graceful degradation when WebSocket unavailable

---

### 4. Total Overview Dashboard (AFK)
**Type:** AFK
**Blocked by:** #3 (Realtime Engine)
**User stories covered:** #1, #2, #3, #4

**What to build:**
The main dashboard page with:
- Top bar: fleet-level stats (online count, avg battery, active alerts)
- Donut chart: robot status distribution (online/offline/warning/critical/maintenance)
- Line chart: fleet-average CPU and latency over time (last 5 min rolling window)
- Heatmap: joint temperature by robot × joint, using ECharts heatmap
- Robot grid/list: card for each robot showing avatar, name, battery bar, status badge, current task

**Acceptance criteria:**
- [ ] Donut chart updates in real-time as robot statuses change
- [ ] Line chart shows rolling 5-minute window of fleet averages
- [ ] Heatmap cells color-code temperature (green→yellow→red: 30→50→65°C)
- [ ] Robot grid shows all 20 robots with battery indicator and status
- [ ] Clicking a robot card navigates to detail view
- [ ] All charts use ECharts with dark/light theme support
- [ ] Dashboard renders at 60fps with 20 robots at 1Hz updates

---

### 5. Robot Detail View + 30-Day History (AFK)
**Type:** AFK
**Blocked by:** #3 (Realtime Engine)
**User stories covered:** #5 (历史曲线), #1 (单台实时数据)

**What to build:**
Robot detail page showing:
- Real-time gauge cluster: battery %, CPU %, network latency, temperature max
- Joint status table: each joint with temperature bar and status indicator
- 30-day history chart: selectable metric (battery/temp/cpu/latency), time range picker
- Current task display with progress
- Geographic location on embedded map (Leaflet, with marker + heading arrow)
- Timeline of recent alerts for this robot

**Acceptance criteria:**
- [ ] Gauges update in real-time (5Hz)
- [ ] Joint table shows all joints with color-coded temperature
- [ ] History chart loads and displays 30 days of mock data
- [ ] Time range selector: 1h / 24h / 7d / 30d
- [ ] Map shows robot marker with heading direction indicator
- [ ] Alert timeline lists last 50 events for this robot
- [ ] Back navigation to fleet overview

---

### 6. Alert Engine + Notification System (AFK)
**Type:** AFK
**Blocked by:** #3 (Realtime Engine), #1 (Canonical Model)
**User stories covered:** #4 (异常告警), #13 (告警时间线)

**What to build:**
Alert engine evaluates each incoming snapshot against configurable rules:
- `battery.percent < threshold` → low battery alert
- `joints.*.status == 'offline'` → joint offline alert
- `robot status == 'fallen'` → fall alert
Alerts go through state machine: pending → active → acknowledged → resolved.
UI: alert badge with count in top bar, alert panel with sound notification, alert timeline view.

**Acceptance criteria:**
- [ ] Alert engine processes each snapshot and emits Alert objects
- [ ] Cooldown prevents duplicate alerts within configurable window (default 5 min)
- [ ] Alert state machine: pending→active→acknowledged→resolved
- [ ] Alert badge in header shows active count with pulse animation
- [ ] Alert panel opens with list of active alerts
- [ ] Sound notification on new critical alert (mutable)
- [ ] Clicking alert navigates to affected robot
- [ ] Alert timeline viewable per robot and fleet-wide

---

### 7. Configuration Panel (AFK)
**Type:** AFK
**Blocked by:** #6 (Alert Engine — shares rule config)
**User stories covered:** #6 (调整告警阈值), #7 (采样频率), #8 (重连策略)

**What to build:**
Configuration panel with per-robot settings:
- Alert thresholds: battery low %, temperature high °C, latency high ms, packet loss %
- Sampling frequency: data push interval (0.2Hz - 10Hz)
- Reconnection strategy: max retries, initial backoff, max backoff, reset timeout
UI: robot selector dropdown → tabbed config form with sliders and number inputs → save button with confirmation.

**Acceptance criteria:**
- [ ] Robot selector filters to specific robot
- [ ] Alert threshold sliders with current value display
- [ ] Sampling frequency dropdown (0.2, 0.5, 1, 2, 5, 10 Hz)
- [ ] Reconnection params: maxRetries (0-20), backoffInitial (1-60s), backoffMax (30-600s)
- [ ] Save persists config (localStorage for demo, API for production)
- [ ] Unsaved changes warning on navigation
- [ ] "Reset to defaults" button per section

---

### 8. Collaboration: Comments + @Mentions (AFK)
**Type:** AFK
**Blocked by:** #5 (Robot Detail View — comments displayed there)
**User stories covered:** #8 (留言、@同事、标记"我在处理")

**What to build:**
Comment thread on robot detail page:
- Text input with @mention autocomplete (from mock user list)
- Comments display with author, timestamp, mentions highlighted
- "I'm handling this" toggle button: sets claimStatus on latest comment
- Mentions trigger a visual indicator (badge on robot card, notification toast)
- Simple mock user list (5 fake engineers)

**Acceptance criteria:**
- [ ] Comment input with @ autocomplete from user list
- [ ] Comments render in chronological thread
- [ ] @mentions highlighted and linked
- [ ] "I'm handling this" button toggles claimStatus
- [ ] Claimed robots show handler name on robot card
- [ ] Mention notifications appear as toasts
- [ ] Comments persist in localStorage

---

### 9. Export: PDF + Excel (AFK)
**Type:** AFK
**Blocked by:** #4 (Dashboard) or #5 (Detail View)
**User stories covered:** #12 (导出报表)

**What to build:**
Export functionality:
- PDF: "Export Dashboard" button captures current view via `window.print()` with `@media print` CSS optimization for charts
- Excel: "Export Data" button generates .xlsx with raw timeline data using exceljs
- Configurable export scope: current robot / entire fleet / selected robots
- Date range picker for historical data export

**Acceptance criteria:**
- [ ] PDF export renders dashboard charts correctly on A4
- [ ] Excel export contains sheets: Summary, Battery History, Temperature History, Alerts
- [ ] Export scope selector: current view, selected robots, all robots
- [ ] Date range picker defaults to last 7 days
- [ ] Download triggers browser download dialog
- [ ] Export progress indicator for large datasets

---

### 10. Theming, i18n & Customizable Layout (AFK)
**Type:** AFK
**Blocked by:** #4 (Dashboard — layout applied here)
**User stories covered:** #9 (暗色/亮色主题), #11 (多语言), #10 (可拖拽布局)

**What to build:**
- Dark/light theme toggle with system preference detection
- CSS variables for all theme colors, ECharts theme integration
- i18n with react-i18next: zh-CN and en-US namespaces
- Drag-and-drop dashboard layout with react-grid-layout
- Layout persistence in localStorage per user
- "Reset layout" and "Lock layout" controls

**Acceptance criteria:**
- [ ] Theme toggle in header, respects `prefers-color-scheme`
- [ ] All components respond to theme change without reload
- [ ] ECharts instances re-theme on toggle
- [ ] Language switcher: 中文 / English, persisted in localStorage
- [ ] All UI text uses i18n keys, no hardcoded strings
- [ ] Dashboard widgets can be dragged to reorder
- [ ] Widget size adjustable via drag handles
- [ ] Layout saved per user, restored on reload
- [ ] Lock layout toggle disables dragging

---

## Dependency Graph

```
#1 Canonical Model ─────┬────► #3 Realtime Engine ──┬──► #4 Overview Dashboard
                        │                          │
#2 Mock WS Server ──────┘                          ├──► #5 Robot Detail + History
                                                   │
                                                   ├──► #6 Alert Engine ──► #7 Config Panel
                                                   │
                                                   └──► (data layer complete)
                                                         │
                              #8 Collaboration ◄────────┤
                              #9 Export ◄────────────────┤
                              #10 Theme/i18n/Layout ◄────┘
```

---

## Completion Report

```yaml
completion_report:
  what_was_done: "将 FleetOps Dashboard PRD 拆解为 10 个独立可交付的垂直切片，每片包含验收标准和依赖关系"
  key_decisions:
    - decision: "将 Canonical Model 和 Adapter Pipeline 作为第一个独立切片"
      rationale: "这是整个系统的数据基础，所有其他切片都依赖统一数据模型。必须先稳定接口"
    - decision: "Mock WebSocket Server 独立于 Realtime Engine 作为 #2"
      rationale: "数据生成和数据消费是两个独立关注点，分离后前端团队可并行开发"
    - decision: "Theme/i18n/Layout 作为收尾切片 #10"
      rationale: "这些横切关注点应在核心功能完成后统一应用，避免重复工作"
    - decision: "所有切片标记为 AFK，不设 HITL"
      rationale: "PRD 已充分明确需求，所有切片都有可验证的验收标准，无需人工交互决策点"
  handoff_focus:
    - "#1 Canonical Model 是阻塞性基础切片，必须首先完成"
    - "#2 Mock Server 和 #3 Realtime Engine 可在 #1 完成后并行"
    - "#4 Dashboard 和 #5 Detail View 可在 #3 完成后并行"
    - "#8 Collaboration 和 #9 Export 是独立功能，可与前端切片并行"
  open_questions:
    - "后端聚合服务是否由本团队构建，还是已有现成服务？这决定 Mock Server 是临时方案还是需要对接真实后端"
  known_constraints:
    - "Demo 阶段使用 localStorage 存储评论和配置，生产环境需替换为持久化后端"
    - "30 天历史数据在 demo 中用前端内存模拟，生产需要时序数据库"
  confidence_differential: 0.90
  dissent_if_alone: null
  iteration_context: null
```
