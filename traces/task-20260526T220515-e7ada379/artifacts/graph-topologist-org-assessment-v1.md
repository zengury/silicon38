# Graph Topologist v2 — Silicon Org 结构评估

**日期:** 2026-05-26
**方法:** Grove black-box + early-defect-detection + paired indicators
**数据:** 17 个任务痕迹 + 35 节点 graph + 64 条触发边

---

## 1. Black Box Model

| Grove 概念 | Silicon Org 映射 | 健康度 |
|-----------|-----------------|--------|
| **Input** | 任务描述 → Encoder 判型 | ⚠️ 判型漂移（feature→complex→design，三轮 FleetOps 三种判型） |
| **Labor** | 激活的节点 × skill 质量 | 🔴 14/32 活跃节点从未被激活。一半劳动力闲置。 |
| **Output** | Deliverables + traces | ✅ 10/17 成功交付 |
| **Windows** | Trace 文件 | ✅ 结构化事件，可审计 |

---

## 2. Daily Operations Review

### Review Task Forecast

| 指标 | 值 | 判定 |
|------|-----|------|
| 判型准确度 | 60% (FleetOps 三轮三种判型) | ⚠️ Encoder 不稳定 |
| 入口节点准确性 | 75% (3/17 任务入口节点偏差) | ⚠️ 偶有 Layer 2 节点被选为入口 |
| 任务放弃率 | 41% (7/17 incomplete) | 🔴 太高 |

### Analyze Activation Variance

**核心发现：图说 64 条边，实际只用 12 条。81% 的触发边从未激活。**

```
实际工作流：triage/zoom-out → to-prd → architect → senior-engineer → code-reviewer
             7 个节点，12 条边，承载了全部 17 个任务的生产负荷。

图上的其他 25 个节点是乘客，不是司机。
```

最常用的边：
- `architect→senior-engineer` (5x) — 脊椎
- `senior-engineer→code-reviewer` (4x) — 免疫系统
- `zoom-out→architect` (3x) — 入口
- `to-prd→to-issues` (2x) — 拆解
- `to-prd→architect` (2x) — 设计传递

### Check Role Inventory

**14 个从未激活的活跃节点：**

| 节点 | 层 | 为什么从未激活 | 严重度 |
|------|-----|--------------|--------|
| `customer-success` | L2 | 新节点，v0.5 刚加入 | 预期 |
| `delivery-prover` | L3 | 新节点，v0.5 刚加入 | 🔴 如果存在，FleetOps 白屏会被拦截 |
| `dependency-auditor` | L3 | 无入边触发 | 🔴 skill 分 0.30，即使激活也无法工作 |
| `devops-engineer` | L2 | 只在涉及部署时激活 | ⚠️ 合理但从未满足条件 |
| `diagnose` | L2 | 只在 bug_fix 任务激活 | ⚠️ 17 个任务中无 bug_fix |
| `epic-design` | L2 | 设计集群休眠 | 🔴 全设计集群未激活 |
| `grill-with-docs` | L1 | 入口节点，无人选用 | ⚠️ 可能被 triage/zoom-out 替代 |
| `handoff` | L3 | 只在显式 handoff 任务激活 | ⚠️ skill 已替换为 v2 |
| `observability-engineer` | L2 | 从未满足条件 | 🔴 skill 分 0.35 |
| `performance-engineer` | L2 | 从未满足条件 | 🔴 skill 分 0.30 |
| `prototype` | L1 | 入口节点，无人选用 | ⚠️ 可能因为任务太大不适合原型 |
| `refactor-specialist` | L2 | 无任务直接触发 | ⚠️ skill 已替换为 Ousterhout |
| `release-manager` | L3 | 只在 release 任务激活 | ⚠️ 17 个任务中无 release |
| `technical-writer` | L3 | skill 分 0.30，即使激活也无法工作 | 🔴 |

### Assess Graph Equipment

**52 条从未使用的触发边中，高危的：**

| 边 | 问题 |
|-----|------|
| `architect→grill-me/may_trigger` (0/17) | grill-me 从未评估过 architect。设计质量无对抗性验证。 |
| `architect→security-engineer/may_trigger` (0/17) | 安全从未在设计阶段介入。 |
| `caveman→architect/may_trigger` (0/17) | caveman 的简化视角从未影响架构。 |
| `caveman→ux-researcher-designer/may_trigger` (0/17) | 设计集群与 intake 集群断裂。 |
| `senior-engineer→observability-engineer/triggers` (0/17) | 每次实现都没有可观测性规划。 |
| `api-designer→senior-engineer/triggers` (0/17) | API 设计从未流向实现。 |
| `api-designer→tdd/triggers` (0/17) | API 契约从未驱动测试。 |

**根因不是边本身有问题——是触发条件太窄，或者上游节点本身从未被激活。**

### Evaluate Manpower

```
瓶颈路径：senior-engineer（每次任务 5-9 分钟，单线程）
热点节点：architect (9 次激活)、senior-engineer (10 次)、code-reviewer (6 次)
闲置节点：14 个从未激活
```

实际的劳动力分布严重偏斜——三个节点干了 70% 的活。

### Monitor Quality Indicators

| 指标 | 值 | 趋势 |
|------|-----|------|
| 任务成功率 | 59% (10/17) | 稳定 |
| 放弃率 | 41% (7/17) | ⚠️ 需关注——大部分放弃发生在 v0.4 之前的早期任务 |
| 平均完成节点数 | 6.2（成功任务） | 上升（v2: 11, v3: 4+10skip） |
| Soul 对齐（设计任务） | 0.30（最后一个） | 📉 退化 |
| Context chain 完整性 | 1.0（v3） | 📈 改进 |

---

## 3. Early Defect Detection

| 缺陷 | 发现阶段 | 如果未修复的成本 |
|------|---------|----------------|
| **81% 的图是装饰性的** — 64 条边，52 条从未触发 | Encoder / Activation | 10× — 每次任务 Runtime 都在评估一批永远用不到的候选边。浪费决策带宽。 |
| **设计集群完全断裂** — ux/ui/epic/prototype 从未走通整条链路 | Activation | 8× — 每个设计任务都跳过了整个设计集群（v3 FleetOps 零设计节点参与） |
| **6 个关键节点即使激活也无法工作** — skill 分 < 0.40 | Role Inventory | 5× — 如果某天 devops-engineer 被激活，它会用 0.65 分的 skill 产出不可用的 CI/CD 配置 |
| **Evaluator 节点被系统性跳过** — grill-me, caveman, tdd 频繁 skip | Activation | 5× — 质量门形同虚设 |

**最便宜的修复：在近期不需要的边上去掉 `triggers`，改为 `may_trigger` 或降低概率。减少每轮决策的噪音。**

---

## 4. Paired Indicators

| 主指标 | 值 | 反指标 | 值 | 平衡 |
|--------|-----|--------|-----|------|
| 任务完成率: 59% | ⚠️ | 跳过率: 29% (FleetOps v3) | ⚠️ | 双低——完成率不够高，跳过率也不够低 |
| 激活节点数: 6.2/任务 | ⚠️ | 死节点数: 14 | 🔴 | **严重失衡** — 图说 32 个活跃节点，实际只用 6 个 |
| 成功率: 59% | ⚠️ | Soul 对齐: 0.30 | 🔴 | 成功的定义里没有品质维度 |
| Context chain: 1.0 (v3) | ✅ | 从未触发的边: 81% | 🔴 | context 传递完美，但图本身有 81% 的 dead weight |

---

## 5. Linearity Tracking

```
任务成功率：v1 (abandoned) → v2 (success) → v3 (success) → 稳定在 60%
图利用率：  1 节点 → 11 节点 → 4+10skip → 在变得更"诚实"（显式跳过 vs 假装激活）
Soul 对齐：  ? → ? → 0.30 → 📉 退化
技能质量：   全 static → 4 个替换 → 📈 改进
```

**不是线性改善——是脉冲式跳跃。** 每次 meta 干预（加 soul、换 skill、加 delivery-prover）带来一次跳跃，然后趋于平坦，等待下一次干预。

---

## 6. 组织诊断总结

### 这是什么组织

一个 **7 人核心团队 + 25 个空办公室** 的公司。

| 特征 | 证据 |
|------|------|
| 核心执行路径极窄 | 7 个节点承载全部工作 |
| 大部分节点是"如果有需要"的预留位 | 14 个从未激活 |
| 质量门存在但不强制 | grill-me/caveman/tdd 被频繁 skip |
| 设计能力名义上存在，实际上断裂 | 设计集群 5 个节点几乎未激活 |
| 新能力在快速加入但尚未使用 | v0.5 加了 5 个节点，0 次激活 |
| 技能质量在改善但尚未传导到产出 | 4 个 skill 替换完成，尚无生产验证 |

### 三件事要做

**1. 修剪图——不是删节点，是降级边。**
81% 的边从未触发不是 bug——是设计的图比实际运行的图大太多。不应该删掉节点（它们代表真实需要的能力），但应该把从未触发的 `triggers` (prob ≥ 0.50) 降为 `may_trigger` 或降低概率。减少每轮 Runtime 的决策噪音。

**2. 强制质量门——至少对 design 类任务。**
`grill-me` 对 architect 的评估，`tdd` 对 senior-engineer 的评估——这些应该按 task_type 设为不可跳过。当前允许 Runtime 跳过任何评估，等于没有质量门。

**3. 给设计集群一个入口。**
当前设计集群（ux/ui/epic/prototype/apple-hig）几乎完全闲置，因为触发它们的条件需要上游节点（triage/to-prd）主动选择。应该有一条从 `to-prd`（当 task_type 是 design/feature+UI 时）直接到 `ux-researcher-designer` 的路径，不需要经过 triage 中转。

### 一句话

**Silicon Org 是一个骨架比肌肉大三倍的组织——图很漂亮，但跑起来的只有脊椎。修剪、强化、让质量门真正关上。**
