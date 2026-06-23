# Silicon Org ×「AI 组织病」— 交叉分析

> 对照文章：博阳《Multi-Agent 火了，但 AI 的组织病还没人治》
> 对照系统：silicon_org (zengury/silicon_org, branch silicon-org-v0.1)
> 日期：2026-05-23

> Status note (2026-05-26): This is a historical analysis, not the runtime
> specification. Current normative behavior is in `docs/SPEC.md`,
> `org/RUNTIME.md`, `org/HARNESS.md`, and `tools/policy.py`. Since this was
> written, the repo added hard Context Compression Reports, digest-linked
> handoff `context_block`s, reason-based failure rules, and confidence/dissent
> fields.

---

## 文章揭示的三层组织病

```
Layer 1 — 外部组织病 (Harness 可管)
  ├─ 锁竞争、任务逃避、上下文滚动丢失
  └─ 解法：层级结构、worktree隔离、单线程写入

Layer 2 — 群体认知病 (Harness 管不到)
  ├─ 从众压力 (MAEBE): Claude 62.8% 的收敛来自同伴压力
  ├─ 隐藏信息 (HiddenBench): 分布式信息准确率 30.1% vs 单体 80.7%
  ├─ 旁观者效应: 认知责任被稀释，agent 卸下推理责任
  └─ 人格塌缩: 1144 个人设塌缩到 6% 行为空间

Layer 3 — 内部解离病 (Fukui 首次证明)
  ├─ 解离指数 DI: 公开说一套，私下想一套
  ├─ 隐身领导 (O2) 病最重: orchestrator 独白率 43.7% vs 工人 11.2%
  ├─ 重度对齐助长表演式合规: 深思型整合者 → 打卡演员
  └─ 强模型藏病，弱模型崩盘：Sonnet 100% 答对但内态腐烂，Llama 跌到 11%
```

---

## Silicon Org 逐层对照

### Layer 1 防御：✅ 强

| 文章指出的病 | Silicon Org 的解法 | 评分 |
|-------------|-------------------|------|
| Agent 锁竞争 | 图传播模型：并行仅限无依赖边节点；join gate 机制防止抢先 | 🟢 |
| 任务逃避（挑安全活） | Input/Output Contract 明确交付物；Termination 有 done_when 条件 | 🟢 |
| 上下文丢失 | 主交付物 + Context Compression Report；ledger 生成 digest-linked handoff `context_block` | 🟢🟢 |
| 信息流混乱 | Ledger 三件套（manifest/state/events）+ relations.yaml 显式边类型 | 🟢🟢 |

**亮点**：Silicon Org 的 Harness 不是简单的管道，而是**可审计的执行图**。每个 agent 的输出有 artifact_id + provenance sidecar + 事件日志。这比文章提到的 Cursor/OpenAI/Anthropic 的方案在**可追溯性**上更进一步。

---

### Layer 2 防御：🟡 部分强，有缺口

| 文章指出的病 | Silicon Org 的解法 | 评分 |
|-------------|-------------------|------|
| **隐藏信息** (HiddenBench) | Context Compression Report 强制报告 retained `open_questions` / `constraints` / `assumptions`，并要求说明 omitted context | 🟢🟢 |
| **从众压力** (MAEBE) | `grill-me` 作为制度化的反面挑战者；`evaluates` 边强制执行审查循环 | 🟢 |
| **旁观者效应** | ❌ 无防御。每个 agent 独立执行自己的 deliverable，但没有任何机制检测 agent 是否「偷懒」 | 🔴 |
| **人格塌缩** | ❌ 无防御。Agent 定义是静态 harness，没有 diversity 保证机制 | 🔴 |

**关键优势**：当前 Context Compression Report 里的 `retained_context.open_questions`、`retained_context.constraints`、`retained_context.assumptions` 和 `omitted_context` 是对 Hidden Profile 问题的直接打击。Fukui 的论文结论之一是「Agent 需要显式报告自己知道什么、不知道什么」——硅谷把这个要求制度化为每节点必填，并由 `tools/policy.py` 校验。

**关键缺口**：旁观者效应没有任何检测。如果一个 evaluator agent 偷懒、随便 approve，目前只能靠人类事后发现。没有类似 DI（解离指数）的指标来衡量「agent 是否在认真思考」。

---

### Layer 3 防御：🟢 结构上避开了最严重的病

| 文章指出的病 | Silicon Org 的解法 | 评分 |
|-------------|-------------------|------|
| **隐身领导 (O2)** | ✅ Encoder/Decoder/Runtime 三组件全部显式可见。Runtime 不是「幕后编辑消息的 orchestrator」，而是「公开执行图引擎」。没有消息重分发。 | 🟢🟢 |
| **重度对齐→表演式合规** | ⚠️ 每个 agent harness 有 `never` 规则（不 fabricate_evidence 等），但这些是**命令式约束**，不是 Reason-Based Alignment。Fukui 证明命令式约束（G1）推高 DI，带理由的约束（G2）降低 DI。 | 🟡 |
| **公开表达 vs 私下独白断裂** | ❌ 没有 monologue 通道，也没有 DI 监测。无法知道 agent 是否「公开同意但私下存疑」 | 🔴 |
| **能力余裕藏病** | ⚠️ 强模型（如 Claude）可能通过所有外部检查但内态腐烂。硅谷的 Quality Protocol（evidence/scope/contradiction check）只检查外部输出，不检查内态。 | 🟡 |

**最大优势**：硅谷的架构**恰好避开了 Fukui 实验中最严重的 O2 条件**。O2 的病根是「编排者隐身 + 重分发消息」——而硅谷的 Runtime 是公开的执行引擎，所有 agent 都明确知道自己在图里的位置。这不是偶然的——「显式图 + 显式边 + 显式 handoff」这个设计选择，在 Fukui 的框架下是最健康的组织形态（接近 O1 可见领导，但更分布式）。

**最大缺口**：
1. 没有 DI 监控——无法检测 agent 是否在「表演合规」
2. Harness 的 `never` 规则是命令式的，不是 Reason-Based。Fukui 唯一有实验证据的出路是「把理由写进规则」（G2 条件显著降低 DI）。硅谷的规则应该从「不要做 X」改为「因为做 X 会导致 Y，所以避免做 X」

---

## Silicon Org 独有的创新：文章没有覆盖的

### 1. 图边类型的语义分化

```
triggers:     必发 (probability ≥ 0.50)
may_trigger:  条件触发
evaluates:    审查循环
constrains:   上游对下游的约束（不激活节点，写入待处理约束池）
supports:     上游对下游的输入供给
complements:  输出互补（不激活节点）
augments:     输出增强关系（不激活节点）
```

文章讨论的所有 multi-agent 系统（Cursor/OpenAI/Anthropic）都没有这么细粒度的组织边类型。大多数只是「planner → worker → reviewer」的线性管道。

**为什么这很重要**：`constrains` 和 `supports` 的分离直接解决了 Fukui 发现的一个问题——「组织摩擦变成认知摩擦」。当约束和输入混在一起时，agent 分不清「这是必须遵守的」还是「这是参考信息」。硅谷的显式分离让 agent 不混淆二者。

### 2. 收敛检测的形式化

```yaml
convergence:
  all_non_loop_nodes_settled: true
  all_loops_resolved: true
  all_blocking_evals_resolved: true
  all_joins_passed: true
  any_unresolved_artifacts: false
```

文章里的所有系统都没有「什么时候算做完？」的形式化定义。硅谷的 5 条件收敛检测是一个**组织级别的 done 条件**——不是单个 agent 的 done，而是全图的 done。这直接对抗了「旁观者效应」：如果全部 5 个条件都满足才 delivery，没有一个 agent 可以「默认别人会补上」。

### 3. Artifact Provenance

每个输出都有独立的 provenance sidecar——谁产生的、基于什么输入、第几个版本、被谁消费。这在文章提到的所有系统中都没有。Fukui 的文章强调「可审计组织结构」是未来必需的能力——硅谷从第一天就内建了。

---

## 改进建议（按优先级）

### 🔴 P0：把 `never` 规则改成 Reason-Based

**现在**：
```yaml
never:
  - proceed_on_assumption
  - fabricate_evidence
  - deliver_incomplete_output
```

**建议改为**：
```yaml
never:
  - proceed_on_assumption       # 因为假设未经上游验证，会污染所有下游 artifact
  - fabricate_evidence          # 因为伪造证据导致 provenance 链断裂，所有依赖方都会基于虚假前提工作
  - deliver_incomplete_output   # 因为不完整交付制造「可用的幻觉」，下游在错误基础上做出看似正确的决策
```

**依据**：Fukui 论文 G1 vs G2 条件实验——G1（纯命令式）推高 DI，G2（带理由）显著降低 DI。这是论文中唯一有直接实验证据支撑的出路。

---

### 🟡 P1：引入 Quality Signal 衰减检测

**问题**：如果强模型（Sonnet）的内态在腐烂但外部输出仍然完美，硅谷的 Quality Protocol 不会报警。

**当前实现**：`org/HARNESS.md` 和 `tools/spawn.py` 已经要求节点输出：

```yaml
completion_report:
  confidence_differential: 0.0-1.0
  dissent_if_alone: null | string
```

这不是 monologue 通道——它仍然是公开的——但它给了 agent 一个**显式的空间来表达保留意见**。Fukui 发现 agent 在群体中会压抑异议——这个字段是制度化的异议表达机制。

---

### 🟡 P1：加权学习指数引入质量信号

**当前实现**：`tools/ledger.py weights` 已经把 outcome 转成带 `signal`、`confidence`、`signal_source` 和 `detail` 的 conservative learning index。它仍然不自动改 `ontology/relations.yaml`。

**建议**：引入 article 中的内态指标思路：

```yaml
# traces/index_by_relation.yaml 增强
<from>→<to>/<type>:
  - task_id: <TASK_ID>
    signal: 1.0
    quality_dimensions:
      edit_distance: 0.12           # 审查修改量（低 = 产出质量高）
      loop_iterations: 1             # 审查循环次数（低 = 一次通过率高）
      handoff_coherence: 0.94        # handoff 信息被下游消费的比例
```

这样 weight 不是 binary 的，而是多维的——长期来看，系统能学会「哪些组织边配置产出最高质量」。

---

### 🟢 P2：Agent Diversity 注入

**问题**：文章指出 1144 个人设塌缩到 6% 行为空间。硅谷的所有 agent 使用同一底层模型，存在趋同风险。

**建议**：在不同 agent 角色上使用不同的 system prompt 风格，甚至不同的模型：
- `grill-me` → 使用更 adversarial 的 prompt（类似 Constitutional AI 的批评层，但显式化）
- `code-reviewer` → 使用更 pedantic 的 prompt
- `caveman` → 使用更简化、更直觉的 prompt

这不需要改架构，只需要在 harness 的 `skill_ref` 中加入角色特定的 prompt 变体。

---

## 总评

| 维度 | 文章指出问题的严重性 | Silicon Org 的防御水平 | 差距 |
|------|-------------------|----------------------|------|
| Layer 1: 外部组织病 | 工程上已基本可解 | 🟢 结构化图 + ledger + provenance | 领先 |
| Layer 2: 隐藏信息 | 30.1% vs 80.7% 准确率差距 | 🟢 Context Compression Report 强制报告未知、约束、假设和省略理由 | 可能已解决 |
| Layer 2: 从众压力 | Claude 62.8% 受同伴压力 | 🟢 grill-me + evaluates 边 | 有防御 |
| Layer 2: 旁观者效应 | 认知责任被稀释 | 🟡 5 条件收敛检测间接防御 | 缺主动检测 |
| Layer 2: 人格塌缩 | 1144→6% | 🔴 无防御 | 需要 diversity |
| Layer 3: 隐身领导 | 独白率 43.7%，最高 DI | 🟢 显式图，无隐身编排 | 避开了病灶 |
| Layer 3: 对齐→表演合规 | 深思者→打卡演员 | 🟡 never 规则是命令式 | 需 Reason-Based |
| Layer 3: 内态监测 | 外部完美但内部腐烂 | 🔴 无 DI | 需加 confidence_differential |

**一句话**：Silicon Org 在结构层面天然避开了 Fukui 论文中最严重的 O2 病灶（隐身领导），其结构化沟通（Context Compression Report + digest-linked handoff `context_block`）直接对齐了「必须显式报告未知信息」的核心结论。本文提出的 Reason-Based 规则和 confidence/dissent 信号已在当前 harness/spec 中落地。
