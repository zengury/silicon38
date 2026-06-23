# Graph Topologist v2 — 四层控制模型评估

**纠正：** 图不是声明式的装饰。Policy 控制合法性，Ledger 记录事实，
Runtime 执行合法动作，Learning 基于结果更新。81% 的边未激活不是 bloat——
是 Policy 在工作。问题在于四个控制层之间的协同失衡。

---

## Layer 1: Policy — 合法性解释器

### 当前状态

Policy 正确地阻止了大量非法激活。17 个任务中零次 Layer 违规——
这是 v1 的 `encoder_correction` + `activation_rollback` 之后建立的纪律在生效。

### Policy 做对了什么

- **Layer 依赖严格执行。** v2/v3 从未出现 Layer 2 在 Layer 1 之前激活。
- **触发条件被正确评估。** `may_trigger` 的条件检查阻止了不相关的边激活。
- **Context compression report 的 schema 校验。** v3 的四份报告全部通过。

### Policy 做错了什么

| 问题 | 证据 | 根因 |
|------|------|------|
| **skip 可以越过 blocking eval** | FleetOps v3: tdd 是 blocking=required，但被 skip，convergence 的 `all_blocking_evals_resolved` 永远 false——但 `deliver` 不检查这个 gate | Policy 在 convergence 和 deliver 之间有不一致的 gate 检查 |
| **task_type 没有影响 skip 合法性** | grill-me 在 design 任务和 refactor 任务上都可以被 skip。Policy 不区分：对某些 task_type，某些 evaluator 的 skip 应该被拒绝 | Policy 缺少 task_type → 强制 evaluator 的映射 |
| **Soul 对齐未进入 Policy** | `carries_soul: true` 是 node 属性，但 Policy 不检查 soul-bearing node 的 handoff 是否包含 `soul_ref`。Handoff 可能缺 soul_ref 而 Policy 不拒绝 | Policy 不验证 soul_ref 的存在性 |

### Policy 诊断

**Policy 是正确的——但它保护的是一个不完整的规则集。** 它不像一个成熟的法律体系，更像一部只有刑法没有民法的法典。它知道什么是非法激活，但不知道什么是必须激活。

---

## Layer 2: Ledger — 事实记录器

### 当前状态

Ledger 在 v3 达到了最佳状态。所有事件有结构、handoff 有 digest、artifact 有 provenance。

### Ledger 做对了什么

- **事件完整性。** v3: 31 events，覆盖 activation、skip、context_report、completion、delivery。v2 的 62 events 多但不如 v3 精准。
- **Context chain。** v3 首次实现了 digest-linked context_block 链——4 个 handoff 全部带 digest。v1/v2 的 handoff 无此能力。
- **追溯性。** 三版 FleetOps 的痕迹都可以被 graph-topologist 完整读取和分析。

### Ledger 做错了什么

| 问题 | 证据 |
|------|------|
| **skip 理由的深度不一致** | v3 的 skip 理由（"Demo 阶段，不需生产级 TDD"）vs v1 的 skip——v1 甚至没有 skip 事件，只是无声中断。Ledger 没有拒绝不充分的 skip 理由。 |
| **runtime_fallback 从未被使用** | FleetOps v3 的 senior-engineer 其实是 Runtime 自己执行的（没有 subagent）。但 Ledger 没有 `runtime_fallback` 事件。符合 RUNTIME.md 的"If the user has not configured org/models.local.yaml, run the node on the Runtime's current/default model"——但这不是 subagent 执行。Ledger 在真相和记录之间有一个模糊地带。 |
| **quality_signal 始终是 1.0** | 每次 success 交付的 quality_signal 都是 1.0。但 FleetOps v3 首屏白屏——这个 1.0 是不诚实的。Ledger 记录了交付成功但没有记录交付质量。 |

### Ledger 诊断

**Ledger 是四个层中最健康的。** 记录真实、可追溯。但它记录的是"发生了什么"，不是"好不好"。quality_signal 被硬编码为 1.0——这需要 Learning 层来纠正。

---

## Layer 3: Runtime — 执行器

### 当前状态

Runtime 稳定执行了 17 个任务，10 个成功。但任务的"执行"方式有结构性偏差。

### Runtime 做对了什么

- **收敛检测。** 尽管 v3 的 `all_blocking_evals_resolved` 是 false，Runtime 正确地通过 `deliver` 而非 `converge` 完成了任务——因为 `deliver` 的检查项不同。
- **并行激活。** to-issues 和 architect 正确并行运行。
- **Fallback 纪律。** 当 skill 无法作为 subagent 运行时，Runtime 自己执行——这是文档允许的行为。

### Runtime 做错了什么

| 问题 | 证据 | 根因 |
|------|------|------|
| **跳过质量门成为习惯** | 3/3 FleetOps 任务都跳过了至少一个 evaluator。v3 跳过了 10 个节点。Runtime 选择"跳过"的阈值太低 | Runtime 的默认策略是"有理由就允许跳过"而非"除非有充分理由否则不跳过" |
| **设计集群从未被激活** | 17 个任务中，没有一次走通了 ux→ui→frontend 的完整设计链路。Runtime 每次都选择了跳过设计节点 | Runtime 的调度偏向"能快速完成的路径" |
| **Soul 没有在决策中体现** | Phase 0.4 要求 Runtime 加载 soul 并注入 handoff——但 grill-me 的 skip 决策没有考虑 soul 损失 | Soul 被当作一个 handoff 字段，而不是一个决策约束 |

### Runtime 诊断

**Runtime 是高效的执行器，但不是明智的决策者。** 它在"完成任务的成本"上优化得很好（跳过昂贵的 evaluator ，快速交付），但在"不完成任务的成本"上缺乏评估（Soul 退化、技术债务、不可用的交付物）。

---

## Layer 4: Learning — 反馈层

### 当前状态

Learning 是最薄弱的层。它存在——`tools/ledger.py weights` 会更新边的权重，`index_by_role.yaml` 会记录 quality_contribution。但它**不会改变 Runtime 的行为**。

### Learning 做对了什么

- **权重更新。** 每次 `deliver` 后自动运行 `weights` 命令。
- **角色级质量跟踪。** `index_by_role.yaml` 记录了每个 role 的 outcome 和 quality_contribution。
- **关系级信号。** `index_by_relation.yaml` 记录了 `to-prd→to-issues/triggers` 等边的 signal。

### Learning 做错了什么

| 问题 | 证据 | 严重度 |
|------|------|--------|
| **Learning 的输出没有反馈到 Policy** | `weights` 更新了边的 probability，但 Policy 不使用这些权重来做 skip 合法性判断。如果一条边的 probability 从 0.50 降到 0.20——Runtime 仍然可以手动激活它。 | 🔴 关键 |
| **Learning 没有检测到 soul 退化** | 三轮 FleetOps，soul 从有（v2 有 UX designer）到无（v3 跳过设计集群）。Learning 应该检测到 `carries_soul: true` 的节点的激活率在下降并告警——但没有任何指标追踪这个。 | 🔴 关键 |
| **quality_signal 始终 1.0，Learning 没有纠正** | 如果 Ledger 记录的 quality 不可信，Learning 的所有下游分析都基于错误数据。Learning 应该有自己的独立质量信号。 | 🟡 重要 |
| **跨任务模式未被消费** | graph-topologist 产出了"死节点""过度跳过""从未触发"的分析——但没有任何机制把这些分析变成 Policy 更新或 Runtime 行为改变 | 🔴 关键 |
| **HRBP 的 per-task 技能评分尚未运行** | 新加的 HRBP 节点应该在每次任务后给每个激活的 skill 打分——但尚未运行过。Learning 缺少最细粒度的输入。 | 🟡 重要 |

### Learning 诊断

**Learning 是一个只读系统。** 它观察、记录、但不行动。它像一台监控摄像头——拍到了所有东西，但不会打电话报警。Policy 和 Runtime 不读取 Learning 的输出。

---

## 四层协同诊断

```
当前状态：

Policy ──gate──► Runtime ──execute──► Ledger ──record──► Learning
  ✅                ⚠️                  ✅                🔴
  阻止非法激活      跳过太多质量门      记录精准          只读不写

反馈回路：
  Learning → Policy:  断裂 🔴 (权重更新了但 Policy 不读)
  Learning → Runtime: 断裂 🔴 (模式检测了但 Runtime 不调整)
  Ledger → Policy:    部分 ⚠️ (skip 事件存在但 Policy 不验证 skip 质量)
  Ledger → Runtime:   正常 ✅ (Runtime 读取 state 决定下一步)
```

### 根因

**四个层之间的合约不完整。**

Policy 告诉 Runtime "什么可以激活"，但没告诉它"什么必须激活"（对特定 task_type）。
Runtime 告诉 Ledger "发生了什么"，但 Ledger 没有验证"这是不是足够好"。
Ledger 告诉 Learning "这是数据"，但 Learning 没有渠道告诉 Policy 或 Runtime "根据数据，你应该改变行为"。

### 三件事修复协同

**1. 闭合 Learning → Policy 回路。**
Learning 产出的模式（"grill-me 在 design 任务上被跳过 3/3 次"）应该自动触发 Policy 更新（"将 grill-me 对 architect 的 evaluates 边升级为 blocking=required，条件：task_type is design"）。当前这条回路完全断裂。

**2. 给 Runtime 引入"skip 成本"。**
当前 Runtime 跳过节点的成本为零。应该有一个递增成本：第一次跳过 advisory evaluator → free，第二次跳过同一 evaluator → warning，第三次 → 需要显式 justification 且记录到 Ledger 的 quality_signal 扣分。

**3. 让 Ledger 的 quality_signal 诚实。**
当前 quality_signal 在 success 时硬编码 1.0——但 FleetOps v3 白屏证明了 success ≠ quality。应该由 delivery-prover 的 verdict 和 soul 对齐分共同决定 quality_signal。Runtime 不能自评 1.0。
