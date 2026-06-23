# Issue Decomposition — 机器人车队运维监控面板 (FleetOps Dashboard)

> 来源: to-prd PRD v1.0 | 策略: Tracer-bullet 垂直切片 | 排序: 依赖优先

---

## Tracer Bullet 1: 数据管道 (必须先通)

> 目标: 让 1 台机器人的数据从网关流到前端卡片

| # | Title | Size | Depends On | Acceptance Criteria |
|---|-------|------|------------|---------------------|
| I-01 | 搭建 RobotTelemetry 统一 Schema 和 protobuf 定义 | M | none | `RobotTelemetry` 结构体编译通过；包含 robot_id, timestamp, battery_pct, joint_temps, cpu_pct, network_latency_ms, current_task, gps, status |
| I-02 | 实现数据归一化 Adapter 框架 + Mock JSON adapter | M | I-01 | 调用 `normalizer.normalize(json_bytes)` 返回标准 RobotTelemetry；输入字段名映射配置化 |
| I-03 | 搭建 Kafka 消息队列 (开发环境) | S | none | topic `robot.telemetry.raw` 和 `robot.telemetry.normalized` 可生产/消费 |
| I-04 | 实现 Normalizer Service（Kafka consumer → normalize → Kafka producer） | L | I-02, I-03 | 消费 raw topic 的消息，1s 内产出 normalized topic 消息；格式错误的原始消息进入 dead-letter topic |
| I-05 | 实现 WebSocket Gateway（消费 normalized topic → 推送前端） | L | I-03, I-04 | 浏览器连接 ws://host/telemetry，收到 JSON 格式 RobotTelemetry；连接断开 30s 内自动重连 |
| I-06 | 实现 RobotCard 前端组件（接收 WebSocket 数据渲染） | M | I-01, I-05 | 卡片显示：状态点、电量%、最高关节温度、CPU%、网络延迟、当前任务名称、告警计数 Badge |

---

## Tracer Bullet 2: 告警引擎 (核心价值)

> 目标: 机器人异常 → 告警触发 → 前端弹窗

| # | Title | Size | Depends On | Acceptance Criteria |
|---|-------|------|------------|---------------------|
| I-07 | 实现告警规则引擎（评估 RobotTelemetry → 产生 Alert 事件） | L | I-04 | 配置 threshold `battery_pct < 20` → 产出 `Alert{robot_id, severity:CRITICAL, type:BATTERY_LOW, timestamp}`；同一机器人同一类型 5 分钟内不重复发送 |
| I-08 | 实现 Alert WebSocket 通道（告警独立于遥测推送） | M | I-05, I-07 | 浏览器通过同一 WebSocket 收到 `type:alert` 消息；AlertBanner 弹窗在 2s 内出现 |
| I-09 | 实现 AlertBanner 前端组件（红色脉冲弹窗 + 声音 + 一键跳转详情） | M | I-06, I-08 | CRITICAL 告警: 红色脉冲边框 + 蜂鸣声 + 点击跳转机器人详情；WARNING 告警: 黄色高亮 + 无声音；指标恢复正常后 WARNING 自动消除，CRITICAL 需手动标记已处理 |
| I-10 | 实现告警历史列表 + 已处理标记 | M | I-07 | 列表筛选：全部/未处理/已处理；点击「已处理」→ 弹出备注框 → 保存后状态变更；显示处理人和处理时间 |

---

## Tracer Bullet 3: 总览仪表盘

> 目标: 一屏看清车队整体健康

| # | Title | Size | Depends On | Acceptance Criteria |
|---|-------|------|------------|---------------------|
| I-11 | 实现车队总览页面布局（网格 + 统计摘要） | M | I-06 | 主屏显示：顶部统计条(正常/警告/严重/离线计数) + 机器人卡片网格；异常机器人自动排在最前 |
| I-12 | 实现环形图组件（车队健康度占比） | M | I-06 | 环形图显示正常/警告/严重/离线四类占比，支持点击分类下钻 |
| I-13 | 实现折线图组件（近 1 小时趋势） | M | I-06 | 折线图显示选定指标(电量/温度/CPU)过去 1 小时的变化；支持多机器人对比 |
| I-14 | 实现地理热力图组件 | L | I-06 | 地图上以颜色密度显示机器人分布；点击热点区域筛选该区域机器人列表 |

---

## Tracer Bullet 4: 机器人详情 & 历史

> 目标: 单机深度诊断

| # | Title | Size | Depends On | Acceptance Criteria |
|---|-------|------|------------|---------------------|
| I-15 | 实现 RobotDetailPanel（遥测面板 + 所有指标） | L | I-06 | 展开显示：所有关节温度、CPU 历史峰值、网络抖动、GPS 坐标；异常指标红色高亮 |
| I-16 | 搭建时序数据库（InfluxDB/TimescaleDB） | L | I-04 | normalized 数据写入 TSDB；查询 robot_id + 时间范围 + 指标 < 2s 返回 |
| I-17 | 实现 30 天历史曲线组件（多指标 + 缩放 + 对比） | L | I-15, I-16 | 支持时间范围拖选、指标切换(电量/温度/CPU)、双机器人叠图对比；30 天数据查询 < 2s |

---

## Tracer Bullet 5: 协作 & 认领

> 目标: 避免重复响应

| # | Title | Size | Depends On | Acceptance Criteria |
|---|-------|------|------------|---------------------|
| I-18 | 实现留言系统后端（CRUD + @mention 解析） | M | none | POST /api/robots/{id}/comments 创建留言；@格式识别为 mention；GET 返回留言列表含时间戳和作者 |
| I-19 | 实现 CommentThread 前端组件（留言列表 + 输入框 + @mention 自动补全） | M | I-15, I-18 | 留言显示作者/时间/内容；输入 @ 弹出同事列表自动补全；支持回车发送 |
| I-20 | 实现 ClaimButton 组件（「我在处理」+ 超时释放） | S | I-18 | 点击认领 → 按钮变灰显示「李梅正在处理」；30 分钟无操作自动释放；第二人点击看到「已被认领」提示 |

---

## Tracer Bullet 6: 配置管理

> 目标: 工程师按机器人定制参数

| # | Title | Size | Depends On | Acceptance Criteria |
|---|-------|------|------------|---------------------|
| I-21 | 实现配置存储后端（per-robot config CRUD） | M | none | CRUD API for robot config: {alert_thresholds, sample_frequency_ms, reconnect_strategy}；多机器人批量更新 |
| I-22 | 实现 ThresholdSlider 组件 + ConfigForm | M | I-15, I-21 | 阈值滑块显示当前值和默认值参考线；采样频率下拉选择；重连策略选择；保存后 5s 内生效 |
| I-23 | 实现批量配置操作（多选机器人 → 统一修改） | M | I-21, I-22 | 勾选多台机器人 → 批量修改阈值/频率/策略；显示变更预览 → 确认 → 应用 |

---

## Tracer Bullet 7: 报表 & 导出

> 目标: 周期性报告生成

| # | Title | Size | Depends On | Acceptance Criteria |
|---|-------|------|------------|---------------------|
| I-24 | 实现 PDF 报表生成服务（服务端渲染） | L | I-16 | 选择时间范围 + 机器人 → 生成 PDF 含可用率统计、告警 Top 5、电量趋势图；生成时间 < 1min |
| I-25 | 实现 Excel 数据导出 | M | I-16 | 导出原始遥测数据为 .xlsx；列: 时间/机器人/指标/值；支持筛选列 |
| I-26 | 实现 ExportDialog 前端组件 | S | I-24, I-25 | 弹出对话框: 时间范围预设(今天/昨天/本周/上周/过去30天/自定义) + 格式选择(PDF/Excel) + 机器人多选；异步生成时显示进度 |

---

## Tracer Bullet 8: 个性化 & 主题

> 目标: 适配工作环境和偏好

| # | Title | Size | Depends On | Acceptance Criteria |
|---|-------|------|------------|---------------------|
| I-27 | 实现暗色/亮色主题系统（CSS Variables + 全局切换） | L | I-11 | 暗色: 深色底 + 高对比度文字 + 图表暗色色板；亮色: 浅色底 + 柔和色；切换动画 300ms；刷新后保持选择 |
| I-28 | 实现国际化框架（react-i18next + 中/英双语） | L | none (可并行) | 所有 UI 文案 key 化；语言切换即时生效；数字格式本地化 |
| I-29 | 实现可拖拽布局（react-grid-layout + 预设模板） | L | I-11 | 3 种预设模板(标准3列/宽屏4列/紧凑2列)；拖拽卡片调整位置和大小；布局保存到 localStorage；刷新恢复；「重置布局」按钮 |

---

## Dependency Graph (简化)

```
I-01 ──► I-02 ──► I-04 ──► I-05 ──► I-06 ──► I-11 ──► I-27, I-29
                 │          │          │
I-03 ────────────┘          │          ├──► I-12, I-13, I-14
                            │          │
                      I-07 ─┘          ├──► I-15 ──► I-17, I-19
                            │          │         │
                      I-08 ─┘          │    I-16 ─┘
                            │          │         │
                      I-09 ─┘          │    I-24, I-25 ──► I-26
                            │          │
                      I-10 ─┘          │
                                       │
I-18 ──► I-19, I-20                    │
I-21 ──► I-22 ──► I-23                 │
I-28 (并行)                             │
```

---

## Completion Report

```yaml
completion_report:
  what_was_done: "将 PRD 19 条 user stories 分解为 29 个独立可交付问题，按 8 条 tracer-bullet 垂直切片组织"
  key_decisions:
    - decision: "Tracer Bullet 1 (数据管道) 作为第一条切片，必须先通"
      rationale: "数据是面板的血液。没有实时数据流，后续所有功能都是 mock。先让 1 台机器人的数据完整走通全链路"
    - decision: "I-28 (国际化) 标记为可并行"
      rationale: "i18n 是纯前端工作，不依赖任何后端服务，可与数据管道并行"
    - decision: "每个 issue 不超过 L 规模（~1 天工作量），超过则进一步拆分"
      rationale: "超出 1 天的 issue 会阻塞其他工作"
  handoff_focus:
    - "senior-engineer: Tracer Bullet 1 (I-01 到 I-06) 是最优先实现路径"
    - "tdd: I-04 (Normalizer Service) 和 I-07 (告警引擎) 是测试重点"
  open_questions: []
  known_constraints:
    - "总共 29 个 issue，预计 2 名全栈工程师 4-6 周完成"
  confidence_differential: 0.0
  dissent_if_alone: null
```
