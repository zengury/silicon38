# Architecture Decision Record — 机器人车队运维监控面板 (FleetOps Dashboard)

> 角色: architect | 来源: PRD + UX Spec | 版本: v1.0

---

## ADR-001: 系统分层架构

### Context
车队运维面板需要处理异构数据接入、实时推送、时序存储、告警、协作、报表六大能力域。系统需要支撑 50 台机器人同时在线，告警延迟 < 2 秒，30 天历史查询 < 2 秒。

### Decision
采用 **5 层管道架构**：Ingest → Normalize → Process → Serve → Present。

```
                       ┌─────────────────────────────────────┐
                       │          PRESENT (Browser)           │
                       │  React SPA — WebSocket + REST        │
                       └──────────┬──────────────────────────┘
                                  │ WSS / HTTPS
                       ┌──────────▼──────────────────────────┐
                       │            SERVE (API)               │
                       │  ┌──────────┐  ┌──────────────────┐ │
                       │  │ WS Gateway│  │  REST API Server │ │
                       │  │ (Go)     │  │  (Node/Fastify)  │ │
                       │  └────┬─────┘  └───────┬──────────┘ │
                       └───────┼─────────────────┼────────────┘
                               │                 │
                  ┌────────────▼───┐   ┌────────▼──────────┐
                  │    PROCESS     │   │                    │
                  │ ┌────────────┐ │   │   PostgreSQL       │
                  │ │Alert Engine│ │   │   (config, users,  │
                  │ │(Rule-based)│ │   │    comments,       │
                  │ └────────────┘ │   │    claims)         │
                  └───────┬────────┘   └────────────────────┘
                          │
               ┌──────────▼──────────────────────────────┐
               │              STORE                       │
               │  ┌────────────────┐  ┌────────────────┐ │
               │  │   TimescaleDB  │  │     Kafka       │ │
               │  │ (30d telemetry)│  │ (Message Queue) │ │
               │  └────────────────┘  └────────────────┘ │
               └──────────▲──────────────────────────────┘
                          │
               ┌──────────┴──────────────────────────────┐
               │            NORMALIZE                     │
               │  ┌────────────────────────────────────┐  │
               │  │   Normalizer Service (Python/Go)    │  │
               │  │   Adapter Registry (hot-load YAML)  │  │
               │  │   Unit Conversion + Schema Mapping  │  │
               │  └────────────────────────────────────┘  │
               └──────────▲──────────────────────────────┘
                          │
               ┌──────────┴──────────────────────────────┐
               │              INGEST                      │
               │  ┌────────────────────────────────────┐  │
               │  │   Ingestion Gateway (Go)            │  │
               │  │   Multi-protocol: HTTP/MQTT/gRPC    │  │
               │  │   Auth + Rate Limit + Validation     │  │
               │  └────────────────────────────────────┘  │
               └──────────▲──────────────────────────────┘
                          │
               ┌──────────┴──────────────────────────────┐
               │         ROBOTS (data sources)            │
               │  JSON / Protobuf-derived / Custom binary │
               └─────────────────────────────────────────┘
```

### Rationale
- **管道分层**确保每层职责单一、可独立测试和替换。Normalize 层变化（新增 adapter）不影响 Serve 层。
- **Kafka** 作为中间缓冲解耦 Ingestion Gateway 和 Normalizer Service，允许两者独立扩缩容。
- **TimescaleDB** 选时序数据库而非普通 PostgreSQL，因为 30 天 × 50 台 × 每秒 1 条 = 1.3 亿条数据，需要时序优化（自动分区、降采样、压缩）。
- **WebSocket Gateway 用 Go**：高并发长连接场景下 Go 的 goroutine 模型是天然优势。Node 也能做，但 50 台机器人 × N 个浏览器连接时开销更大。
- **REST API Server 用 Node/Fastify**：团队如果已有 Node 技术栈可以减少认知负担；协作功能（留言/认领）是标准 CRUD，Node 生态成熟。

### Alternatives Rejected
- **不用 Redis Pub/Sub 替代 Kafka**：Redis Pub/Sub 不持久化，消费者离线时消息丢失。监控面板需要消息可靠性（如果 normalizer 重启，不应丢数据）。
- **不用 InfluxDB**：TimescaleDB 基于 PostgreSQL，支持完整 SQL 和 JOIN，对报表生成更友好（报表常需要 JOIN 机器人元数据）。
- **不用 MQTT Broker 替代 Ingestion Gateway**：MQTT 适合 IoT，但车队中部分机器人可能只有 HTTP 上报能力。Gateway 做协议适配更好。

### Consequences
- 运维复杂度增加（Kafka + TimescaleDB + PostgreSQL 三个有状态服务）
- Go WebSocket Gateway 引入第二语言，团队需要 Go 能力或愿意学习
- 管道架构使系统延迟可预期：Ingest → Normalize → WS Gateway 路径 < 500ms

---

## ADR-002: 数据归一化策略 — Adapter 模式

### Context
机器人回传数据格式不统一：字段名不同（`battery` vs `bat_pct` vs `power_level`），单位不同（华氏 vs 摄氏），编码不同（JSON vs Protobuf 衍生）。需要在不修改核心代码的前提下支持新机型接入。

### Decision
实现 **Adapter Registry** 模式：

```yaml
# adapter_registry.yaml
adapters:
  - id: "g1-default"
    robot_model: "Unitree G1"
    protocol: json
    mapping:
      battery_pct: "$.power.battery_percentage"
      joint_temps: "$.joints[*].temperature_celsius"
      cpu_pct: "$.system.cpu_load"
      network_latency_ms: "$.network.rtt_ms"
      current_task: "$.mission.name"
      gps: {lat: "$.location.latitude", lon: "$.location.longitude"}
    unit_conversions:
      joint_temps: "identity"  # already celsius
      
  - id: "legacy-r2"
    robot_model: "Legacy R2"
    protocol: protobuf_derived
    proto_file: "protos/legacy_r2.proto"
    mapping:
      battery_pct: "power_state.soc"   # state of charge, 0-1 → multiply by 100
      joint_temps: "motor_states[].temp"  # fahrenheit → convert
      cpu_pct: "sys_info.load_avg"
      network_latency_ms: "comm.latency_us"  # microseconds → divide by 1000
      current_task: null  # this robot model doesn't report current task
      gps: null           # no GPS
    unit_conversions:
      battery_pct: "multiply(100)"
      joint_temps: "fahrenheit_to_celsius"
      network_latency_ms: "divide(1000)"
```

Normalizer 启动时加载 registry，按 `robot_id` 前缀或 `robot_model` 匹配 adapter。新机型接入 = 新增一个 YAML entry + 可选的 .proto 文件。

### Rationale
- **适配器是声明式配置**，不是代码。运维工程师自己可以添加新机型映射，不需要开发参与。
- **YAML 热加载**：adapter 文件变更后，normalizer 自动 reload（watch 文件变化），无需重启服务。
- **单位转换**在 normalize 阶段一次完成，下游永远拿摄氏度和百分比，不用再关心原始单位。

### Alternatives Rejected
- **不用 ETL 工具（如 Apache NiFi）**：太重。运维面板只需要简单的字段映射+单位转换，引入 ETL 是一头大象踩一个钉子。
- **不用 AI/LLM 自动推断映射**：不可靠。字段名 `bat` 在不同厂商可能代表 `battery` 或 `batch_id`。人工配置一次比 AI 猜错一次更安全。

### Consequences
- 每种新机型需要一个人工维护 YAML adapter（一次性成本 ~ 10 分钟）
- 如果未来有 50 种机型，adapter 目录会很大，但每个文件很小，可管理
- 复杂转换逻辑（如 Protobuf 嵌套结构解析）可能超出 YAML 表达能力，需要 code-based adapter 逃生门

---

## ADR-003: 前端架构 — React SPA

### Context
面板是 Web SPA，需要实时数据流、复杂图表、可拖拽布局、主题切换、国际化。需要支持 50 台机器人数据的同时渲染。

### Decision

```
src/
├── app/                    # Next.js App Router (or Vite SPA)
├── features/
│   ├── dashboard/          # 总览仪表盘
│   │   ├── FleetGrid.tsx    # 机器人卡片网格
│   │   ├── RingChart.tsx    # 环形图
│   │   ├── TrendLine.tsx    # 折线图
│   │   └── Heatmap.tsx      # 地理热力图
│   ├── robot-detail/       # 机器人详情
│   │   ├── TelemetryPanel.tsx
│   │   ├── HistoryChart.tsx
│   │   └── CommentThread.tsx
│   ├── alerts/             # 告警中心
│   │   ├── AlertList.tsx
│   │   └── AlertBanner.tsx
│   ├── config/             # 配置管理
│   │   └── ConfigPanel.tsx
│   ├── export/             # 报表导出
│   │   └── ExportDialog.tsx
│   └── collaboration/      # 协作
│       ├── CommentInput.tsx
│       └── ClaimButton.tsx
├── shared/
│   ├── hooks/
│   │   ├── useWebSocket.ts      # WebSocket 连接管理 + 自动重连
│   │   ├── useTelemetry.ts      # 遥测数据订阅 + 缓存
│   │   └── useAlerts.ts         # 告警订阅
│   ├── components/
│   │   ├── RobotCard.tsx
│   │   ├── StatusDot.tsx
│   │   └── ThemeToggle.tsx
│   ├── store/
│   │   ├── fleetStore.ts        # 车队状态 (Zustand)
│   │   ├── alertStore.ts        # 告警状态
│   │   └── layoutStore.ts       # 布局配置 (persist to localStorage)
│   └── i18n/
│       ├── zh.json
│       └── en.json
└── styles/
    ├── tokens.css           # 设计 token (CSS Variables)
    ├── dark.css             # 暗色主题变量
    └── light.css            # 亮色主题变量
```

**技术选型**:
| 层 | 选择 | 理由 |
|----|------|------|
| 框架 | React 18 + TypeScript | 团队通用技能；生态最成熟 |
| 构建 | Vite | 快；SPA 场景比 Next.js 更轻 |
| 状态管理 | Zustand | 轻量、TypeScript 友好、支持 persist middleware |
| 图表 | ECharts | 内置环形图/折线图/热力图；大数据量性能好 |
| 地图 | Leaflet + OpenStreetMap | 免费；离线可用 tile cache |
| 拖拽布局 | react-grid-layout | 成熟稳定；支持响应式断点和持久化 |
| WebSocket | 原生 WebSocket + 自建 reconnection hook | 不引入额外库 |
| i18n | react-i18next | 生态标准 |
| 主题 | CSS Variables + data-theme attribute | 零运行时开销；图表通过 ECharts theme 同步切换 |

### Rationale
- **Zustand over Redux**: 状态结构简单（车队状态是一个 key-value map），不需要 Redux 的 reducer/action 仪式。Zustand 的 `persist` middleware 天然支持布局和主题持久化。
- **ECharts over D3**: D3 灵活但学习曲线陡峭。ECharts 提供开箱即用的 ring/line/heatmap，配置声明式，团队 1 天可上手。
- **Feature-based 目录结构**: 每个功能模块自包含（组件 + hooks + 类型），让不同工程师可以并行开发不同 feature 而不会产生 merge conflict。
- **Vite over Next.js**: 面板是纯 SPA，没有 SEO 需求，不需要 SSR。Vite 更简单更快。

### Alternatives Rejected
- **不用 Server-Sent Events (SSE) 替代 WebSocket**: SSE 单向推送适合遥测，但协作功能（留言发送）需要双向。同一个 WebSocket 承载遥测+告警+协作通知，减少连接数。
- **不用 GraphQL 替代 REST**: 面板的数据查询模式是固定的（列表/详情/历史），GraphQL 的灵活查询是过度设计。REST 端点足够，且更容易缓存。

### Consequences
- ECharts bundle size 较大（~1MB），需要按需引入（仅引入使用的图表类型）
- react-grid-layout 的拖拽在大量卡片时可能有性能问题（> 50 张卡片），需要虚拟化策略

---

## ADR-004: 告警引擎设计

### Context
需要检测摔倒、关节失联、电量过低等异常，在 < 2 秒内推送告警到前端。同一告警不应重复触发（避免告警风暴）。

### Decision

```python
# 告警规则结构 (stored in PostgreSQL, hot-reloaded by Alert Engine)
{
  "rule_id": "battery-critical",
  "condition": "battery_pct < threshold",
  "severity": "CRITICAL",
  "default_threshold": {"battery_pct": 15},
  "robot_overrides": {"robot_03": {"battery_pct": 10}},  # per-robot
  "auto_resolve": False,    # CRITICAL → manual
  "cooldown_seconds": 300,  # 5 min dedup
  "description_template": "电量严重不足 (${value}%)"
}
```

**告警生命周期**:
```
Normal ──► rule triggered ──► FIRING ──► auto_resolve? ──Yes──► RESOLVED
                                        │                        ▲
                                        └── No ──► ACKNOWLEDGED ─┘
                                                        │
                                              (engineer clicks "已处理")
```

**架构**:
- Alert Engine 作为独立 goroutine/进程，消费 Kafka normalized topic
- 每条 RobotTelemetry 到达时，评估所有匹配该 robot_id 的规则
- 匹配的告警检查 cooldown：同一 (robot_id, rule_id) 在 cooldown 内不重复
- 新告警写入 PostgreSQL + 通过 Kafka `robot.alert` topic 推送到 WebSocket Gateway
- WebSocket Gateway 消费 alert topic → 按 robot_id 路由到订阅该机器人的浏览器

**摔倒检测**:
- 机器人固件发送 `status: ERROR` + `error_code: FALL_DETECTED` → Alert Engine 直接映射为 CRITICAL
- 不使用姿态估算（不依赖 IMU 数据，信任固件判断）

**关节失联检测**:
- `joint_temps` 中某关节字段缺失 3 个连续采样周期 → WARNING: JOINT_DISCONNECTED
- 恢复到有数据 2 个采样周期 → 自动 RESOLVED

### Rationale
- **规则引擎而非 ML**: 告警条件是确定性的（阈值判断），不需要 ML。ML 在可解释性和误报方面都是劣势。
- **Kafka 解耦告警生产和推送**: Alert Engine 只需要关心规则评估，不需要管理 WebSocket 连接。WebSocket Gateway 只需要关心消息路由。
- **Cooldown 防抖**: 电量在 15% 附近波动时不会产生告警风暴。5 分钟的 cooldown 在运维场景中合理（一次告警足够引起注意）。

### Alternatives Rejected
- **不用 Prometheus AlertManager**: AlertManager 主要针对基础设施监控（CPU/内存），其 rule 语法（PromQL）不适合业务级告警（"电量低于 X%，但仅在正在执行任务时告警"）。
- **不用复杂事件处理 (CEP)**: CEP 适合关联多个事件流（如"A 发生且 5 分钟内 B 也发生"）。当前需求是单事件触发条件，CEP 是杀鸡用牛刀。

### Consequences
- Alert Engine 成为关键路径上的单点。需部署多实例 + Kafka consumer group 保证高可用
- Per-robot threshold 增加了规则评估的复杂度（不是简单的全局阈值）

---

## ADR-005: 历史数据存储与查询

### Context
需要存储每台机器人每秒一条的遥测数据，保留 30 天，查询 < 2 秒。30 天 × 50 台 × 3600 × 24 ≈ 1.3 亿行。

### Decision

**TimescaleDB hypertable**:

```sql
CREATE TABLE telemetry (
    time        TIMESTAMPTZ NOT NULL,
    robot_id    TEXT NOT NULL,
    battery_pct FLOAT,
    cpu_pct     FLOAT,
    joint_temps JSONB,       -- {"left_knee": 42.5, "right_knee": 43.1, ...}
    network_latency_ms INT,
    current_task TEXT,
    gps_lat     FLOAT,
    gps_lon     FLOAT
);

SELECT create_hypertable('telemetry', 'time');
CREATE INDEX ON telemetry (robot_id, time DESC);

-- 自动压缩策略：7 天后的数据压缩
SELECT add_compression_policy('telemetry', INTERVAL '7 days');

-- 自动降采样策略：30 天后的数据聚合为 5 分钟窗口
SELECT add_retention_policy('telemetry', INTERVAL '30 days');
```

**查询 API**:
```
GET /api/robots/{robot_id}/telemetry/history
  ?metrics=battery_pct,cpu_pct
  &from=2025-05-01T00:00:00Z
  &to=2025-05-25T00:00:00Z
  &interval=1m          # 聚合粒度: 1s, 1m, 5m, 1h
  &compare=robot_05     # 可选：对比另一台机器人
```

TimescaleDB 的 `time_bucket()` 函数按 interval 自动聚合：
```sql
SELECT time_bucket('1 minute', time) AS bucket,
       robot_id,
       AVG(battery_pct) as avg_battery,
       AVG(cpu_pct) as avg_cpu
FROM telemetry
WHERE robot_id = 'robot_03'
  AND time BETWEEN '2025-05-01' AND '2025-05-25'
GROUP BY bucket, robot_id
ORDER BY bucket;
```

### Rationale
- **TimescaleDB over InfluxDB**: 需要 JOIN 操作（历史查询关联 robot 元数据、关联告警事件）。TimescaleDB = PostgreSQL + time-series，兼顾关系型和时序型。
- **JSONB for joint_temps**: 关节数量因机器人型号不同（有的 12 个关节，有的 20 个）。JSONB 允许灵活 schema，且 TimescaleDB 支持 JSONB 索引。
- **自动压缩 + 降采样**: 7 天内数据保持原始精度（1 秒），7-30 天压缩（不牺牲精度但节省存储），30 天后降采样到 5 分钟聚合。查询近 7 天走未压缩 chunk，加载快。

### Alternatives Rejected
- **不用 MongoDB 时序集合**: MongoDB 的时序集合功能较新（5.0+），生态和运维经验不如 TimescaleDB。SQL 查询在报表生成中优势明显。
- **不用 Elasticsearch**: ES 适合全文搜索，不适合时序聚合。对"过去 30 天每 5 分钟的平均电量"这种查询，ES 的聚合语法远不如 SQL 直观。

### Consequences
- TimescaleDB 是 PostgreSQL 扩展，团队如果已有 PostgreSQL 运维经验，学习成本低
- 1.3 亿行未压缩约 ~40GB；压缩后约 ~8GB。运维需要监控磁盘使用

---

## ADR-006: 部署架构

### Context
面板需要部署到生产环境供运维团队使用。团队规模小（2-3 名运维工程师 + 1 名主管），并发用户 < 10。

### Decision

```
                    ┌──────────────┐
                    │  Nginx (TLS) │
                    │  static SPA  │
                    │  + reverse   │
                    │  proxy       │
                    └──┬───┬───┬──┘
                       │   │   │
          ┌────────────┼───┼───┼──────────────┐
          │            │   │   │              │
          ▼            ▼   │   │              │
   ┌──────────┐  ┌─────────┴┐  │              │
   │ WS GW    │  │ REST API │  │              │
   │ (Go)     │  │ (Node)   │  │              │
   │ :8081    │  │ :3000    │  │              │
   └────┬─────┘  └────┬─────┘  │              │
        │              │        │              │
        └──────┬───────┘        │              │
               │                │              │
        ┌──────▼──────┐  ┌──────▼──────┐  ┌───▼──────────┐
        │   Kafka     │  │ PostgreSQL  │  │  TimescaleDB │
        │   :9092     │  │ :5432       │  │  :5433       │
        └──────▲──────┘  └─────────────┘  └──────────────┘
               │
        ┌──────┴──────┐
        │ Normalizer  │
        │ (Python/Go) │
        │ :8082       │
        └──────▲──────┘
               │
        ┌──────┴──────┐
        │ Ingestion   │
        │ Gateway     │
        │ :8080       │
        └─────────────┘
```

**单机部署方案**（初创团队，< 50 台机器人）:
- 全部服务通过 Docker Compose 部署在同一台机器（4 核 16GB RAM 足够）
- Nginx 提供 TLS 终止 + SPA 静态文件服务 + WebSocket 代理
- Kafka 可用 Redpanda 替代（兼容 Kafka API 但更轻量，单二进制文件）

**扩展路径**（50+ 台机器人）:
- Ingestion Gateway + Normalizer 可独立水平扩展（无状态）
- WebSocket Gateway 需 sticky session 或 Redis 做 pub/sub 桥接跨实例
- Kafka + TimescaleDB 保持单实例直到数据量突破单机容量

### Rationale
- **Docker Compose for simplicity**: Kubernetes 对 2-3 人团队运维太重。单机 Docker Compose 满足当前需求，且有迁移到 k8s 的路径（每个服务已有 Dockerfile）。
- **Redpanda over Kafka**: 减少运维负担。Kafka 需要 Zookeeper（或 KRaft），Redpanda 是单二进制。在 < 50 台机器人的吞吐量下性能差异不可感知。

---

## ADR-007: 安全与认证

### Context
面板包含机器人位置、状态、团队留言等敏感数据。需要接入现有认证系统。

### Decision
- **认证**: 假定已有 SSO（OAuth2/OIDC），面板作为 OAuth2 Client
- **Nginx 层 JWT 验证**: 所有 API 请求在 Nginx 层验证 JWT，无效 token 直接返回 401，不到达应用层
- **WebSocket 认证**: 连接时携带 token 作为 query param `?token=xxx`，WebSocket Gateway 验证后建立连接
- **API 权限**: 初期不实现细粒度 RBAC（所有登录用户均可查看所有机器人）；如需要，后期通过 middleware 添加
- **数据传输**: TLS 全链路（Robot → Gateway 走 mTLS 或 TLS + API Key）

---

## System Failure Modes

| 故障 | 影响 | 降级策略 |
|------|------|---------|
| Ingestion Gateway 宕机 | 无新数据进入 | 前端显示「数据更新于 N 秒前」；Gateway 重启后 Kafka 中的积压消息被消费恢复 |
| Kafka 宕机 | 数据管线中断 | Normalizer 缓存 5 分钟原始数据到本地磁盘；Kafka 恢复后重放 |
| Normalizer 宕机 | 归一化数据停止产出 | WebSocket 继续推送最后已知状态；卡片标记「数据可能过期」 |
| TimescaleDB 宕机 | 历史查询不可用 | 实时监控不受影响；历史曲线区域显示「历史数据暂不可用，正在恢复」 |
| WebSocket Gateway 宕机 | 实时推送中断 | 前端自动重连（指数退避 1s→2s→4s→...→max 30s）；重连时显示黄色横幅 |

---

## Completion Report

```yaml
completion_report:
  what_was_done: "完整系统架构设计：5 层管道架构、数据归一化 Adapter 模式、前端 React SPA 架构、告警引擎设计、时序存储方案、部署架构、安全方案"
  key_decisions:
    - decision: "5 层管道架构（Ingest → Normalize → Process → Serve → Present）"
      rationale: "每层职责单一可替换。Normalize 层变化不影响 Serve 层。Kafka 缓冲解耦。"
    - decision: "Adapter Registry 用声明式 YAML 而非代码"
      rationale: "运维工程师可自行添加新机型映射，不需要开发介入。一次配置 10 分钟。"
    - decision: "TimescaleDB 而非 InfluxDB"
      rationale: "需要 SQL JOIN 做报表；团队如果是 PostgreSQL 背景则学习成本为零"
    - decision: "告警引擎用规则引擎而非 ML"
      rationale: "告警条件是确定性的阈值判断。ML 带来不可解释性和误报风险。"
    - decision: "单机 Docker Compose 部署，Redpanda 替代 Kafka"
      rationale: "初创团队运维 Kubernetes 太重。Redpanda 降运维复杂度。保留扩展路径。"
  handoff_focus:
    - "senior-engineer: Ingestion Gateway + Normalizer Service 是最优先实现的微服务"
    - "api-designer: REST API 端点（历史查询 GET /api/robots/:id/telemetry/history, 配置 CRUD, 留言 CRUD）"
    - "database-engineer: TimescaleDB hypertable schema + 压缩策略"
    - "senior-frontend: 前端架构按 feature-based 目录结构 + Zustand store 设计"
    - "devops-engineer: Docker Compose 编排 + Nginx 配置 + TLS"
  open_questions:
    - "现有 SSO 系统是 OAuth2 还是 LDAP？影响认证中间件选型"
    - "机器人侧上报数据的网络环境？是否需要离线缓存 + 恢复重传？"
  known_constraints:
    - "Web 平台，非移动端"
    - "只读监控，无控制指令"
    - "并发用户 < 10"
    - "车队规模：当前 50 台，架构可扩展至 200 台不修改核心设计"
  confidence_differential: 0.05
  dissent_if_alone: null
```
