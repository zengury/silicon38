# PRD: Robot Fleet Operations Dashboard

## Problem Statement

运维工程师管理一支人形机器人车队时，缺乏统一面板来实时监控每台机器人的健康状态。当前痛点：
- 不同机器人回传的数据格式不统一（JSON / Protobuf 衍生格式，字段名和单位各异）
- 异常事件（摔倒、关节失联、电量过低）依靠人工巡检，响应滞后
- 历史数据回溯需要手动拼接日志
- 团队协作碎片化（群聊、口头交接），无统一上下文
- 报表生成依赖手动导出拼接

需要一个 Web 端统一运维监控面板，覆盖实时监控、告警、历史回溯、配置管理、团队协作、报表导出全闭环。

## Solution

Web 端车队运维面板，核心链路：**异构数据归一化 → 实时推送 → 告警引擎 → 多维度可视化 → 协作 → 导出**。Demo 阶段完成核心链路跑通 + 关键界面。

## User Stories

### 实时监控
1. 作为运维工程师，我想要在一屏内看到所有机器人的在线状态卡片，以便快速定位离线或异常机器人。
2. 作为运维工程师，我想要看到每台机器人的电量百分比、关节温度、CPU 使用率、网络延迟、当前执行任务和地理位置，以便判断是否需要干预。
3. 作为运维工程师，我想要数据自动刷新（WebSocket 推送），以便不需要手动刷新页面。
4. 作为运维工程师，我想要点击某台机器人卡片进入详情页，展示更完整的传感器数据和状态机，以便深入排查。

### 总览仪表盘
5. 作为运维工程师，我想要一个总览仪表盘，用环形图展示车队在线率/离线率，以便一眼判断整体可用性。
6. 作为运维工程师，我想要折线图展示过去 1 小时车队平均电量/温度趋势，以便发现异常漂移。
7. 作为运维工程师，我想要热力图展示各机器人各关节温度分布，以便定位热点机器人。
8. 作为运维工程师，我想要地图视图显示各机器人的地理位置，以便了解空间分布。

### 告警
9. 作为运维工程师，我想要机器人摔倒时自动告警通知（声音 + 视觉高亮），以便第一时间响应。
10. 作为运维工程师，我想要关节通信失联时触发告警，以便排查硬件故障。
11. 作为运维工程师，我想要电量低于阈值时告警，以便安排充电。
12. 作为运维工程师，我想要告警分级（严重/警告/信息），以便按优先级处理。
13. 作为运维工程师，我想要告警可确认/静音/归档，以便管理告警生命周期。

### 历史数据
14. 作为运维工程师，我想要查看某台机器人过去 30 天内任意指标的变化曲线（温度、电量、CPU），以便分析趋势。
15. 作为运维工程师，我想要在历史曲线上缩放时间范围（1h / 6h / 24h / 7d / 30d），以便快速定位异常时段。

### 配置管理
16. 作为运维工程师，我想要调整每台机器人的告警阈值（温度上限、电量下限、延迟上限），以便适应不同环境。
17. 作为运维工程师，我想要调整采样频率（1s / 5s / 10s / 30s），以便平衡数据精度和带宽。
18. 作为运维工程师，我想要配置断线重连策略（重试次数、重试间隔、超时时间），以便适配弱网环境。

### 协作
19. 作为运维工程师，我想要在具体机器人下留言评论，以便记录处理过程。
20. 作为运维工程师，我想要 @同事 通知他们关注某台机器人，以便高效协作。
21. 作为运维工程师，我想要标记"我在处理"来声明 ownership，以便避免重复工作。

### 报表导出
22. 作为运维工程师，我想要导出某台机器人过去一段时间的状态报表为 PDF，以便汇报。
23. 作为运维工程师，我想要导出车队健康度汇总为 Excel，以便数据分析。

### 体验
24. 作为运维工程师，我想要切换暗色/亮色主题，以便适应不同光照环境。
25. 作为运维工程师，我想要面板支持中/英文切换，以便国际化团队使用。
26. 作为运维工程师，我想要自定义面板布局（拖拽卡片位置），以便按自己的习惯组织信息。

## Implementation Decisions

### 架构决策
1. **前端框架**：React 18 + TypeScript。状态管理用 Zustand（轻量、适合实时数据流）。
2. **数据可视化**：Recharts（折线图/环形图/热力图） + Leaflet（地图）。
3. **实时通信**：WebSocket 连接后端推送层，前端用自定义 useWebSocket hook 订阅。
4. **主题系统**：CSS Variables + Tailwind CSS 暗色模式。设计 Token 集中管理。
5. **国际化**：react-i18next，中/英双语。
6. **拖拽布局**：react-grid-layout。
7. **报表导出**：Demo 阶段前端导出 CSV（PapaParse），PDF 用浏览器打印；服务端 PDF 渲染留接口。

### 数据架构决策
8. **数据归一化层（核心模块）**：Schema Registry + Adapter 模式。每种机器人格式对应一个 Adapter，将异构字段映射到统一 `RobotTelemetry` schema。Adapter 负责：字段名重命名、单位转换、缺失字段默认值填充。
9. **统一 Schema**：`RobotTelemetry { robotId, timestamp, battery: {level, voltage, temperature}, joints: [{name, temperature, torque, velocity}], cpu: {usage, temperature}, network: {latency, rssi}, task: {id, name, progress}, location: {lat, lng, alt}, status: ONLINE|OFFLINE|ERROR }`
10. **时序存储（Demo 简化）**：客户端内存维护滑动窗口（最近 1000 条），模拟 30 天历史由预生成的 mock 数据提供。生产环境迁移到 InfluxDB/TimescaleDB。
11. **告警引擎**：规则定义 `{ metric, operator, threshold, severity }`，每收到一条遥测数据即评估。告警去重：同一机器+同一告警类型 5 分钟内不重复。
12. **状态管理**：全局 store 结构：`{ robots: Map<id, RobotState>, alerts: Alert[], config: RobotConfig[], ui: { theme, language, layout } }`

### 模块划分
13. **核心模块（Deep Modules）**：
    - `DataNormalizer`：Schema Registry + Adapter 注册 + 归一化管道。接口：`normalize(raw: unknown, format: string): RobotTelemetry`
    - `AlertEngine`：规则评估 + 去重 + 生命周期管理。接口：`evaluate(telemetry: RobotTelemetry): Alert[]`
    - `WebSocketManager`：连接管理 + 自动重连 + 消息分发。接口：`subscribe(topic, handler), unsubscribe(topic)`
14. **UI 模块**：
    - `DashboardOverview`：总览仪表盘（环形图/折线图/热力图/地图）
    - `RobotCard`：单机器人状态卡片
    - `RobotDetail`：机器人详情面板（传感器数据表 + 状态机 + 历史曲线）
    - `AlertPanel`：告警列表 + 确认/静音操作
    - `ConfigPanel`：配置表单（阈值/频率/重连策略）
    - `CollaborationPanel`：留言 + @提及 + 状态标记
    - `LayoutShell`：暗/亮主题 + 语言切换 + 拖拽布局容器

## Testing Decisions

1. **测试策略**：优先测试核心 Deep Modules（DataNormalizer, AlertEngine），UI 组件做 smoke test。
2. **DataNormalizer 测试**：给定不同格式的 raw 数据（JSON mock + Protobuf JSON mock），验证输出 RobotTelemetry 字段完整性和单位正确性。
3. **AlertEngine 测试**：给定边界值遥测数据，验证告警触发/不触发规则正确性；验证去重逻辑。
4. **UI 测试**：RobotCard 渲染测试（各状态颜色），AlertPanel 告警确认流程。
5. **参照**：项目为 greenfield，无既有测试参照。使用 Vitest + React Testing Library。

## Out of Scope

- 机器人端数据采集/固件改动
- 生产部署 CI/CD 流水线
- 完整 RBAC 权限系统（Demo 无登录）
- 移动端适配
- 机器人远程控制（只读监控）
- 多租户/组织管理
- 第三方系统集成（PagerDuty、Slack webhook 等）
- 服务端 PDF 渲染（Demo 用浏览器打印）
- 完整 i18n 翻译（Demo 只做中/英框架，文案不全翻译）

## Success Criteria

1. Demo 可展示：6 台模拟机器人卡片 + 总览仪表盘 + 告警触发动画
2. 数据归一化器能接收 3 种不同格式（JSON A / JSON B / Protobuf-like），统一为 RobotTelemetry
3. 告警引擎在摔倒/关节失联/低电量场景下 1 秒内触发告警通知
4. 历史曲线能展示过去 30 天 mock 数据并支持时间范围缩放
5. 暗色/亮色主题切换即时生效
6. 配置面板修改阈值后告警行为立即更新
7. 留言和 @ 功能在机器人详情下可用
