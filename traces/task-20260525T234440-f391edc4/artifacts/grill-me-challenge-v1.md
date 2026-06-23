# Grill-Me: 架构对抗性审查 — 机器人车队运维面板

> 审查对象: architect ADR v1.0 (ADR-001 到 ADR-007) | 审查者: grill-me | 审查模式: advisory

---

## Verdict: ISSUES_TO_ADDRESS (2 critical, 3 major)

架构整体方向正确，5 层管道设计合理。但以下假设存在风险，需在进入实现前解决。

---

## Critical Challenges

### C1: 异构数据归一化层假设「每种新机型只需加 YAML」

**Assumption**: 所有机器人数据源都可以通过声明式 YAML mapping 完成归一化，不需要代码级 adapter。

**Failure Condition**: 当某机型的数据需要语义级别的转换时——例如 `battery_pct` 在一种协议中表示「剩余电量百分比」，在另一种协议中表示「已消耗电量百分比」——YAML 的 `multiply(100)` 无法区分「补数」还是「倍数」。更危险的场景：Protobuf 字段使用了 `oneof` 或 `map` 类型，YAML 路径表达式无法表达。

**Severity**: CRITICAL
**Recommendation**: 在 ADR-002 中增加 Code Adapter 逃生门的设计细节。YAML adapter 覆盖 80% 场景，剩余的 20% 应允许注册 Python/Go 函数作为 adapter。例如：
```yaml
adapters:
  - id: "complex-r3"
    code_adapter: "adapters/complex_r3.py"  # implements normalize(raw) → RobotTelemetry
```

### C2: 告警引擎的「摔倒检测依靠固件判断」

**Assumption**: 机器人固件会可靠地在摔倒时发送 `status: ERROR` + `error_code: FALL_DETECTED`。

**Failure Condition**: 固件在摔倒时可能已经 crash/断电，根本发不出 `status: ERROR`。实际运维中，摔倒更可能表现为：IMU 数据突然静止（机器人躺平）+ 关节角度异常（超出运动范围）+ 最后一条心跳后无数据。完全依赖固件的 error_code 会漏掉「固件来不及上报就断电」的摔倒。

**Severity**: CRITICAL
**Recommendation**: 增加基于遥测推断的摔倒检测作为**补充规则**（不是替代）：
- 心跳超时 > 15s（已存在）→ OFFLINE
- 如果 OFFLINE 前最后一帧数据中 joint 角度出现 > 120° 的异常值 → 标记为「疑似摔倒，需人工确认」
- 这不是 ML，是额外的确定规则

---

## Major Challenges

### M1: 5 层管道架构对初创团队运维过重

**Assumption**: 2-3 人团队有能力运维 Kafka/Redpanda + TimescaleDB + PostgreSQL + Ingestion Gateway + Normalizer + WS Gateway + REST API + Nginx。

**Failure Condition**: 实际上，小团队经常低估 Kafka 的运维成本。Redpanda 简化了部署，但仍有 partition、consumer group rebalance、offset 管理等问题。当凌晨 3 点 Kafka 宕机且唯一的运维工程师在处理机器人故障时，面板自身的问题可能比机器人的问题更晚被发现。

**Severity**: MAJOR
**Recommendation**: 增加一个「最小可用模式」：Kafka 可选——Normalizer 可以直接通过 gRPC/HTTP 从 Ingestion Gateway 接收数据并同步写入 TimescaleDB + 推送到 WS Gateway。Kafka 在车队 > 20 台或需要削峰时再引入。这个简化牺牲了缓冲能力，但把自举阶段运维复杂度从 6 个服务降到 4 个。

### M2: 单机部署 + Docker Compose 假设无状态服务可以简单重启

**Assumption**: 服务崩溃后重启即可恢复，无状态服务没有任何副作用。

**Failure Condition**: Normalizer 依赖 Adapter Registry YAML 文件。如果 YAML 文件在运行时被误修改（如错误的路径表达式），Normalizer 热加载后可能开始产生大量错误数据写入 Kafka → TimescaleDB。这些**脏数据**会在下游产生误告警（字段被错误映射导致温度显示 200°C）。重启 Normalizer 不能恢复脏数据，需要回滚 TimescaleDB 或手动清理。

**Severity**: MAJOR
**Recommendation**: Adapter Registry 热加载应增加「影子模式」：新 adapter 先并行运行 5 分钟，输出与旧 adapter 对比，差异超过阈值（如 20% 字段值变化 > 50%）则拒绝切换并告警。生产数据永远走已验证的 adapter。

### M3: 报表 PDF 生成未考虑大车队超时

**Assumption**: 报表生成 < 1 分钟对 50 台机器人 30 天数据足够。

**Failure Condition**: 50 台 × 30 天 × 24h × 60min × 60s = 1.3 亿行。即使 TimescaleDB 查询只需 2 秒，PDF 渲染（Puppeteer 启动 Chrome、渲染 ECharts 图表为图片）可能需要 60-120 秒。运维主管点击「导出」后看到空白页面 2 分钟会认为系统卡死并刷新页面重试——产生多个重复的渲染任务，进一步拖垮服务。

**Severity**: MAJOR
**Recommendation**: 报表导出必须设计为**异步任务模式**。点击导出 → 创建 background job → 返回 job_id → 前端轮询（或 WebSocket 推送完成通知）→ 完成后从对象存储/临时 URL 下载。这已经在 UX spec 的 edge case 中提到，但架构 ADR 未体现为设计决策。

---

## Minor Challenges

### m1: 前端图表使用 ECharts 包体积 1MB+
**Assumption**: ECharts 按需引入可以将 bundle 降到可接受范围。
**Risk**: ECharts 的 tree-shaking 不完美，实际按需引入后仍在 600-800KB。对运维中心内网环境可能不是问题，但需要在 ADR 中标记为已知的代价。
**Severity**: MINOR

### m2: react-grid-layout 50 张卡片性能
**Assumption**: 50 张机器人卡片在同屏性能可接受。
**Risk**: react-grid-layout 对每张卡片使用绝对定位 + CSS transform，50 张卡片同时渲染 DOM 节点 > 200 个。如果每张卡片内部还有实时更新的数据（WebSocket 每秒推送），渲染频率合并成问题。需要 react-window 虚拟化或卡片折叠为非活跃状态。
**Severity**: MINOR

---

## What the Architecture Gets Right

1. **Adapter Registry 声明式设计** — 正确。运维人员可自行添加新机型是合理的成本权衡。
2. **TimescaleDB over InfluxDB** — 正确。报表需要 SQL JOIN，时序 + 关系型混合是正确选择。
3. **告警 cooldown 防抖** — 正确。5 分钟窗口在运维场景中合理。
4. **WebSocket Gateway 用 Go** — 正确。高并发长连接场景下 goroutine 是天然优势。
5. **不引入 ML** — 正确。确定性规则 > 不可解释模型。

---

## Completion Report

```yaml
completion_report:
  what_was_done: "对架构 ADR 进行对抗性审查，识别 2 个 CRITICAL、3 个 MAJOR、2 个 MINOR 问题，并记录 5 个架构正确决策"
  key_decisions:
    - decision: "摔倒检测不能仅依赖固件 error_code，需增加遥测推断补充规则"
      rationale: "固件可能在摔倒时 crash/断电，无法发出 error_code。心跳消失+最后帧 joint 异常是更可靠的信号"
    - decision: "Kafka 应可降级为直连模式以降低自举阶段运维复杂度"
      rationale: "Kafka 在车队 < 20 台时是过度工程。提供无 Kafka 的 minimal mode 降低准入门槛"
    - decision: "Adapter Registry 热加载需影子模式——新旧 adapter 并行 5 分钟验证再切换"
      rationale: "防止错误的 YAML 配置污染生产数据，造成不可恢复的脏数据和误告警"
  handoff_focus:
    - "architect: 更新 ADR-002（增加 Code Adapter 逃生门 + 影子模式）和 ADR-004（增加遥测推断摔倒检测）"
    - "devops-engineer: 设计 minimal mode（无 Kafka 部署方案）"
  open_questions:
    - "机器人固件 crash/断电的实际频率是多少？（决定是否需要遥测推断摔倒检测）"
  known_constraints:
    - "只读监控面板，不涉及机器人控制"
  confidence_differential: 0.10
  dissent_if_alone: "如果只有我一个 agent，我会更强调将 Kafka 从架构中移除作为默认选项，而非作为降级模式。消息队列对初创团队的运维负担经常被低估，且汽车队 < 50 台时直连管道完全可行。但我理解团队选择保留 Kafka 是为了扩展路径——这是一个合理的工程权衡。"
```
