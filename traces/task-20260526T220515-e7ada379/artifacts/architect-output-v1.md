# Architecture Decision Record: FleetOps Dashboard

## ADR-001: System Architecture — Modular SPA with Backend Aggregation Service

**Status:** Proposed
**Date:** 2026-05-26

### Context

运维工程师需要监控 20-100 台异构人形机器人（不同厂商、不同数据协议）。系统需要实时展示、异常告警、历史查询、团队协作、报表导出、主题切换和可拖拽布局。Demo 阶段需要能在浏览器中展示完整功能。

### Decision

采用 **Modular SPA + Backend Aggregation Service** 架构：

```
┌─────────────────────────────────────────────────────────────────┐
│                        浏览器 (SPA)                              │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────────┐  │
│  │Dashboard │ │ Detail   │ │ Alert    │ │ Config / Collab /  │  │
│  │Overview  │ │ View     │ │ Panel    │ │ Export / Theme     │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬──────────┘  │
│       │             │            │                 │             │
│       └─────────────┴────────────┴─────────────────┘             │
│                          │                                       │
│                   ┌──────┴──────┐                                │
│                   │ State Store │  (Zustand + TanStack Query)    │
│                   └──────┬──────┘                                │
│                          │                                       │
│                   ┌──────┴──────┐                                │
│                   │ WebSocket   │  (single connection)           │
│                   │ Client      │                                │
│                   └──────┬──────┘                                │
└──────────────────────────┼──────────────────────────────────────┘
                           │ wss://
┌──────────────────────────┼──────────────────────────────────────┐
│                   ┌──────┴──────┐                                │
│                   │ WebSocket   │                                │
│                   │ Server      │  (Node.js / Bun)               │
│                   └──────┬──────┘                                │
│                          │                                       │
│     ┌────────────────────┼────────────────────┐                 │
│     │                    │                    │                 │
│  ┌──┴────────┐  ┌────────┴──────┐  ┌─────────┴──────┐          │
│  │ Adapter   │  │ Alert Engine  │  │ History Store  │          │
│  │ Pipeline  │  │ (Rule Eval)   │  │ (In-Memory)    │          │
│  └─────┬─────┘  └───────────────┘  └────────────────┘          │
│        │                                                        │
│  ┌─────┴─────┐  ┌──────────┐  ┌──────────────┐                 │
│  │ JSON v1   │  │ JSON v2  │  │ Protobuf v1  │  ...            │
│  │ Adapter   │  │ Adapter  │  │ Adapter      │                 │
│  └───────────┘  └──────────┘  └──────────────┘                 │
│                                                                  │
│                 Backend Aggregation Service                      │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Robot Fleet (20-100)  │
              │   JSON / Protobuf / ... │
              └─────────────────────────┘
```

### Rationale

1. **SPA 适合仪表盘场景**：大量图表、频繁状态更新，SPA 避免页面刷新。不需要 SSR。
2. **Backend Aggregation Service 作为数据归一化层**：处理异构数据协议，对前端暴露统一的 Canonical Model。前端不需要知道每种协议细节。
3. **单一 WebSocket 连接**：相比多连接或轮询，单连接减少资源消耗，消息通过 `robotId` field 路由到对应组件。
4. **模块化 SPA 内部**：Dashboard、Detail、Alert、Config 等模块独立，通过共享 State Store 通信，不直接耦合。
5. **Demo 阶段简化**：Backend Service 用 Node.js/Bun 进程实现，内置 Mock 数据生成器和内存存储。生产可替换为 Go/Rust 高性能服务 + 时序数据库。

### Alternatives Rejected

| Alternative | Reason Rejected |
|-------------|-----------------|
| SSR (Next.js) | 仪表盘以实时数据为主，SEO 无价值，SSR 增加复杂度 |
| 前端直接连接每台机器人 | 安全风险（暴露机器人 IP）、浏览器连接数限制、协议适配在前端导致 bundle 膨胀 |
| REST 轮询 | 1Hz 更新频率 × 20 机器人 = 20 req/s，WebSocket 推送效率更高 |
| Micro-Frontend (Module Federation) | 团队规模小（初期 1 个前端团队），不需要独立部署，增加运维负担 |
| 后端用 Go/Rust 从 Day 1 | Demo 阶段追求迭代速度，Node.js/Bun 生态更丰富，后期可替换 |

### Consequences

- **正向**：清晰的数据流方向（Robot → Adapter → Canonical → State Store → UI），每层职责单一
- **正向**：Adapter Pipeline 可独立测试，添加新协议只需实现 Adapter 接口
- **负向**：Backend Service 是单点，生产需要冗余部署。初期可接受
- **负向**：WebSocket 重连期间没有数据，需要客户端缓存最后已知状态

---

## ADR-002: Canonical Data Model Design

**Status:** Proposed
**Date:** 2026-05-26

### Context

不同机器人厂商回传的数据格式、字段名、单位均不一致。需要定义一个统一的 Canonical Model 作为系统内部唯一数据表示。

### Decision

定义 `RobotSnapshot` 作为核心数据模型，所有 Adapter 将原始数据映射到此模型：

```typescript
// === Canonical Robot Data Model ===

interface RobotSnapshot {
  // Identity
  robotId: string;            // unique identifier, e.g. "G1-042"
  timestamp: number;          // Unix ms, UTC

  // Battery
  battery: {
    percent: number;          // 0.0 - 100.0
    voltage: number;          // volts (V)
    current: number;          // amperes (A)
    estimatedRemaining: number; // seconds
    temperature: number;      // celsius
  };

  // Joints (keyed by joint name)
  joints: Record<string, JointState>;

  // Compute
  cpu: {
    usagePercent: number;     // 0.0 - 100.0
    temperature: number;      // celsius
    memoryUsedMB: number;
    memoryTotalMB: number;
  };

  // Network
  network: {
    latencyMs: number;        // round-trip to aggregation service
    signalStrength: number;   // dBm (typically -30 to -90)
    packetLoss: number;       // 0.0 - 1.0
    bandwidthKbps: number;
  };

  // Current Task
  task: {
    id: string | null;
    name: string | null;
    type: 'idle' | 'patrol' | 'transport' | 'charge' | 'maintenance' | 'custom';
    progress: number | null;  // 0.0 - 100.0
  };

  // Geolocation
  location: {
    lat: number;              // WGS84 decimal degrees
    lng: number;
    altitude: number;         // meters above sea level
    heading: number;          // degrees (0 = North, clockwise)
    speed: number;            // m/s
    accuracy: number;         // meters (GPS accuracy radius)
  };

  // Derived Status
  status: RobotStatus;

  // Meta
  rawFormat: string;          // original protocol identifier, e.g. "json_v1"
  sequenceNumber: number;     // monotonic counter per robot
}

interface JointState {
  temperature: number;        // celsius
  position: number;           // radians or degrees (normalized to radians)
  velocity: number;           // rad/s
  torque: number;             // N·m
  current: number;            // amperes
  status: 'ok' | 'warning' | 'critical' | 'offline';
}

type RobotStatus = 'online' | 'offline' | 'warning' | 'critical' | 'maintenance';
```

### Unit Normalization Rules

所有 Adapter 必须将输入单位转换为以下标准单位：

| Dimension | Canonical Unit | Common Input → Conversion |
|-----------|---------------|--------------------------|
| Temperature | Celsius (°C) | °F → (°F - 32) × 5/9 |
| Battery % | 0-100 | 0-1 ratio → × 100 |
| Voltage | Volts (V) | mV → ÷ 1000 |
| Position | Radians | Degrees → × π/180 |
| Speed | m/s | km/h → ÷ 3.6 |
| Distance | meters | feet → × 0.3048, inches → × 0.0254 |
| Lat/Lng | Decimal degrees | DMS → decimal conversion |

### Rationale

1. **Canonical Model 是系统的"通用语言"**：UI 组件、告警引擎、历史存储都基于此模型，不需要各自处理格式差异
2. **扁平结构优于深层嵌套**：方便 ECharts 直接消费，减少数据转换
3. **包含 derived status**：原始数据可能来自不同字段（如 `is_fallen` flag 或 `imu.orientation` 异常），Adapter 统一映射为 status enum
4. **sequenceNumber** 用于检测丢包和乱序

### Alternatives Rejected

| Alternative | Reason Rejected |
|-------------|-----------------|
| Schema-on-read (存原始数据，查询时转换) | 每次查询都需转换，历史查询性能差 |
| GraphQL 动态 Schema | 过度设计，机器人数据字段有限且稳定 |
| 每种数据源独立 UI 组件 | 代码重复，维护成本高 |

---

## ADR-003: Adapter Pipeline Architecture

**Status:** Proposed
**Date:** 2026-05-26

### Decision

Adapter 采用 Pipeline 模式，分三个阶段：

```
Raw Message → [1. Protocol Parser] → [2. Field Mapper] → [3. Unit Normalizer] → Canonical Snapshot
```

```typescript
interface DataAdapter {
  /** Protocol identifier (e.g. "json_v1", "protobuf_g1") */
  readonly protocol: string;

  /** Stage 1: Parse raw bytes/string into a semi-structured object */
  parse(raw: Uint8Array | string): Record<string, unknown>;

  /** Stage 2: Map vendor-specific fields to canonical field paths */
  mapFields(parsed: Record<string, unknown>): Partial<CanonicalFields>;

  /** Stage 3: Normalize units to canonical units */
  normalizeUnits(mapped: Partial<CanonicalFields>): Partial<CanonicalFields>;

  /** Full pipeline */
  adapt(raw: Uint8Array | string): RobotSnapshot;
}

/** Registry: robotId → adapter */
class AdapterRegistry {
  private adapters: Map<string, DataAdapter> = new Map();

  register(robotId: string, adapter: DataAdapter): void;
  getAdapter(robotId: string): DataAdapter | undefined;

  /** Attempt auto-detection by trying each adapter's parse() */
  autoDetect(raw: Uint8Array | string): DataAdapter | null;
}
```

### Field Mapping Examples

**JSON v1 Adapter:**
```typescript
// Input:  { "batLevel": 85.5, "jointTemp_0": 42, "cpuPct": 67 }
// Output: { battery: { percent: 85.5 }, joints: { "0": { temperature: 42 } }, cpu: { usagePercent: 67 } }
```

**Protobuf v1 Adapter:**
```typescript
// Input:  Binary protobuf with fields: battery_percentage=85, motor_temp=[42, 38, 45]
// Output: { battery: { percent: 85.0 }, joints: { "0": { temperature: 42 }, "1": { temperature: 38 }, ... } }
```

### Rationale

1. **Pipeline 三阶段分离关注点**：协议解析 (parse)、语义映射 (mapFields)、单位转换 (normalizeUnits)。每阶段可独立测试和复用
2. **AdapterRegistry 支持动态注册**：新机器人上线时注册对应 adapter，不影响现有机器人
3. **Auto-detect** 用于未知格式的容错：尝试所有已注册 adapter 的 parse，选择不抛异常的

### Error Handling

- `parse` 失败 → 标记 `status: 'offline'`，记录错误日志
- `mapFields` 无匹配 → 对应字段设为 `null`，不阻塞其他字段
- `normalizeUnits` 越界 → 钳制到合理范围（如 battery.percent clamp 0-100）

---

## ADR-004: Real-Time Data Flow

**Status:** Proposed
**Date:** 2026-05-26

### Decision

```
Robot Fleet → [各自的协议] → Backend Aggregation Service
                                  │
                     ┌────────────┼────────────┐
                     │            │            │
                 Adapter      Alert         History
                 Pipeline     Engine        Buffer
                     │            │            │
                     └────────────┼────────────┘
                                  │
                          WebSocket Server
                          (single port)
                                  │
                         wss:// (JSON)
                                  │
                     ┌────────────┼────────────┐
                     │                         │
              WebSocket Client          REST API (optional)
                     │                 /api/history/:robotId
              ┌──────┴──────┐         /api/config/:robotId
              │ State Store │         /api/comments/:robotId
              └──────┬──────┘
                     │
              ┌──────┴──────────────────┐
              │ React Components (UI)   │
              └─────────────────────────┘
```

**WebSocket 消息格式：**

```typescript
// Server → Client messages
type WSMessage =
  | { type: 'snapshot'; robotId: string; data: RobotSnapshot }
  | { type: 'alert'; alert: Alert }
  | { type: 'fleet_summary'; data: FleetSummary }
  | { type: 'heartbeat'; serverTime: number }

// Client → Server messages (config, comments go through REST)
type WSClientMessage =
  | { type: 'subscribe'; robotIds?: string[] }  // filter, '*' = all
  | { type: 'pong' }
```

**更新频率设计：**

| Data Type | Push Frequency | Rationale |
|-----------|---------------|-----------|
| Robot snapshot | 1 Hz (configurable 0.2-10 Hz) | 平衡实时性和带宽 |
| Alert | Immediate on trigger | 告警不能延迟 |
| Fleet summary | 1 Hz | 聚合数据，与 snapshot 同步 |
| Heartbeat | Every 15s | 保持连接活跃 |

### Reconnection Strategy

```
Initial → wait 1s → retry → wait 2s → retry → wait 4s → ... → max 60s
Reset to 1s after successful connection for 2+ minutes
```

### Rationale

- WebSocket 推送比轮询更高效，尤其在 20+ 机器人场景
- JSON 格式在 Demo 阶段可读性好，生产可升级为 MessagePack/Protobuf
- 客户端可订阅特定机器人，减少不需要的数据传输
- 告警即时推送给所有客户端，不需要各自轮询

---

## ADR-005: Alert Engine Design

**Status:** Proposed
**Date:** 2026-05-26

### Decision

告警引擎在 Backend Service 中运行，处理每个到达的 snapshot：

```typescript
interface AlertRule {
  id: string;
  robotId: string | '*';       // '*' = global rule
  metric: AlertMetric;
  operator: 'lt' | 'gt' | 'eq' | 'neq';
  threshold: number;
  severity: 'warning' | 'critical';
  cooldownMs: number;          // 去重窗口，默认 300000 (5 min)
  enabled: boolean;
}

type AlertMetric =
  | 'battery.percent'
  | 'battery.temperature'
  | 'cpu.usagePercent'
  | 'cpu.temperature'
  | 'network.latencyMs'
  | 'network.packetLoss'
  | `joints.${string}.temperature`
  | `joints.${string}.status`
  | 'status';                  // 机器人整体状态

interface Alert {
  id: string;
  ruleId: string;
  robotId: string;
  metric: AlertMetric;
  severity: 'warning' | 'critical';
  value: number;
  threshold: number;
  message: string;             // Human-readable, i18n key
  state: 'pending' | 'active' | 'acknowledged' | 'resolved';
  triggeredAt: number;
  acknowledgedAt?: number;
  acknowledgedBy?: string;
  resolvedAt?: number;
}

// State machine:
// pending → (cooldown passes) → active → (user acknowledges) → acknowledged → (condition clears) → resolved
// OR: pending → (condition clears before cooldown) → resolved (auto-resolve)
```

**预设告警规则（默认值，可配置）：**

| Rule | Metric | Op | Threshold | Severity | Cooldown |
|------|--------|----|-----------|----------|----------|
| Low Battery Warning | battery.percent | lt | 20 | warning | 10 min |
| Low Battery Critical | battery.percent | lt | 10 | critical | 5 min |
| High Joint Temp Warning | joints.*.temperature | gt | 50 | warning | 5 min |
| High Joint Temp Critical | joints.*.temperature | gt | 65 | critical | 2 min |
| High CPU Temp | cpu.temperature | gt | 80 | warning | 5 min |
| High Latency | network.latencyMs | gt | 500 | warning | 3 min |
| High Packet Loss | network.packetLoss | gt | 0.1 | warning | 3 min |
| Robot Offline | status | eq | offline | critical | 1 min |
| Joint Offline | joints.*.status | eq | offline | critical | 1 min |

### Rationale

- **Cooldown 去重**：避免同一条件在短时间内反复触发告警风暴
- **状态机**：跟踪告警生命周期，支持运维工程师确认和处理
- **规则 DSL 可配置**：满足需求#6（工程师调整阈值）
- **全局规则 + 单机规则**：`*` 规则适用于所有机器人，`robotId` 指定规则覆盖全局

---

## ADR-006: Frontend Component Architecture

**Status:** Proposed
**Date:** 2026-05-26

### Decision

组件树按功能域划分，共享 State Store：

```
<App>
├── <ThemeProvider>              ← Tailwind dark mode + ECharts theme
├── <I18nProvider>               ← react-i18next
├── <Layout>                     ← react-grid-layout
│   ├── <Header>
│   │   ├── <FleetStatsBar>      ← 在线率、平均电量、告警数
│   │   ├── <AlertBadge>         ← 告警计数 + 脉冲动画
│   │   ├── <ThemeToggle>
│   │   ├── <LanguageSwitcher>
│   │   └── <ConnectionStatus>
│   ├── <DashboardPage>          ← route: /
│   │   ├── <StatusDonutChart>   ← ECharts 环形图
│   │   ├── <CpuLatencyLineChart>← ECharts 折线图
│   │   ├── <JointTempHeatmap>   ← ECharts 热力图
│   │   └── <RobotGrid>
│   │       └── <RobotCard> ×20  ← 电池条、状态徽标、任务名
│   ├── <RobotDetailPage>        ← route: /robot/:id
│   │   ├── <GaugeCluster>       ← 4个仪表盘
│   │   ├── <JointStatusTable>
│   │   ├── <HistoryChart>       ← 时间范围选择器
│   │   ├── <RobotMap>           ← Leaflet
│   │   ├── <AlertTimeline>
│   │   └── <CommentThread>      ← 评论 + @提及
│   ├── <AlertPage>              ← route: /alerts
│   │   └── <AlertList>
│   ├── <ConfigPage>             ← route: /config
│   │   ├── <RobotSelector>
│   │   └── <ConfigForm>         ← 阈值/采样/重连
│   └── <ExportPanel>            ← 侧边栏/弹窗
```

### State Management (Zustand Stores)

```
robotStore:     Map<robotId, RobotSnapshot>  +  updateSnapshot(snapshot)
alertStore:     Alert[] + activeCount        +  addAlert / ackAlert / resolveAlert
configStore:    Map<robotId, RobotConfig>    +  updateConfig / resetConfig
commentStore:   Map<robotId, Comment[]>      +  addComment / deleteComment
layoutStore:    LayoutConfig[]               +  saveLayout / loadLayout
uiStore:        theme, language, connection  +  toggleTheme / setLanguage
historyStore:   Map<robotId, DataPoint[]>    +  appendDataPoint / queryRange
```

每个 Store 独立，组件通过 custom hooks 订阅需要的部分（自动 selector 优化）。

### Rationale

- Zustand 轻量（<1KB），无 boilerplate，适合频繁更新的实时数据
- 每个 Store 独立，避免不必要的重渲染（robotStore 更新不影响 configStore 的订阅者）
- Layout 与业务逻辑解耦，react-grid-layout 只消费 layoutStore

---

## ADR-007: Technology Stack

**Status:** Proposed
**Date:** 2026-05-26

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Framework** | React 18 + TypeScript 5 | 生态最成熟，类型安全 |
| **Build** | Vite 5 | 极速 HMR，ESM native |
| **Styling** | Tailwind CSS 3 + CSS Variables | Utility-first，dark mode 原生支持 |
| **Charts** | ECharts 5 | 大数据量实时更新，热力图/环形图/折线图内置 |
| **Maps** | Leaflet + OpenStreetMap | 免费，轻量，足够标注机器人位置 |
| **Layout** | react-grid-layout | 拖拽、调整大小、持久化 |
| **State** | Zustand 4 | 轻量、高性能、selector 优化 |
| **Server Cache** | TanStack Query 5 | REST API 缓存、自动重取 |
| **i18n** | react-i18next | 业界标准、namespace 分割 |
| **Export** | exceljs + window.print() | Excel 生成 + PDF through browser print |
| **Mock Server** | Bun + ws | 高性能 WebSocket，TypeScript native |
| **Testing** | Vitest + React Testing Library + Playwright | Vite 原生测试，组件测试 + E2E |

### Packages NOT Selected

| Package | Reason Rejected |
|---------|-----------------|
| D3.js | 需要手写大量图表逻辑，ECharts 声明式更高效 |
| MUI / Ant Design | 仪表盘需要高度定制样式，组件库限制太多 |
| Redux / MobX | Boilerplate 多，Zustand 满足需求且更简洁 |
| Mapbox GL JS | 收费，Leaflet 免费且满足标注需求 |
| Next.js | 仪表盘不需求 SSR/SSG，纯 SPA 更简单 |
| Recharts / Chart.js | 大数据量实时更新性能不如 ECharts |

---

## ADR-008: Deployment Topology (Demo)

**Status:** Proposed
**Date:** 2026-05-26

```
Developer Machine (localhost)
│
├── Frontend Dev Server (Vite :5173)
│   └── React SPA
│       ├── WebSocket → ws://localhost:3001
│       └── REST → http://localhost:3001/api/*
│
└── Backend Service (Bun :3001)
    ├── WebSocket Server
    ├── Mock Data Generator (20 robots)
    ├── Adapter Pipeline
    ├── Alert Engine
    ├── History Buffer (in-memory, ring buffer)
    └── REST API (comments, config, history queries)
```

Demo 阶段前后端合一 repo，通过 `concurrently` 或 `turbo` 一键启动。生产环境下 Backend Service 独立部署在边缘网关或中心云。

---

## Completion Report

```yaml
completion_report:
  what_was_done: "为 FleetOps Dashboard 产出 8 个架构决策记录，覆盖系统拓扑、数据模型、适配器管道、实时数据流、告警引擎、前端组件树、技术栈选型和部署拓扑"
  key_decisions:
    - decision: "Modular SPA + Backend Aggregation Service 架构"
      rationale: "SPA 适合仪表盘场景，Backend 作为数据归一化层解耦异构协议与前端展示"
    - decision: "Canonical Model 作为系统唯一数据表示，Adapter Pipeline 三阶段转换"
      rationale: "异构数据统一是整个系统最难的技术问题，Pipeline 模式提供可测试、可扩展的解决方案"
    - decision: "ECharts 作为图表库，Leaflet 作为地图库"
      rationale: "大数据量实时更新 + 免费方案，满足 Demo 和初期生产需求"
    - decision: "Zustand 多 Store 架构，按功能域分离"
      rationale: "实时数据频繁更新场景下，独立 Store 避免不必要的组件重渲染"
    - decision: "WebSocket 单一连接，JSON 消息格式"
      rationale: "Demo 阶段简单可调试，生产可升级为二进制协议"
    - decision: "告警引擎状态机 + Cooldown 去重"
      rationale: "避免告警风暴，支持运维工程师的确认→处理→解决工作流"
    - decision: "Demo 阶段前后端合一，Bun + Vite"
      rationale: "一键启动便于演示，降低演示环境依赖"
  handoff_focus:
    - "Canonical Model (ADR-002) 是所有实现工作的数据契约，必须首先稳定"
    - "Adapter Pipeline (ADR-003) 的 parse/mapFields/normalizeUnits 接口是实现异构数据支持的关键"
    - "Zustand Store 划分 (ADR-006) 决定了前端模块的通信方式"
    - "Alert Engine 状态机 (ADR-005) 需要精确实现去重和生命周期"
  open_questions:
    - "生产环境下 Backend Aggregation Service 是否独立团队开发和部署？"
    - "30 天历史数据量预估：20 robots × 1Hz × 86400s × 30d ≈ 52M data points。Demo 阶段内存存储可接受，生产需要时序数据库"
    - "多人协作时评论和配置的并发冲突策略？初期可乐观锁或 last-write-wins"
  known_constraints:
    - "所有 ADR 基于 Demo 阶段约束：单用户、内存存储、localhost 部署"
    - "生产环境需要考虑：多用户并发、持久化存储、横向扩展、安全认证"
    - "Leaflet 在中国大陆可能需要替换为国内地图服务（高德/百度）"
  confidence_differential: 0.90
  dissent_if_alone: null
  iteration_context: null
```
