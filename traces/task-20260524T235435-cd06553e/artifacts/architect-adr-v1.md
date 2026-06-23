# Architecture Decision Record: 机器人车队运维监控面板 (Robot Fleet Ops Dashboard)

---

## ADR-001: 架构范式 — Modular Monolith BFF + Microservices for Data Pipeline

### Context

需要构建一个 Web 运维面板，覆盖实时监控、异构数据归一化、告警、历史查询、配置管理、协同、报表导出、主题/i18n/布局共 9 个功能域。团队规模假设为中小组（3-6 人），初期需要快速交付完整功能。

### Decision

采用 **Modular Monolith BFF + 独立 Data Pipeline 微服务** 的混合架构。

```
┌────────────────────────────────────────────────────┐
│                  Browser (React SPA)                │
│  总览 │ 机器人列表 │ 详情 │ 告警 │ 报表 │ 配置 │ 设置  │
└──────────────┬─────────────────────────────────────┘
               │ REST + WebSocket
               ▼
┌─────────────────────────────────────────────────────┐
│              BFF (Node.js / Fastify)                 │
│  ┌──────────┬──────────┬──────────┬──────────┐     │
│  │ Robot    │ Alert    │ Config   │ Collab   │     │
│  │ Module   │ Module   │ Module   │ Module   │     │
│  ├──────────┼──────────┼──────────┼──────────┤     │
│  │ Report   │ Fleet    │ Auth     │ Export   │     │
│  │ Module   │ Module   │ Module   │ Module   │     │
│  └──────────┴──────────┴──────────┴──────────┘     │
│                                                     │
│  Shared: WS Hub │ i18n Resolver │ Config Cache      │
└──┬──────────────┬──────────────┬────────────────────┘
   │              │              │
   ▼              ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│PostgreSQL│ │TimescaleDB│ │  Redis   │
│(配置/用户│ │(时序遥测) │ │(缓存/WS) │
│ 评论/告警)│ │           │ │         │
└──────────┘ └────▲──────┘ └──────────┘
                  │
┌─────────────────┴───────────────────────────────────┐
│           Data Pipeline (独立微服务)                  │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐ │
│  │ Ingest   │→ │ Normalize │→ │ TSDB Writer      │ │
│  │ (MQTT/   │  │ (Schema   │  │ (批量写入         │ │
│  │  HTTP/   │  │  Mapper)  │  │  + 事件发布)      │ │
│  │  gRPC)   │  │           │  │                  │ │
│  └──────────┘  └───────────┘  └──────────────────┘ │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │  Alert Evaluator (嵌入 Pipeline)              │   │
│  │  每条归一化数据 → 规则评估 → 触发告警          │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Rationale

1. **BFF 用 Monolith**: 9 个功能域在初期边界模糊，过度拆分导致集成复杂度超过模块本身复杂度。Modular Monolith 保持代码边界清晰，未来可独立拆出。
2. **Data Pipeline 独立**: 异构数据归一化是系统的计算密集路径，独立部署允许独立扩缩容，且协议适配（MQTT/HTTP/gRPC/Protobuf 解析）与 Web 层无关。
3. **告警引擎嵌入 Pipeline**: 告警评估在每个数据点归一化后立即执行，避免从 TSDB 轮询的延迟和计算浪费。

### Alternatives Rejected

| Alternative | Why Rejected |
|---|---|
| 全微服务 | 9 个功能域 × 独立服务 = 过高的运维复杂度，初期团队无法承受 |
| 全 Monolith | 数据归一化管道与 Web 层耦合，独立扩容困难 |
| Serverless (Lambda) | 长连接 WebSocket + 持续数据流不适合 Lambda 计费模型 |
| 告警引擎独立服务 | 增加一跳网络延迟；告警需要原始数据点上下文，独立部署无优势 |

### Consequences

- BFF 模块间通过 TypeScript interface 通信，不通过网络
- Pipeline 通过 Redis Streams 与 BFF 解耦（告警事件、在线状态变更）
- 未来若某个 BFF 模块（如 Report Engine）需要独立扩容，可直接抽为微服务

---

## ADR-002: Data Pipeline — 归一化引擎设计

### Context

机器人回传数据格式不统一：JSON、Protobuf 转 JSON、MQTT binary payload，字段名和单位各异。需归一化为统一 Schema 后写入 TSDB。

### Decision

归一化引擎采用 **配置驱动的协议适配器 + 声明式映射规则** 架构。

```
                    ┌─────────────┐
  MQTT (binary) ──→ │ MQTT Adapter│──┐
                    └─────────────┘  │
                    ┌─────────────┐  │    ┌───────────────┐    ┌──────────┐
  HTTP (JSON)   ──→ │HTTP Adapter │──┼──→ │ Schema Mapper │──→ │TSDB Write│
                    └─────────────┘  │    │ (规则引擎)     │    └──────────┘
                    ┌─────────────┐  │    └───────┬───────┘
  gRPC (Protobuf)──→ │gRPC Adapter│──┘            │
                    └─────────────┘               ▼
                                           ┌──────────────┐
                                           │ Alert Eval    │
                                           │ (规则评估)     │
                                           └──────┬───────┘
                                                  ▼
                                           ┌──────────────┐
                                           │ Event Emitter │
                                           │ → Redis Stream│
                                           └──────────────┘
```

### 核心设计决策

**1. 协议适配器是插件，不是 if-else**

每个协议（JSON/MQTT/gRPC）一个适配器，输出统一中间格式（`RawTelemetry`）。新增协议只需添加适配器，不改核心逻辑。

**2. 映射规则声明式，热加载**

```yaml
# mapping_rules/humanoid-v3-json.yaml
protocol: json
field_map:
  "battery.level_pct": { source: "$.bat.pct", transform: "multiply(100)" }
  "joints[*].temperature_c": { source: "$.servos[*].temp", transform: "celsius" }
  "compute.cpu_pct": { source: "$.sys.cpu" }
  "network.latency_ms": { source: "$.conn.ping" }
  "location.lat": { source: "$.gps.latitude" }
  "location.lon": { source: "$.gps.longitude" }
unit_conversions:
  "temperature_c": { from: "fahrenheit", fn: "(v-32)*5/9" }
  "voltage_v": { from: "millivolt", fn: "v/1000" }
```

映射规则存储在 PostgreSQL `mapping_rules` 表，启动时加载，支持 API 热更新。

**3. 原始数据保留**

每条归一化后的数据同时保留 `source_raw` 字段（原始报文），用于审计和前端 tooltip 显示"原始值"。

**4. 告警评估在内联路径**

数据归一化后、写入 TSDB 前，立即评估告警规则。规则使用 JSONLogic 表达式，存储在 PostgreSQL `alert_rules` 表。

### Alternatives Rejected

| Alternative | Why Rejected |
|---|---|
| 前端归一化 | 数据量大时浏览器性能不可控，且安全风险（原始数据不应全部推送到前端） |
| Kafka 做消息队列 | 运维复杂度高于 Redis Streams，初期数据量不需要 Kafka 的分区持久化能力 |
| 硬编码协议解析 | 每加入新机器人型号需要改代码发版 → 违反热加载需求 |

---

## ADR-003: 时序数据存储

### Context

需要存储每台机器人每次上报的六维数据（电量、关节温度、CPU、网络延迟、任务、GPS），支持 30 天历史查询和降采样聚合。

### Decision

使用 **TimescaleDB**（PostgreSQL 扩展）作为时序存储。

计算：
- 50 台机器人 × 每 5 秒 1 次上报 = 10 条/秒
- 每条 ~2KB = 20KB/秒 ≈ 1.7GB/天 ≈ **51GB/30 天**（原始）
- 启用 TimescaleDB 压缩 → 预计 **~5GB/30 天**

```
-- 核心表结构
CREATE TABLE telemetry (
    time        TIMESTAMPTZ NOT NULL,
    robot_id    TEXT NOT NULL,
    battery_pct FLOAT,
    cpu_pct     FLOAT,
    latency_ms  FLOAT,
    location    GEOGRAPHY(POINT),
    joints      JSONB,          -- 关节数组（每机器人关节数不同）
    task        JSONB,          -- 当前任务快照
    anomalies   JSONB,          -- 异常检测结果
    source_raw  BYTEA           -- 原始报文（LZ4 压缩）
);

SELECT create_hypertable('telemetry', 'time');

-- 自动降采样：1小时 → 1分钟聚合，1天 → 5分钟，30天 → 1小时
SELECT add_continuous_aggregate_policy('telemetry_hourly', ...);
SELECT add_retention_policy('telemetry', INTERVAL '30 days');

-- 启用原生压缩（90%+ 压缩率）
ALTER TABLE telemetry SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'robot_id'
);
```

### Rationale

1. **SQL 查询能力**: 聚合查询（"过去 24 小时平均电量按小时分组"）用 SQL 比 InfluxDB Flux 更直观
2. **与 PostgreSQL 共存**: 配置、用户、评论在同一数据库实例，减少运维面
3. **自动降采样**: 连续聚合策略自动维护物化视图，30 天查询无需扫原始数据
4. **原生压缩**: 90%+ 压缩率，51GB → 5GB

### Alternatives Rejected

| Alternative | Why Rejected |
|---|---|
| InfluxDB | 单独运维一个数据库，增加复杂度；查询语言 Flux 学习成本 |
| ClickHouse | 分析场景强但运维复杂度高于 TimescaleDB，初期过度 |
| PostgreSQL 裸表 | 无自动分区/压缩/降采样，30 天 51GB 查询会扫全表 |

---

## ADR-004: 实时推送架构

### Context

前端需要 ≤2 秒延迟的实时数据更新。每台机器人每 5 秒一次上报，50 台 = 10 次/秒。

### Decision

**Pipeline 事件驱动 + Redis Pub/Sub + WebSocket Hub**

```
Pipeline (Alert Eval)
  │
  ├── 写入 TimescaleDB
  └── 发布事件到 Redis Stream: "telemetry:robot_id"
                    │
                    ▼
              Redis Streams
                    │
                    ▼
         BFF WebSocket Hub
         (消费者组订阅)
                    │
                    ▼
         Socket.IO → Browser
```

### 关键设计

| 决策点 | 选择 | 理由 |
|---|---|---|
| 传输协议 | Socket.IO (WebSocket + HTTP 长轮询 fallback) | 自动重连、房间(room)机制、广泛浏览器支持 |
| 事件通道 | Redis Streams（非 Pub/Sub） | Streams 支持消费者组、消息持久化、ack 机制，故障恢复不丢消息 |
| 订阅粒度 | 按机器人 ID 订阅房间 | 前端只订阅当前视图所需的机器人，详情页订阅单台，总览页订阅全部 |
| 心跳 | 30s 间隔 ping/pong | 检测僵尸连接，触发前端"重连中"提示 |

### 数据流

```
1. Pipeline 归一化 R-042 数据
2. Pipeline 写入 TimescaleDB
3. Pipeline 发布 XADD telemetry:all {robot_id: "R-042", data: {...}}
4. BFF WebSocket Hub 消费到事件
5. Hub 将数据推送到订阅了 "R-042" 房间的所有客户端
6. 浏览器 ECharts 追加数据点，卡片数值更新
```

---

## ADR-005: 告警引擎设计

### Context

四种异常类型（摔倒、关节失联、电量过低、自定义阈值），需要可配置规则、冷却去重、升级策略。

### Decision

**嵌入式规则引擎 + 告警状态机**

```
数据到达 Pipeline
       │
       ▼
┌──────────────────┐
│  Rule Evaluator   │  加载所有 active 告警规则
│  (JSONLogic)      │  逐条评估当前数据点
└──────┬───────────┘
       │ 匹配?
       ▼
┌──────────────────┐
│  Dedup + Cooldown │  检查 Redis: alert:{robot}:{type}:fired
│  Check            │  在冷却期内 → 丢弃
└──────┬───────────┘
       │ 通过
       ▼
┌──────────────────┐
│  Alert State      │  INSERT INTO alerts
│  Machine          │  PUBLISH alerts:new
└──────┬───────────┘
       │
       ▼
   WebSocket Hub → Browser 弹窗
```

### 告警生命周期状态机

```
                  ┌─────────┐
    规则匹配 ───→ │  FIRED   │
                  └────┬─────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
     ┌─────────┐ ┌─────────┐ ┌─────────┐
     │   ACK   │ │  MUTED  │ │ AUTO-   │
     │ (确认)  │ │ (静音)  │ │ RESOLVE │
     └────┬────┘ └────┬────┘ └─────────┘
          │           │
          ▼           │ (5 分钟后)
     ┌─────────┐      │
     │ CLOSED  │ ◄────┘
     └─────────┘
```

### 核心规则

| 告警类型 | 触发条件 | 严重度 | 冷却 |
|---|---|---|---|
| robot_fallen | anomalies 含 "fallen" | emergency | 0s（不回退） |
| joint_lost | 任意关节 status = "lost" | emergency | 10s |
| battery_critical | battery_pct < threshold 且非 idle | critical | 30s |
| joint_overheat | 任意关节 temp > threshold | warning | 60s |
| high_latency | latency_ms > threshold | warning | 60s |

---

## ADR-006: 前端架构

### Context

SPA 需要支持：实时数据展示、多种图表、地图、拖拽布局、暗/亮主题、多语言。

### Decision

**React 18 + Zustand（全局状态）+ React Query（服务端缓存）+ 模块化路由**

```
src/
├── app/
│   ├── App.tsx                    # 根组件 (ThemeProvider + I18nProvider)
│   ├── router.tsx                 # React Router v6 路由定义
│   └── layouts/
│       ├── DashboardLayout.tsx    # 侧边导航 + 顶栏 + 内容区
│       └── AuthLayout.tsx         # 登录页布局
│
├── features/                      # 功能模块 (每个模块自包含)
│   ├── fleet-overview/            # 总览仪表盘
│   │   ├── components/            # DonutChart, TrendLine, HeatMap
│   │   ├── hooks/                 # useFleetOverview
│   │   └── index.ts
│   ├── robot-detail/              # 机器人详情
│   │   ├── components/            # MetricCard, JointStatus, HistoryChart, CommentThread
│   │   ├── hooks/                 # useRobotTelemetry, useRobotConfig
│   │   └── index.ts
│   ├── alerts/                    # 告警中心
│   │   ├── components/            # AlertList, AlertFilter, AlertToast
│   │   ├── hooks/                 # useAlerts
│   │   └── index.ts
│   ├── reports/                   # 报表
│   ├── settings/                  # 系统设置
│   └── collaboration/             # 协同评论
│
├── shared/                        # 共享层
│   ├── components/                # Button, Modal, Drawer, Toast, ...
│   ├── hooks/                     # useWebSocket, useTheme, useI18n
│   ├── stores/                    # Zustand stores
│   │   ├── layoutStore.ts         # 拖拽布局持久化
│   │   ├── themeStore.ts          # 主题状态
│   │   └── userStore.ts           # 用户/认证
│   ├── services/                  # API 客户端
│   │   ├── robotService.ts
│   │   ├── alertService.ts
│   │   └── wsClient.ts            # Socket.IO 封装
│   ├── types/                     # 共享类型
│   │   └── telemetry.ts           # TelemetryData 类型（与归一化 Schema 对齐）
│   └── i18n/                      # 翻译文件
│       ├── zh-CN/
│       └── en/
```

### 关键状态管理决策

| 数据 | 管理方式 | 理由 |
|---|---|---|
| 实时遥测数据 | Zustand store + WebSocket 直接写入 | 高频更新，不需要 React Query 缓存 |
| 机器人列表/详情 | React Query | 带缓存、重试、后台刷新 |
| 告警列表 | React Query (invalidate on WS event) | 服务端分页 + WS 事件触发 refetch |
| 布局配置 | Zustand + localStorage 持久化 | 纯客户端状态 |
| 主题/i18n | Zustand + persisted | 无需服务端 |

### 图表库选择

| 图表类型 | 库 | 理由 |
|---|---|---|
| 环形图 (Donut) | ECharts | 动画流畅、支持点击跳转 |
| 折线图 (Trend) | ECharts | 大数据量高性能、支持缩放/平移 |
| 热力图 (Heatmap) | Mapbox GL JS + ECharts | Mapbox 负责地图底图，ECharts 覆盖热力层 |
| 关节状态图 | 自研 SVG 组件 | 人形机器人关节布局固定，不需要通用图表库 |

---

## ADR-007: 部署拓扑

### Decision

**Docker Compose（开发/小规模）→ Kubernetes（生产/大规模）**

```
                    ┌──────────────┐
                    │   Nginx      │  TLS 终止 + 静态资源
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  BFF × 2 │ │ Pipeline │ │  Redis   │
        │ (Node)   │ │  × 2     │ │          │
        └────┬─────┘ └────┬─────┘ └──────────┘
             │            │
             └─────┬──────┘
                   ▼
        ┌──────────────────┐
        │ PostgreSQL +      │
        │ TimescaleDB       │
        │ (主 + 只读副本)    │
        └──────────────────┘
```

| 组件 | 最小配置 | 推荐配置 |
|---|---|---|
| BFF | 1 vCPU, 512MB × 1 | 2 vCPU, 1GB × 2 |
| Pipeline | 2 vCPU, 1GB × 1 | 2 vCPU, 2GB × 2 |
| PostgreSQL | 2 vCPU, 4GB, 100GB SSD | 4 vCPU, 16GB, 500GB SSD + 只读副本 |
| Redis | 1 vCPU, 1GB | 2 vCPU, 4GB + Sentinel |

---

## System Data Flow (End-to-End)

```
Robot (Edge)                    Cloud                           Browser
───────────                     ─────                           ───────

┌──────────┐                                                    
│ 传感器采集 │                                                   
│ (5s 周期) │                                                   
└────┬─────┘                                                    
     │ MQTT / HTTP / gRPC                                       
     ▼                                                          
┌──────────┐    ┌──────────┐    ┌──────────┐                   
│ 边缘网关  │───→│ Pipeline │───→│TimescaleDB│                  
│ (可选)   │    │ Ingest   │    │  Write    │                  
└──────────┘    └────┬─────┘    └──────────┘                   
                     │                                         
                     │ normalize                                
                     ▼                                         
                ┌──────────┐                                   
                │ Normalize│                                   
                │ (Map     │                                   
                │  Rules)  │                                   
                └────┬─────┘                                   
                     │                                         
                     ├──→ TSDB Write ──→ TimescaleDB           
                     │                                         
                     ├──→ Alert Eval ──→ Redis Stream ─────────┐
                     │   (match?)                              │
                     │       │ YES                             │
                     │       ▼                                 │
                     │  ┌──────────┐    ┌──────────┐          │
                     │  │Dedup+    │───→│PostgreSQL│          │
                     │  │Cooldown  │    │ alerts   │          │
                     │  └──────────┘    └──────────┘          │
                     │                                         │
                     └──→ Redis Stream ────────────────────────┤
                          "telemetry:new"                      │
                                                               ▼
                                                          ┌──────────┐
                                                          │ BFF WS   │
                                                          │ Hub      │
                                                          └────┬─────┘
                                                               │
                                          ┌────────────────────┤
                                          ▼                    ▼
                                     ┌──────────┐       ┌──────────┐
                                     │ Dashboard│       │ Detail   │
                                     │ Page     │       │ Page     │
                                     │ (全部)    │       │ (R-042)  │
                                     └──────────┘       └──────────┘
```

---

## Security Considerations

| 威胁 | 缓解措施 |
|---|---|
| 机器人数据链路被劫持 | mTLS（边缘网关 ↔ Pipeline），数据签名验证 |
| 未授权访问面板 | JWT + RBAC（管理员/工程师/只读），Token 过期 8h |
| 评论注入 (XSS) | 评论内容 sanitize，禁止 HTML |
| API 滥用 | Rate limiting: 100 req/min per user, 1000 req/min total |
| 配置被恶意修改 | 配置修改记录审计日志（谁、何时、改了什么、旧值） |
| WebSocket 劫持 | Socket.IO auth middleware 验证 JWT |

---

## Key Metrics & SLIs

| 指标 | 目标 | 监控方式 |
|---|---|---|
| 数据延迟（采集→面板显示） | P95 < 2s | Pipeline 到 WS Hub 的时间戳差值 |
| 归一化吞吐 | > 100 msg/s | Pipeline metrics |
| API 响应时间 | P95 < 200ms | BFF request duration |
| WebSocket 消息延迟 | P95 < 500ms | WS event timestamp diff |
| 告警漏报率 | 0% | 每日抽样审计 |
| 页面加载时间 | FCP < 1.5s | RUM (Real User Monitoring) |

---

## Open Questions

1. **边缘网关是否存在？** 若机器人直接上报到云端，Pipeline 需直接暴露 MQTT/gRPC 端点。若有边缘网关，Pipeline 只需对接网关。
2. **多车队/多区域？** 当前设计按单车队单区域。多区域需考虑 TSDB 按区域分区 + 联邦查询。
3. **机器人身份认证机制？** 是证书（mTLS）还是 Token？影响 Pipeline Ingest 的认证层设计。

---

## Handoff Focus for Downstream Nodes

| Node | What to focus on |
|---|---|
| `api-designer` | REST/WS API 契约基于 ADR-004/006 的接口草案，补充错误码和分页规范 |
| `database-engineer` | ADR-003 的 TimescaleDB schema、索引策略、retention policy 的具体 DDL |
| `senior-engineer` | ADR-002 的 Pipeline 实现（协议适配器接口、映射引擎、告警评估器） |
| `devops-engineer` | ADR-007 的 Docker Compose 文件和 CI/CD pipeline |
| `senior-frontend` | ADR-006 的前端模块划分、组件树、WebSocket 集成 |
| `security-engineer` | 安全威胁模型中标注的 mTLS、JWT、审计日志 |
