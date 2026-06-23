# 前端实现方案 — 机器人车队运维监控面板

> 角色: senior-frontend | 来源: 架构 ADR + 设计系统 Spec | 版本: v1.0

---

## 1. 项目结构 (Feature-based)

```
fleetops-dashboard/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts             # 集成 design tokens
├── public/
│   └── locales/
│       ├── zh/translation.json
│       └── en/translation.json
└── src/
    ├── main.tsx                    # app entry
    ├── App.tsx                     # router + layout shell
    │
    ├── features/
    │   ├── dashboard/              # 总览仪表盘
    │   │   ├── DashboardPage.tsx
    │   │   ├── FleetGrid.tsx       # 机器人卡片网格（虚拟化）
    │   │   ├── FleetSummary.tsx    # 顶部统计条
    │   │   ├── RingChart.tsx       # 环形图
    │   │   ├── TrendLine.tsx       # 折线图
    │   │   └── FleetHeatmap.tsx    # 热力图
    │   │
    │   ├── robot-detail/           # 机器人详情
    │   │   ├── RobotDetailDrawer.tsx
    │   │   ├── TelemetryPanel.tsx
    │   │   ├── JointTempList.tsx
    │   │   └── MiniHistoryChart.tsx
    │   │
    │   ├── alerts/                 # 告警中心
    │   │   ├── AlertsPage.tsx
    │   │   ├── AlertBanner.tsx     # 顶部通知条
    │   │   ├── AlertList.tsx       # 告警历史列表
    │   │   └── AlertFilter.tsx
    │   │
    │   ├── history/                # 历史曲线
    │   │   ├── HistoryPage.tsx
    │   │   ├── HistoryChart.tsx    # 30天全功能曲线
    │   │   └── MetricSelector.tsx
    │   │
    │   ├── config/                 # 配置管理
    │   │   ├── ConfigPage.tsx
    │   │   ├── ConfigPanel.tsx     # 单机器人配置
    │   │   ├── ThresholdSlider.tsx
    │   │   └── BatchConfig.tsx     # 批量配置
    │   │
    │   ├── collaboration/          # 协作
    │   │   ├── CommentThread.tsx
    │   │   ├── CommentInput.tsx    # @mention 自动补全
    │   │   └── ClaimButton.tsx
    │   │
    │   ├── export/                 # 报表导出
    │   │   ├── ExportDialog.tsx
    │   │   └── ExportProgress.tsx
    │   │
    │   └── layout/                 # 布局系统
    │       ├── AppShell.tsx        # 全局布局容器
    │       ├── Sidebar.tsx
    │       ├── TopNav.tsx
    │       └── DragGrid.tsx        # 可拖拽网格容器
    │
    ├── shared/
    │   ├── components/             # 共享 UI 组件
    │   │   ├── RobotCard.tsx
    │   │   ├── StatusDot.tsx
    │   │   ├── AlertBadge.tsx
    │   │   ├── MetricRing.tsx      # 通用环形图封装
    │   │   ├── LoadingSkeleton.tsx
    │   │   ├── EmptyState.tsx
    │   │   └── ErrorBoundary.tsx
    │   │
    │   ├── hooks/                  # 共享 hooks
    │   │   ├── useWebSocket.ts     # WebSocket 连接管理
    │   │   ├── useTelemetry.ts     # 遥测数据订阅
    │   │   ├── useAlerts.ts        # 告警订阅
    │   │   ├── useRobotDetail.ts   # 机器人详情查询 (REST)
    │   │   ├── useHistory.ts       # 历史数据查询
    │   │   └── useTheme.ts         # 主题管理
    │   │
    │   ├── stores/                 # Zustand stores
    │   │   ├── fleetStore.ts
    │   │   ├── alertStore.ts
    │   │   ├── uiStore.ts          # 主题/语言/布局
    │   │   └── collaborationStore.ts
    │   │
    │   ├── types/                  # TypeScript 类型
    │   │   ├── telemetry.ts        # RobotTelemetry
    │   │   ├── alert.ts            # Alert
    │   │   ├── robot.ts            # Robot 元数据
    │   │   └── config.ts           # RobotConfig
    │   │
    │   ├── utils/
    │   │   ├── format.ts           # 数字/日期/单位格式化
    │   │   ├── chartTheme.ts       # ECharts 暗色/亮色主题
    │   │   └── constants.ts
    │   │
    │   └── i18n/
    │       └── i18n.ts             # i18next 配置
    │
    └── styles/
        ├── index.css               # @tailwind + CSS variables
        ├── tokens.css              # 设计 token (CSS 变量)
        ├── theme-dark.css
        └── theme-light.css
```

---

## 2. State Management — Zustand Stores

### 2.1 fleetStore

```typescript
interface FleetState {
  robots: Map<string, RobotTelemetry>;    // robot_id → 最新遥测
  robotMeta: Map<string, RobotMeta>;      // robot_id → 元数据
  onlineCount: number;
  warningCount: number;
  criticalCount: number;
  offlineCount: number;
  
  // Actions
  upsertTelemetry: (data: RobotTelemetry) => void;
  markOffline: (robotId: string) => void;
  getRobot: (robotId: string) => RobotTelemetry | undefined;
  getFilteredRobots: (filter: FleetFilter) => RobotTelemetry[];
}

// 性能优化: 使用 Map 而非对象，50 台机器人每秒更新时 O(1) 查找
// 派生状态用 computed selector，避免不必要的重渲染
```

### 2.2 alertStore

```typescript
interface AlertState {
  activeAlerts: Alert[];           // 当前活跃告警
  alertHistory: Alert[];           // 历史告警（分页加载）
  unreadCount: number;
  
  // Actions
  addAlert: (alert: Alert) => void;
  acknowledgeAlert: (alertId: string, note: string) => void;
  resolveAlert: (alertId: string) => void;
  dismissBanner: (alertId: string, duration: number) => void;
}

// 告警去重已在后端处理，前端不需要额外逻辑
// activeAlerts 按 severity + timestamp 排序
```

### 2.3 uiStore

```typescript
interface UIState {
  theme: 'dark' | 'light';
  language: 'zh' | 'en';
  sidebarCollapsed: boolean;
  layout: LayoutConfig[];           // 可拖拽卡片的位置/大小
  
  // Actions
  toggleTheme: () => void;
  setLanguage: (lang: string) => void;
  updateLayout: (config: LayoutConfig[]) => void;
  resetLayout: () => void;
}

// persist middleware → localStorage
// theme 初始化时检查 localStorage → prefers-color-scheme → dark (fallback)
```

---

## 3. Data Flow

### 3.1 WebSocket → Store → Component

```
WebSocket (single connection)
    │
    ├── type: "telemetry"
    │   └── useTelemetry hook
    │       ├── fleetStore.upsertTelemetry(data)
    │       │   ├── RobotCard re-render (仅该 robot_id)
    │       │   ├── FleetSummary re-render (counts)
    │       │   └── RingChart re-render (percentages)
    │       └── (if detail panel open → RobotDetailDrawer updates)
    │
    ├── type: "alert"
    │   └── useAlerts hook
    │       ├── alertStore.addAlert(data)
    │       │   ├── AlertBanner triggers
    │       │   ├── NotificationBell badge++
    │       │   └── RobotCard alert badge updates
    │       └── (if severity === CRITICAL → play sound)
    │
    └── type: "heartbeat"
        └── fleetStore.markOnline(robotId) // 确认连接存活
```

### 3.2 REST → Component (non-real-time data)

```
REST API (fetch)
    │
    ├── GET /api/robots/:id/telemetry/history  → useHistory hook → HistoryChart
    ├── GET /api/robots/:id/comments           → collaborationStore → CommentThread
    ├── POST /api/robots/:id/comments          → collaborationStore.addComment()
    ├── GET /api/robots/:id/config             → ConfigPanel (local form state)
    ├── PUT /api/robots/:id/config             → ConfigPanel → toast success
    └── POST /api/export                       → ExportDialog → ExportProgress (poll)
```

---

## 4. WebSocket Hook Implementation

```typescript
// src/shared/hooks/useWebSocket.ts

function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number>();
  const retryCountRef = useRef(0);
  const listenersRef = useRef<Map<string, Set<(data: any) => void>>>();
  
  const connect = useCallback(() => {
    const token = getAuthToken();
    const ws = new WebSocket(`wss://${HOST}/ws?token=${token}`);
    
    ws.onopen = () => {
      retryCountRef.current = 0;
      uiStore.setConnectionStatus('connected');
    };
    
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      const listeners = listenersRef.current.get(msg.type);
      listeners?.forEach(fn => fn(msg.payload));
    };
    
    ws.onclose = () => {
      uiStore.setConnectionStatus('disconnected');
      scheduleReconnect();
    };
    
    wsRef.current = ws;
  }, []);
  
  const scheduleReconnect = () => {
    const delay = Math.min(1000 * 2 ** retryCountRef.current, 30000);
    retryCountRef.current++;
    reconnectTimeoutRef.current = setTimeout(connect, delay);
  };
  
  const subscribe = (type: string, callback: (data: any) => void) => {
    // add to listenersRef, return unsubscribe fn
  };
  
  return { subscribe, connectionStatus };
}
```

**关键设计决策**:
- **单一 WebSocket 连接**: 所有实时数据（遥测 + 告警 + 心跳 + 协作通知）走同一个连接，通过 `msg.type` 分发
- **指数退避重连**: 1s → 2s → 4s → 8s → ... → max 30s
- **重连时恢复状态**: 重连成功后，前端请求最近 5 分钟的遥测数据补推（`GET /api/telemetry/since?t=...`）

---

## 5. 性能优化策略

### 5.1 机器人卡片网格虚拟化

50 张卡片同时渲染 → 使用 `react-window` 的 `FixedSizeGrid`：
```typescript
// 仅在视口内的卡片渲染真实 DOM
// 视口外的卡片展示占位骨架
// 每行 3 张卡片 × 可见 5 行 = 15 张卡片同时渲染（而非 50 张）
```

### 5.2 Zustand 选择器优化

```typescript
// ❌ 整个 store 变化触发所有消费者重渲染
const fleet = useFleetStore();

// ✅ 只订阅需要的字段
const robot = useFleetStore(state => state.robots.get(robotId));
const onlineCount = useFleetStore(state => state.onlineCount);

// 使用 shallow comparison 避免不必要渲染
const counts = useFleetStore(
  state => ({ online: state.onlineCount, warning: state.warningCount }),
  shallow
);
```

### 5.3 ECharts 按需引入

```typescript
// 只引入使用的图表类型，而非整个 echarts
import * as echarts from 'echarts/core';
import { PieChart, LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([PieChart, LineChart, GridComponent, TooltipComponent, CanvasRenderer]);
```

### 5.4 批量更新 WebSocket 消息

WebSocket 每秒推送 50 条消息 → 使用 `requestAnimationFrame` 批量更新：
```typescript
let pendingUpdates: RobotTelemetry[] = [];

ws.onmessage = (event) => {
  pendingUpdates.push(JSON.parse(event.data));
  if (pendingUpdates.length === 1) {
    requestAnimationFrame(() => {
      fleetStore.batchUpsert(pendingUpdates);
      pendingUpdates = [];
    });
  }
};
```

---

## 6. 路由设计

```
/                          → DashboardPage (总览仪表盘)
/alerts                    → AlertsPage (告警中心)
/robots/:id                → RobotDetailDrawer (叠加在任意页面之上)
/history/:id               → HistoryPage (全功能历史曲线)
/config                    → ConfigPage (配置管理)
/config/:id                → ConfigPanel (单机器人配置)
```

- 机器人详情使用 Drawer 而非独立页面 — 用户可以在查看详情的同时保持总览可见
- 所有路由保持 Sidebar 高亮同步

---

## 7. 关键交互实现

### 7.1 告警声音管理
```typescript
// 使用 Web Audio API，不依赖 <audio> 元素
const alertSound = useCallback(() => {
  const ctx = new AudioContext();
  const osc = ctx.createOscillator();
  osc.frequency.value = 800;
  osc.connect(ctx.destination);
  osc.start();
  osc.stop(ctx.currentTime + 0.2); // 200ms beep
}, []);
```

### 7.2 @mention 自动补全
```typescript
// CommentInput 中检测 @ 字符 → 显示同事列表下拉
// 使用 Tribute.js 或自行实现简单的 popover
// 回车选中 → 插入 <span data-mention="user_id">@张三</span>
```

### 7.3 拖拽布局持久化
```typescript
// react-grid-layout 的 onLayoutChange → uiStore.updateLayout(layout)
// uiStore 的 persist middleware → localStorage
// 页面加载时 → uiStore.layout → react-grid-layout 的 layout prop
```

---

## 8. 测试计划

| 范围 | 工具 | 重点场景 |
|------|------|---------|
| 单元测试 | Vitest | fleetStore 的 upsertTelemetry 逻辑、alertStore 去重逻辑 |
| 组件测试 | React Testing Library | RobotCard 各状态渲染、AlertBanner 弹出/消除、ClaimButton 状态切换 |
| Hook 测试 | @testing-library/react-hooks | useWebSocket 重连逻辑、useTelemetry 订阅/取消订阅 |
| E2E | Playwright | 告警发现→详情→认领→处理 完整旅程、主题切换图表色板同步 |

---

## Completion Report

```yaml
completion_report:
  what_was_done: "前端实现方案：feature-based 目录结构、4 个 Zustand store 设计、WebSocket → Store → Component 数据流、useWebSocket hook 实现细节、性能优化策略（虚拟化/选择器/ECharts tree-shaking/批量更新）、路由设计、关键交互实现方案、测试计划"
  key_decisions:
    - decision: "单一 WebSocket 连接承载所有实时数据（遥测+告警+心跳），通过 msg.type 分发"
      rationale: "浏览器对同域 WebSocket 连接数通常限制 6 个，单连接避免连接竞争。消息分发模式允许不同 feature 独立订阅各自的数据类型"
    - decision: "使用 react-window 虚拟化机器人卡片网格"
      rationale: "50 张卡片全部渲染 DOM 节点 > 200 个。虚拟化将同时渲染数降到 ~15 张，性能差异在低端机器上可达 10 倍"
    - decision: "机器人详情用 Drawer 而非独立页面"
      rationale: "运维场景需要同时看到总览和详情。Drawer 允许工程师在处理一台机器人时依然看到车队的全局告警变化"
    - decision: "requestAnimationFrame 批量更新 WebSocket 消息"
      rationale: "50 台机器人每秒各推送 1 条 → 50 次独立的 Zustand 更新 = 50 次 React re-render。批量合并为每帧 1 次更新 = 60fps 下 1 次 re-render"
  handoff_focus:
    - "code-reviewer: useWebSocket hook 重连逻辑和 fleetStore 批量更新是审查重点"
    - "tdd: fleetStore 和 alertStore 是测试起点"
  open_questions:
    - "ECharts 在暗色主题下的色板需与设计 token 同步，是否已有 Figma/设计稿色板可导出？"
  known_constraints:
    - "SPA 无 SSR，Vite 构建"
    - "最小支持 1366×768，移动端不在 scope"
    - "WCAG AA 最低标准"
  confidence_differential: 0.0
  dissent_if_alone: null
```
