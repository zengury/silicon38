# PRD: 机器人车队运维监控面板 (Robot Fleet Ops Dashboard)

---

## Problem Statement

运维工程师管理一支人形机器人车队时面临六个核心痛点：

1. **数据不可见** — 每台机器人的实时状态（电量、关节温度、CPU、网络延迟、当前任务、GPS）分散在不同系统或完全不可见，出问题只能等机器人自己报错或人工巡检。
2. **数据格式混乱** — 机器人回传数据格式不统一（有的 JSON、有的 Protobuf 转），字段名、单位各不一样，归一化处理全靠工程师手动脚本。
3. **缺乏全局视角** — 没有车队级健康度聚合视图，无法快速回答"车队整体是否健康"。
4. **告警不及时** — 机器人摔倒、关节失联、电量过低等异常状态无主动推送，依赖工程师轮询发现。
5. **历史不可追溯** — 无法回溯过去 30 天的状态曲线，排查问题只能看当前快照。
6. **协同靠吼** — 多位工程师同时运维，缺少在面板内的协同机制（留言、@同事、标记处理者），沟通发生在微信/钉钉而非工作台。

## Solution

一个 Web 运维监控面板，将数据归一化、实时推送、告警、历史、协同、配置和导出整合为一个工作台。

核心链路：
```
机器人 → 边缘网关 → 消息队列 → 归一化引擎 → 时序数据库
                                              ↓
                                        WebSocket Hub
                                              ↓
                                         浏览器面板
```

### 模块划分

| 模块 | 职责 | 深度 |
|---|---|---|
| **Data Ingest & Normalize** | 接收异构数据 → 统一 Schema → 写入 TSDB | Deep — 简单接口，复杂内部（协议适配、单位换算、字段映射） |
| **Real-time Push Hub** | TSDB 变更事件 → WebSocket → 前端订阅 | Shallow — 事件转发 |
| **Alert Engine** | 规则评估 → 告警生成 → 通知分发 | Deep — 规则 DSL + 状态机 + 去重/升级 |
| **History Service** | 时序查询 + 降采样聚合 | Shallow — TSDB 查询代理 |
| **Config Service** | 每机器人配置 CRUD → 下发至边缘网关 | Moderate |
| **Collaboration Service** | 评论线程 + @提及 + 状态标记 | Shallow |
| **Report Engine** | 快照聚合 → PDF/Excel 渲染 | Moderate |
| **Shell (Frontend)** | 主题/i18n/布局/路由 | Thin shell — 核心逻辑在各模块 |

## User Stories

### 实时监控 (Real-time Monitoring)

1. 作为运维工程师，我想在仪表盘上看到所有机器人的实时状态卡片（电量、关节温度、CPU、网络延迟、当前任务、GPS），以便快速判断哪些机器人需要关注。
2. 作为运维工程师，我想看到每台机器人的连接状态（在线/离线/异常），以便知道是数据延迟还是机器人真的掉线。
3. 作为运维工程师，我想点击任意机器人卡片进入详情页，查看该机器人的完整六维数据面板和更大的地图视图。
4. 作为运维工程师，当地图上有 10+ 台机器人时，我想自动聚合临近机器人，放大地图时解散聚合，以便不被标记覆盖。
5. 作为运维工程师，我想让实时数据以 ≤2 秒延迟刷新，以便及时发现状态变化。

### 异构数据归一化 (Heterogeneous Data)

6. 作为运维工程师，我不想关心机器人回传的是 JSON 还是 Protobuf——面板上所有数据应统一展示，字段名和单位自动转换。
7. 作为系统管理员，当新机器人型号加入车队时，我希望能通过配置文件（而非改代码）添加其数据映射规则。
8. 作为运维工程师，我想在数据字段旁边看到原始值提示（tooltip 显示 "原始字段: batt_pct, 原始值: 0.87→转换为 87%"），以便信任归一化结果。

### 车队总览 (Fleet Overview)

9. 作为运维工程师，我想在总览页看到环形图（在线/离线/异常比例）、折线图（过去 1 小时平均电量/CPU 趋势）、热力图（按地理位置分布的车队健康度），以便 10 秒内判断车队整体状态。
10. 作为运维工程师，我想自定义总览仪表盘的时间窗口（1h / 6h / 24h / 7d），图表自动刷新。
11. 作为运维工程师，我想在环形图上点击"异常"扇区直接跳转到异常机器人列表。

### 告警 (Alerts)

12. 作为运维工程师，当机器人摔倒时，我想立即收到页面弹窗 + 声音告警，告警信息包含机器人 ID、时间、GPS 坐标。
13. 作为运维工程师，当关节失联或电量低于阈值时，我想看到告警列表（支持按严重程度/时间/机器人过滤）。
14. 作为运维工程师，我想对告警执行：确认（表示我知道）、静音（该告警类型 5 分钟内不再响）、关闭（问题已解决）。
15. 作为运维工程师，同一告警在 30 秒内不应重复弹窗（去重）。

### 历史曲线 (History)

16. 作为运维工程师，我想到任意机器人详情页，选择过去 30 天内的任意时间窗口，查看电量/温度/CPU/延迟的时间序列曲线。
17. 作为运维工程师，我想在曲线上缩放、平移、对比两台机器人的同类指标。
18. 作为运维工程师，当数据因网络断连出现缺口时，曲线应显示断点标记而非错误连接。

### 配置面板 (Configuration)

19. 作为运维工程师，我想在配置面板为每台机器人设置告警阈值（电量 <X%、温度 >Y°C、延迟 >Zms）。
20. 作为运维工程师，我想调整每台机器人的采样频率（1s/5s/10s/30s），并在机器人电量过低时自动降频。
21. 作为运维工程师，我想配置重连策略：最大重试次数、退避策略（固定/指数）、心跳超时。
22. 作为运维工程师，配置更改后应在面板上显示同步状态（已下发/下发中/下发失败）。

### 协同运维 (Collaboration)

23. 作为运维工程师，我想在任意机器人详情页下方看到评论区，发表文字评论。
24. 作为运维工程师，我想在评论中 @同事名字，被 @ 的同事收到通知。
25. 作为运维工程师，我想点击"我在处理"按钮标记该机器人为自己的处理任务，其他同事看到标记后避免冲突。
26. 作为运维工程师，我想看到每条评论的时间戳和作者，以及该机器人的当前处理者。

### 报表导出 (Reports)

27. 作为运维工程师，我想选择任意时间范围和机器人范围，导出车队健康报告（PDF），包含总览图、告警摘要、关键指标统计。
28. 作为运维工程师，我想导出原始时序数据为 Excel (.xlsx)，以便在外部工具中进一步分析。
29. 作为运维工程师，导出不应阻塞面板操作——导出任务后台执行，完成后通知下载。

### 个性化 (Customization)

30. 作为运维工程师，我想在暗色主题和亮色主题之间切换，面板即时生效。
31. 作为运维工程师，我想切换面板语言（至少中文/英文），所有文案、单位、日期格式自动切换。
32. 作为运维工程师，我想拖拽仪表盘上的组件（卡片、图表）到任意位置，布局自动保存到我的账号。

## Implementation Decisions

### 技术栈

| 层 | 选型 | 理由 |
|---|---|---|
| 前端框架 | React 18 + TypeScript | 生态成熟，组件化适合仪表盘 |
| 状态管理 | Zustand + React Query | 轻量、实时状态 + 服务端缓存分离 |
| 图表库 | ECharts / Recharts | 环形图、折线图、热力图全面覆盖 |
| 地图 | Mapbox GL JS / Leaflet | 机器人 GPS 可视化 |
| 实时通信 | WebSocket (Socket.IO) | 双向推送，自动重连 |
| 拖拽布局 | react-grid-layout | 成熟的可持久化网格布局 |
| 主题 | CSS Variables + Tailwind dark mode | 运行时切换，零重建 |
| i18n | react-i18next | 命名空间隔离，动态加载 |
| BFF | Node.js (Fastify) + TypeScript | 高性能、Schema-first |
| 数据归一化 | 独立 Go/Rust 微服务 或 Node.js Stream | 高吞吐解析 + 转换 |
| 消息队列 | Redis Streams / NATS | 轻量，适合 IoT 数据 |
| 时序数据库 | TimescaleDB / InfluxDB | 时序专用，降采样、连续聚合 |
| 关系数据库 | PostgreSQL | 配置、用户、评论、告警 |
| 告警引擎 | 嵌入式规则引擎（JSONLogic / 自研） | 每个数据点评估，无需外部依赖 |
| 报表 | Puppeteer (PDF) + ExcelJS (Excel) | 服务端渲染 |
| 部署 | Docker Compose → K8s | 渐进式 |

### 数据归一化 Schema（核心深度模块）

```yaml
# 统一数据模型 — 所有异构源归一化到此 Schema
RobotTelemetry:
  robot_id: string           # 不可变
  timestamp: ISO8601         # 采集时刻
  source_protocol: enum      # json | protobuf | mqtt_raw
  source_raw: blob           # 原始报文（保留用于审计）
  mapping_rule_id: string    # 使用的映射规则版本

  battery:
    level_pct: float         # 0-100, 归一化后
    voltage_v: float | null
    current_a: float | null
    temperature_c: float | null

  joints:
    - joint_id: string
      temperature_c: float
      torque_nm: float | null
      angle_deg: float | null
      status: enum           # nominal | warm | hot | lost

  compute:
    cpu_pct: float           # 0-100
    memory_pct: float        # 0-100
    disk_free_gb: float | null

  network:
    latency_ms: float
    rssi_dbm: float | null
    packet_loss_pct: float | null

  task:
    task_id: string | null
    task_name: string | null
    progress_pct: float | null
    status: enum             # idle | executing | paused | error

  location:
    lat: float
    lon: float
    alt_m: float | null
    accuracy_m: float | null

  anomalies:
    - type: enum             # fallen | joint_lost | battery_critical | ...
      severity: enum         # warning | critical | emergency
      detected_at: ISO8601
      detail: string
```

### 映射规则配置示例

```yaml
# 新机器人型号只需添加映射规则，不改代码
mapping_rules:
  - rule_id: "humanoid-v3-json"
    protocol: json
    field_map:
      "battery.level_pct": { source: "$.bat.pct", transform: "multiply(100)" }
      "battery.voltage_v": { source: "$.bat.v" }
      "joints[*].temperature_c": { source: "$.servos[*].temp", transform: "celsius" }
      "compute.cpu_pct": { source: "$.sys.cpu" }
      "network.latency_ms": { source: "$.conn.ping" }
      "location.lat": { source: "$.gps.latitude" }
      "location.lon": { source: "$.gps.longitude" }
    unit_conversions:
      "temperature_c": { from: "fahrenheit", fn: "(v-32)*5/9" }
      "voltage_v": { from: "millivolt", fn: "v/1000" }
```

### API 契约

```
# REST
GET    /api/v1/robots                    # 车队列表 + 实时快照
GET    /api/v1/robots/:id                # 单机器人详情
GET    /api/v1/robots/:id/telemetry      # 时序数据查询 (range, interval)
GET    /api/v1/robots/:id/config         # 机器人配置
PUT    /api/v1/robots/:id/config         # 更新配置
GET    /api/v1/fleet/overview            # 车队聚合 (环形/折线/热力)
GET    /api/v1/alerts                    # 告警列表 (filterable)
POST   /api/v1/alerts/:id/ack            # 确认告警
POST   /api/v1/alerts/:id/close          # 关闭告警
GET    /api/v1/robots/:id/comments       # 评论列表
POST   /api/v1/robots/:id/comments       # 发表评论
POST   /api/v1/robots/:id/claim          # 标记"我在处理"
DELETE /api/v1/robots/:id/claim          # 取消标记
POST   /api/v1/reports/pdf               # 生成 PDF 报表
POST   /api/v1/reports/excel             # 生成 Excel 报表
GET    /api/v1/reports/:id/status        # 查询报表生成状态

# WebSocket
WS     /ws/fleet                         # 车队实时数据流
  → event: robot_telemetry               # 每次数据归一化后推送
  → event: alert_fired                   # 告警触发
  → event: robot_online_status           # 上下线事件
```

### 告警规则 DSL

```yaml
rules:
  - alert_id: "battery_critical"
    description: "电量过低"
    condition:
      and:
        - { field: "battery.level_pct", op: "lt", value: "{{threshold}}" }
        - { field: "task.status", op: "neq", value: "idle" }
    severity: critical
    cooldown_seconds: 30

  - alert_id: "joint_lost"
    condition:
      any:  # any joint matches
        - field: "joints[*].status"
          op: "eq"
          value: "lost"
    severity: emergency
    cooldown_seconds: 10

  - alert_id: "robot_fallen"
    condition:
      field: "anomalies[*].type"
      op: "contains"
      value: "fallen"
    severity: emergency
    cooldown_seconds: 0  # no cooldown for falls
```

## Testing Decisions

**测试原则**: 只测外部行为，不测实现细节。接口是契约。

| 模块 | 测试策略 | 关键用例 |
|---|---|---|
| Data Normalizer | 单元测试 — 每种协议 + 每个映射规则 | 输入 {batt_pct: 0.87} → 输出 battery.level_pct: 87 |
| Alert Engine | 单元测试 — 每条规则正/反/边界 | 电量 20% 触发、电量 21% 不触发、冷却期内不重复 |
| REST API | 集成测试 — 每个 endpoint 的 happy path + error | 200 OK / 404 / 422 / 429 |
| WebSocket | 集成测试 — 连接/断连/重连/事件推送 | 新数据到达时已连接客户端收到事件 |
| UI 组件 | 组件测试 — 渲染 + 交互 | 环形图渲染正确颜色、拖拽保存布局 |
| 报表导出 | E2E — PDF/Excel 内容验证 | 导出文件包含正确的数据行数、图表截图 |
| 性能 | 负载测试 — 100 台机器人 × 1s 采样 | 归一化延迟 < 50ms、WS 推送延迟 < 200ms |

## Out of Scope

- 机器人固件更新 / OTA
- 移动端 App（仅 Web）
- 预测性维护 ML 模型
- 完整 IM 系统（仅评论线程 + @mention）
- 第三方工单系统集成（Jira / PagerDuty）
- SSO / LDAP / OIDC（预留接口，v1 用本地账号 + JWT）
- 多租户 / 组织架构
- 视频流 / 机器人摄像头画面
- 语音告警（仅浏览器声音）

## Further Notes

- 归一化引擎是核心竞争力。建议作为独立服务部署，允许水平扩展。映射规则支持热加载。
- 告警冷却时间、去重窗口、升级策略应在 v1 就做扎实——运维系统最怕告警风暴。
- 协同功能保持轻量。评论是 JSON blob 存在 PostgreSQL，不需要引入专门的协作引擎。
- 主题和 i18n 用 token 化方式：所有颜色/间距/圆角/etc 定义为 CSS custom properties，切换时只换 root class。
