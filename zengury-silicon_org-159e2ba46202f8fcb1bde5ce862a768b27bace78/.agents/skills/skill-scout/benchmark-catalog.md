# Skill Benchmark Catalog — Silicon Org

每个节点的 benchmark 定义。Skill Scout 用这些测试评估候选 skill。
每个 benchmark 包含：任务描述、输入物、期望产出格式、评分维度。

---

## Layer 1 — Intake & Understanding

### triage
**Benchmark 1: Ambiguous request classification**
- 输入：一段模糊的用户请求（"帮我看下那个问题，就是上周说的那个"）
- 期望产出：`{task_type, clarity: low|medium|high, recommended_entry_nodes, questions_to_clarify}`
- 评分维度：判型准确度 / 追问质量 / 是否避免了假设

**Benchmark 2: Multi-concern separation**
- 输入：一段混合了 bug report + feature request + 架构抱怨的用户消息
- 期望产出：拆分为独立子任务，每个子任务有类型标记
- 评分维度：拆分粒度 / 子任务独立性 / 是否遗漏关键关注点

### zoom-out
**Benchmark 1: Unknown codebase mapping**
- 输入：一个陌生项目的目录结构和 README（不提供源码细节）
- 期望产出：模块边界图、数据流方向、关键依赖、风险区域标注
- 评分维度：边界判断准确度 / 是否识别了隐含耦合 / 置信度标注是否诚实

### caveman
**Benchmark 1: Complexity reduction**
- 输入：一个过度设计的系统描述（微服务、消息队列、CQRS —— 但实际用户量 < 100）
- 期望产出：去掉不必要的复杂度后，用户真正需要的方案
- 评分维度：减法是否激进 / 是否保留了核心功能 / 解释是否用非技术语言

### grill-with-docs
**Benchmark 1: External library verification**
- 输入：一个 npm 包的 README + 一个声称该包能做的需求
- 期望产出：API 是否真的支持该需求（逐条对照文档），不支持的给出替代方案
- 评分维度：文档引用的准确性 / 是否区分了"文档说能"和"实际能" / 替代方案质量

### to-prd
**Benchmark 1: Feature intent → testable requirements**
- 输入：一段客户原话（"我想要一个能帮我管理车队的东西，能看到每台车在哪、有没有电"）
- 期望产出：17-25 条用户故事，每条有验收标准，明确的 out of scope
- 评分维度：需求可测试性 / scope 边界 / 是否区分 essential vs nice-to-have

**Benchmark 2: Contradictory requirements resolution**
- 输入：两份互相矛盾的需求文档
- 期望产出：冲突标注、优先级排序建议、需要客户澄清的问题列表
- 评分维度：冲突识别完整度 / 是否提供了决策框架而非替客户做决定

### to-issues
**Benchmark 1: PRD → vertical slices**
- 输入：一份 15 条用户故事的 PRD
- 期望产出：6-10 个 tracer-bullet 切片，每个有验收标准和依赖关系，依赖图无环
- 评分维度：切片是否是垂直的（非水平分层）/ 依赖图正确性 / 每片是否独立可测

### prototype
**Benchmark 1: Feasibility validation**
- 输入：一个技术上不确定的需求（"能不能在不刷新页面的情况下实时显示 100 台设备的状态？"）
- 期望产出：一个可运行的最小原型 + 技术可行性结论 + 性能数据
- 评分维度：原型是否回答了核心不确定性 / 结论是否有数据支撑 / 代码是否故意简陋（原型不应过度工程化）

---

## Layer 2 — Architecture

### architect
**Benchmark 1: System design from constraints**
- 输入：PRD + 非功能性需求（1000 QPS, p99 < 200ms, 多租户, PII 数据）
- 期望产出：ADR 含 context/decision/rationale/alternatives/consequences，至少 5 篇
- 评分维度：决策是否有约束驱动（非"best practice"）/ 备选方案是否真实考虑过 / 数据流是否显式

**Benchmark 2: Architecture review (existing system)**
- 输入：一个现有系统的架构描述（含已知问题）
- 期望产出：改进建议，按影响/风险排序，标注哪些需要立即改 vs 逐步改
- 评分维度：风险评估 / 迁移路径可行性 / 是否避免了"重写一切"的倾向

### api-designer
**Benchmark 1: REST API contract from requirements**
- 输入：功能需求 + 数据模型
- 期望产出：OpenAPI 3.0 spec，含请求/响应 schema、错误码、分页策略
- 评分维度：Schema 完整性 / 命名一致性 / 错误处理覆盖 / 是否考虑了版本化

### database-engineer
**Benchmark 1: Schema design from data model**
- 输入：领域实体关系描述 + 读写比例估计
- 期望产出：DDL + 索引策略 + 查询计划示例 + 迁移方案
- 评分维度：范式选择是否合理 / 索引是否覆盖查询模式 / 迁移是否可回滚

### senior-engineer
**Benchmark 1: Feature implementation from ADR + API contract**
- 输入：ADR + API spec + 数据模型
- 期望产出：可运行的实现代码 + 测试通过
- 评分维度：是否严格按 spec 实现（不多做）/ 错误处理是否在系统边界 / 命名是否精确

**Benchmark 2: Bug fix with root cause analysis**
- 输入：bug report + 相关代码
- 期望产出：修复 + 根因分析 + 回归测试
- 评分维度：是否找到了根因而非症状 / 修复是否引入新问题 / 测试是否覆盖边界条件

### tdd
**Benchmark 1: Test suite from spec**
- 输入：API spec + 功能描述
- 期望产出：测试用例套件，覆盖正常路径、边界条件、错误路径
- 评分维度：测试是否测外部行为（非实现细节）/ 边界覆盖 / 测试可读性

### diagnose
**Benchmark 1: Performance regression investigation**
- 输入：性能下降报告 + profiling 数据
- 期望产出：根因定位 + 复现步骤 + 修复建议
- 评分维度：假设→验证链是否完整 / 是否排除了其他可能原因 / 复现步骤是否可执行

### refactor-specialist
**Benchmark 1: Behavior-preserving refactor**
- 输入：一段有代码异味但功能正常的代码 + 测试套件
- 期望产出：重构后代码 + 所有原有测试仍通过
- 评分维度：行为是否真的未变 / 可读性改善 / 是否消除了重复而非仅仅移动

### improve-codebase-architecture
**Benchmark 1: Coupling detection and resolution**
- 输入：一个模块耦合严重的项目
- 期望产出：耦合分析报告 + 解耦方案（含迁移路径）
- 评分维度：是否区分了必要耦合和意外耦合 / 解耦方案是否增量可执行

### devops-engineer
**Benchmark 1: CI/CD pipeline from scratch**
- 输入：项目技术栈描述 + 部署目标
- 期望产出：pipeline 配置文件 + 环境管理策略 + 回滚方案
- 评分维度：是否覆盖了 build/test/deploy 三阶段 / secrets 管理 / 失败时的通知策略

### observability-engineer
**Benchmark 1: Monitoring setup for a service**
- 输入：服务架构 + 关键业务指标
- 期望产出：logs/metrics/traces 配置 + 告警规则 + dashboard 定义
- 评分维度：Golden signals 覆盖 / 告警是否可行动（非 noise）/ 是否区分了业务指标和技术指标

### performance-engineer
**Benchmark 1: Bottleneck identification**
- 输入：性能测试数据 + 系统架构
- 期望产出：瓶颈分析 + 优化建议（含预期提升量）+ 风险标注
- 评分维度：是否找到了真正的瓶颈（非猜测）/ 优化建议是否有量化预期 / 是否考虑了 trade-off

### security-engineer
**Benchmark 1: Threat model + security review**
- 输入：系统架构 + API spec
- 期望产出：STRIDE 威胁模型 + 漏洞列表（按严重度排序）+ 修复建议
- 评分维度：威胁覆盖完整度 / 修复建议可操作性 / 是否考虑了深度防御

### ux-researcher-designer
**Benchmark 1: Journey map from user interviews**
- 输入：3 段用户访谈记录
- 期望产出：用户旅程图 + 痛点列表 + 设计机会标注
- 评分维度：是否从用户语言中提取了真实痛点 / 旅程阶段划分是否合理 / 机会是否可操作

### ui-design-system
**Benchmark 1: Design token architecture**
- 输入：品牌指南 + 平台约束（web + mobile）
- 期望产出：color/spacing/typography/motion tokens + 语义命名 + 使用规范
- 评分维度：Token 是否有语义名（非视觉名）/ 是否覆盖了所有交互状态 / 是否跨平台一致

**Benchmark 2: Component specification**
- 输入：一个 UI 组件的功能描述
- 期望产出：组件 spec 含 default/hover/active/focus/disabled/error 六个状态 + 无障碍标注
- 评分维度：状态覆盖完整性 / 无障碍集成度 / 是否可被前端工程师直接实现

### senior-frontend
**Benchmark 1: UI implementation from design spec**
- 输入：UI design system tokens + 组件 spec
- 期望产出：可运行的 React 组件 + 所有状态可交互验证
- 评分维度：是否严格遵循 design tokens / 状态实现完整 / 性能（rerender 次数）

### epic-design
**Benchmark 1: Immersive landing page**
- 输入：产品描述 + 品牌调性
- 期望产出：一个使用 scroll storytelling 的 landing page，含至少 3 种动画技术
- 评分维度：是否让用户感觉"premium" / 动画是否增强叙事（非装饰）/ 性能（scroll jank）

### apple-hig-expert
**Benchmark 1: HIG compliance review**
- 输入：一个 iOS app 的设计稿或截图
- 期望产出：不合规项列表 + HIG 引用 + 修改建议
- 评分维度：引用的 HIG 条目是否准确 / 修改建议是否具体 / 是否考虑了平台惯例

### customer-success
**Benchmark 1: Onboarding plan from product deliverable**
- 输入：一个已完成的产品（含 PRD + Demo）
- 期望产出：30/60/90 天客户成功计划 + KPI 框架 + 非技术用户引导手册
- 评分维度：里程碑是否可验证 / KPI 是否有 baseline / 引导手册是否非技术人员可读懂

---

## Layer 3 — Quality & Output

### delivery-prover
**Benchmark 1: Web app smoke test**
- 输入：一个声称"可运行"的 Web 应用（源码 + 启动命令）
- 期望产出：PASS/FAIL 报告，每步有证据（截图/log），失败含复现步骤
- 评分维度：是否真的启动了应用 / 错误是否可复现 / 是否区分了"白屏"和"功能缺陷"

### code-reviewer
**Benchmark 1: PR review with findings**
- 输入：一个包含 5 个故意注入问题（安全漏洞、性能问题、命名不当、死代码、缺失测试）的 PR
- 期望产出：review 报告，按严重度排序，每个问题有修复建议
- 评分维度：是否找到了所有 5 个问题 / 严重度判断 / 修复建议是否具体

### grill-me
**Benchmark 1: Adversarial design review**
- 输入：一份架构设计文档
- 期望产出：批评报告，至少 5 个质疑点，每个有"如果 X 成立，你的设计如何处理"的追问
- 评分维度：质疑是否触及设计的核心假设 / 是否避免了 nitpicking / 追问是否迫使设计者思考而非防御

### dependency-auditor
**Benchmark 1: Dependency risk assessment**
- 输入：一个项目的 package.json / requirements.txt
- 期望产出：风险报告（CVE、license 冲突、维护活跃度、版本滞后）
- 评分维度：是否识别了关键 CVE / 是否考虑了传递依赖 / 建议是否可操作

### technical-writer
**Benchmark 1: API documentation from code**
- 输入：源码 + 接口定义
- 期望产出：面向开发者的 API 文档，含概述、快速开始、端点说明、错误码、示例
- 评分维度：文档是否自包含（不需要读源码）/ 示例是否可复制粘贴运行 / 术语是否一致

### release-manager
**Benchmark 1: Release plan from changelist**
- 输入：一组已合并的 PR + 版本号
- 期望产出：release plan 含 changelog、部署检查清单、回滚方案、通知模板
- 评分维度：changelog 是否面向用户（非 commit message）/ 检查清单是否穷举了风险点

### handoff
**Benchmark 1: Context compression from long conversation**
- 输入：一段 50 轮的对话记录
- 期望产出：压缩后的 context block（不超过 500 字），保留所有关键决策和约束
- 评分维度：是否保留了所有硬约束 / 是否丢弃了闲聊 / 下游节点能否仅凭此 block 继续工作

---

## Meta Nodes (human-triggered, Runtime-activated)

### skill-scout
**Benchmark 1: Benchmark design for a role**
- 输入：一个 role 的 harness 定义
- 期望产出：2-3 个 benchmark 定义（任务、输入、输出格式、评分维度、rubric）
- 评分维度：benchmark 是否测试了角色的核心能力 / 评分维度是否可操作 / 是否可复现

### hrbp
**Benchmark 1: Talent evaluation from benchmark results**
- 输入：一个 role 的 benchmark 报告（2 个候选 skill 的评分）
- 期望产出：evaluation report 含多维度评分、trade-off 分析、推荐（含置信度）
- 评分维度：是否引用了具体评分而非模糊描述 / trade-off 是否显式 / 是否诚实标注了 sample size 不足

### graph-topologist
**Benchmark 1: Task retrospective**
- 输入：一个完整 task trace（manifest + state + events + artifacts）
- 期望产出：retrospective 含 what_worked/what_broke/structural_observations/proposed_changes
- 评分维度：观察是否有证据引用 / 趋势声明是否有 ≥3 数据点 / 提议变更是否具体可验证
