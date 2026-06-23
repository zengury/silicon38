# PRD: 人形机器人车队运维监控面板 (FleetOps Dashboard)

## Problem Statement

运维工程师需要同时管理一批异构的人形机器人（不同厂商、不同数据协议），当前缺乏统一的监控面板。每台机器人回传的数据格式、字段名、单位均不一致，工程师需要频繁切换多个工具才能掌握车队整体状态。异常发生时（摔倒、关节失联、电量过低），缺乏即时告警机制。工程师之间也无法在面板内协作处理故障。

## Solution

一个 Web 端运维监控面板（FleetOps Dashboard），提供统一的机器人车队实时监控、异常告警、历史分析、工程师协作和报表导出能力。系统通过适配层统一异构数据源，对外提供一致的数据模型。

## User Stories

1. 作为运维工程师，我想要在一个总览仪表盘上看到整个车队的健康度概览（在线率、平均电量、告警数），以便快速判断当前车队是否正常。
2. 作为运维工程师，我想要通过环形图查看机器人按状态的分布（在线/离线/告警/维护），以便了解车队整体可用性。
3. 作为运维工程师，我想要通过热力图查看机器人关节温度的空间分布，以便定位是否存在系统性散热问题。
4. 作为运维工程师，我想要通过折线图查看车队 CPU 负载和网络延迟的趋势，以便提前发现性能劣化。
5. 作为运维工程师，我想要在列表/网格视图中看到每台机器人的实时数据（电量、关节温度、CPU、网络延迟、当前任务、地理位置），以便逐台巡检。
6. 作为运维工程师，我想要机器人回传数据时系统自动适配不同字段名和单位（如 `battery_pct` vs `batLevel`，摄氏度 vs 华氏度），以便无论数据源格式如何都能统一展示。
7. 作为运维工程师，我点击某台机器人后能看到其过去 30 天的历史曲线（电量、温度、CPU、延迟），以便分析趋势和排查历史问题。
8. 作为运维工程师，当机器人出现摔倒、关节失联、电量低于阈值时，我希望收到实时告警通知（声音 + 视觉高亮），以便立即响应。
9. 作为运维工程师，我希望能自定义每台机器人的告警阈值（温度上限、电量下限、延迟上限），以便适应不同机型和工况。
10. 作为运维工程师，我希望能调整每台机器人的采样频率（数据上报间隔），以便在带宽和精度之间取得平衡。
11. 作为运维工程师，我希望能配置每台机器人的重连策略（最大重试次数、回退间隔），以便在网络不稳定时自动恢复连接。
12. 作为运维工程师，我能在某台机器人详情页下留言评论、@同事，并标记"我在处理"，以便团队协作排障。
13. 作为运维工程师，我希望通过拖拽自定义面板布局（移动、调整图表大小），以便构建符合个人习惯的工作台。
14. 作为运维工程师，我希望在暗色/亮色主题之间切换，以便在不同光照环境下舒适工作。
15. 作为运维工程师，我希望面板支持多语言（至少中/英文），以便国际化团队使用。
16. 作为运维工程师，我希望能将当前视图或历史数据导出为 PDF 或 Excel 报表，以便存档和汇报。
17. 作为运维工程师，当告警触发时我希望能看到告警时间线和已处理的告警历史，以便追踪处理状态。

## Implementation Decisions

### 1. 技术栈选型

**前端**: React 18 + TypeScript + Vite。理由：生态成熟、组件丰富、适合数据密集型仪表盘。

**图表库**: ECharts（环形图、折线图、热力图）。理由：对大数据量实时更新友好，热力图开箱即用。

**状态管理**: Zustand（轻量）或 TanStack Query（服务端状态缓存）。理由：仪表盘以服务端数据为主，TanStack Query 更适合缓存和轮询策略。

**布局**: react-grid-layout 实现可拖拽自定义布局。

**主题/国际化**: Tailwind CSS dark mode + react-i18next。

**构建目标**: 纯前端 SPA，通过 REST API / WebSocket 与后端通信。无需 SSR。

### 2. 数据适配层（核心模块）

这是整个系统最关键的架构决策。设计一个 **Schema Adapter Pipeline**：

```
原始消息（JSON/Protobuf）→ Parser（按协议类型选择）→ Normalizer（统一字段名+单位转换）→ Canonical Model → 前端
```

**Canonical Model（统一数据模型）**：

```typescript
interface RobotSnapshot {
  robotId: string;
  timestamp: number;          // Unix ms, UTC
  battery: {
    percent: number;          // 0-100
    voltage: number;          // volts
    estimatedRemaining: number; // seconds
  };
  joints: Record<string, {
    temperature: number;      // celsius
    status: 'ok' | 'warning' | 'critical' | 'offline';
    torque: number;           // N·m
  }>;
  cpu: {
    usagePercent: number;
    temperature: number;      // celsius
  };
  network: {
    latencyMs: number;
    signalStrength: number;   // dBm
    packetLoss: number;       // 0-1
  };
  task: {
    id: string | null;
    name: string | null;
    progress: number | null;  // 0-100
  };
  location: {
    lat: number;
    lng: number;
    heading: number;          // degrees
    speed: number;            // m/s
  };
  status: 'online' | 'offline' | 'warning' | 'critical' | 'maintenance';
  rawFormat: 'json_v1' | 'json_v2' | 'protobuf_v1';
}
```

**Adapter 注册机制**：每种数据源格式实现一个 `Adapter` 接口，通过 `robotId` 路由到对应适配器。

```typescript
interface DataAdapter {
  protocol: string;
  parse(raw: Uint8Array | object): Partial<RobotSnapshot>;
  normalize(parsed: any): Partial<RobotSnapshot>;
}
```

### 3. 模块划分

| 模块 | 职责 | 接口 |
|------|------|------|
| `data-adapter` | 异构数据解析与规范化 | Adapter Registry + Canonical Model |
| `realtime-engine` | WebSocket 连接管理、心跳、重连 | subscribe(robotId) → Observable<RobotSnapshot> |
| `alert-engine` | 阈值判定、告警去重、通知分发 | evaluate(snapshot, rules) → Alert[] |
| `history-store` | 30 天时序数据存储与查询 | query(robotId, metric, range) → DataPoint[] |
| `collab-service` | 评论、@提及、处理标记 | CRUD for comments + mention notify |
| `export-service` | PDF/Excel 导出 | export(view, format) → Blob |
| `config-store` | 阈值/采样频率/重连策略存储 | getConfig(robotId) / setConfig(robotId, patch) |
| `dashboard-layout` | 拖拽布局持久化 | saveLayout(userId, layout) / loadLayout(userId) |

### 4. 实时数据架构

前端不直接连接每台机器人。后端通过 WebSocket 推送聚合后的 Canonical Model：

```
机器人群 → [各自协议] → 后端聚合服务（Data Adapter Pipeline）→ WebSocket → 前端
```

前端使用一个 WebSocket 连接接收所有机器人的更新，通过 `robotId` 分流到对应视图组件。

更新频率：总览数据 1Hz，单台详情 5Hz（可由运维工程师调整）。

### 5. 告警引擎

告警规则以 DSL 形式存储，引擎在每个 snapshot 到达时评估：

```typescript
interface AlertRule {
  id: string;
  robotId: string | '*';     // '*' = 全局
  metric: string;            // 'battery.percent', 'joints.*.temperature'
  operator: 'lt' | 'gt' | 'eq';
  threshold: number;
  severity: 'warning' | 'critical';
  cooldownMs: number;        // 去重窗口
}
```

告警状态机：`pending → active → acknowledged → resolved`

### 6. 协作功能设计

评论数据结构：

```typescript
interface Comment {
  id: string;
  robotId: string;
  authorId: string;
  text: string;
  mentions: string[];         // @的用户ID列表
  claimStatus: 'none' | 'investigating' | 'fixing' | 'resolved';
  createdAt: number;
}
```

### 7. 导出功能

- PDF：通过浏览器打印 API（`window.print()` + `@media print` CSS）渲染当前仪表盘视图
- Excel：使用 `exceljs` 库生成 `.xlsx`，包含原始时序数据

## Testing Decisions

- 单元测试：Data Adapter 的 parse/normalize 逻辑（覆盖每种协议格式的 fixture 数据）
- 集成测试：Alert Engine 的阈值判定和去重逻辑
- 组件测试：仪表盘图表的渲染（使用 mock WebSocket 数据流）
- E2E：核心用户流程（登录 → 查看总览 → 点击机器人 → 查看历史 → 导出报表）
- 测试工具：Vitest + React Testing Library + Playwright

评判好测试的标准：只测试外部行为，不测试实现细节。例如测试 Adapter 的 `parse` 输出是否符合 Canonical Model，但不对内部 parser 实现做假设。

## Out of Scope

- 机器人遥控功能（本面板为只读监控）
- 机器人固件 OTA 更新
- 用户权限管理系统（初期假设单团队使用）
- 移动端 App
- 语音告警
- 视频流/摄像头画面集成
- 第三方监控系统集成（Prometheus/Grafana 等）
- 离线模式 / PWA
- 自定义仪表盘插件市场

## Further Notes

- 客户需求中的"地理位置"展示：使用 Mapbox 或 Leaflet 嵌入地图组件，标注机器人位置和朝向。
- 多语言：初期支持中文（zh-CN）和英文（en-US），通过 `i18next` 的 namespace 分割各模块文案。
- 暗色主题：基于 Tailwind 的 `dark:` 前缀，ECharts 主题跟随切换。
- Demo 阶段可先使用 mock 数据生成器，模拟 20 台机器人的真实行为（电量随机波动、偶尔触发告警、温度随任务变化等）。

---

## Completion Report

```yaml
completion_report:
  what_was_done: "将客户需求转化为完整 PRD，定义 17 条可测试用户故事、7 项实现决策、测试策略和明确范围边界"
  key_decisions:
    - decision: "设计 Schema Adapter Pipeline 作为异构数据统一层的核心架构"
      rationale: "客户明确要求支持多种不统一的数据格式，这是整个系统最关键的技术挑战。适配器模式提供可扩展的协议注册机制"
    - decision: "前端使用纯 SPA 架构，后端通过 WebSocket 推送 Canonical Model"
      rationale: "实时监控面板的核心是数据流的时效性，WebSocket 推送 + 前端消费是最直接的方案。后端做数据归一化，前端只负责展示"
    - decision: "告警引擎独立为可配置模块，规则 DSL 存储"
      rationale: "客户需要自定义阈值，规则 DSL 提供最大灵活性。独立模块便于测试和维护"
    - decision: "协作功能采用轻量评论+@提及模型，不引入完整聊天系统"
      rationale: "运维协作不需要完整 IM，轻量评论足以满足"标记我在处理"和"@同事"的需求"
  handoff_focus:
    - "异构数据适配层的 Canonical Model 定义和 Adapter 接口是后续架构设计的输入"
    - "实时数据流架构（WebSocket 推送频率、消息格式）需要架构师细化"
    - "告警引擎的状态机和去重策略需要进一步设计"
  open_questions:
    - "后端聚合服务的部署位置（边缘网关 vs 中心云）影响延迟和可用性"
    - "30 天历史数据的存储方案（时序数据库选择：InfluxDB vs TimescaleDB vs ClickHouse）"
    - "地图服务选型（Mapbox 收费 vs Leaflet 免费）需要根据预算决定"
    - "用户认证方式（OAuth2 SSO vs 本地账号）未明确"
  known_constraints:
    - "不同机器人厂商的数据协议差异大，Adapter 注册机制必须是动态可扩展的"
    - "实时性要求：总览 1Hz、详情 5Hz 意味着后端需要处理 20-100 台机器人的数据流"
    - "浏览器性能：同时渲染 20+ 台机器人的图表需要考虑虚拟化和增量更新"
  confidence_differential: 0.85
  dissent_if_alone: null
  iteration_context: null
```
