# 舰队仪表盘 — 第一原理分析

## 1. 那一件真正的事 (The One True Act)

**在机器人故障的秒数内，用户能够回答三个问题：是哪一台机器，出了什么问题，还剩多久。**

这不是"总览"。这不是"历史"。这是**故障时刻的决策支持**——操作员收到告警，打开仪表盘，在三秒内知道：*这台机器为什么停了，我现在能做什么，如果我什么都不做会发生什么。* 一切都以这个时刻为中心。一切都为这个时刻让路。

---

## 2. 每一项功能 vs 刀

### 1. 实时显示每台机器人电量、关节温度、CPU、网络延迟、当前任务、地理位置
**SERVES** — 这是故障诊断的原始素材。电量、温度、CPU 直接回答"出了什么问题"。当前任务和位置是理解故障上下文的必要条件。但呈现方式必须围绕这三个问题：不是详尽的仪表板，而是**关键信号被迫优先**。

### 2. 数据格式不统一（JSON / protobuf 混用，字段名和单位不一致），都要展示
**SUPPORTS** — 这是一个工程问题，不是产品问题。用户不关心数据格式混乱本身；他们关心**能看懂数字**。这需要一个数据规范化层（servant），让 UI 始终呈现一致的字段和单位。不要把数据混乱暴露给用户，要吞掉它。

### 3. 总览仪表盘：环形图 + 折线图 + 热力图，展示车队整体健康度
**DILUTES** — 这看似很合理："我想知道车队的整体状态"。但在故障时刻，整体状态无关。操作员不会说"我的车队 78% 健康，真好"——他会说"这台机器停了，为什么？" 整体指标是**统计的感觉**，不是**行动的根据**。它稀释了对单机故障的关注，推高了 UI 复杂度，要求实时聚合能力。移出产品。

### 4. 异常告警（摔倒、关节失联、电量过低）
**SERVES** — 告警是故障的入口。摔倒、关节失联、电量过低都是**能改变操作员行动的**状态信息。但这不是一个面板；这是一个**级联触发器**：告警来 → 用户跳到那台机器 → 他看到完整的诊断数据。告警系统必须和单机视图紧密耦合，不是独立的对话框。

### 5. 每台机器人 30 天历史曲线
**DEFER_IS_A_LIE** — "历史"听起来像事后分析，这真的需要在故障时刻吗？不。用户在故障发生时需要**过去 5 分钟的趋势**——是在恶化吗，还是才刚发生的脉冲？30 天的曲线是**工程运维和容量规划**的问题，属于分析层，不属于故障响应层。这会增加数据库负担，增加页面复杂度，分散注意力。完全拒绝。

### 6. 配置面板：调整告警阈值、采样频率、重连策略
**SUPPORTS** — 阈值和重连策略是**必需的后台系统**，但不属于主界面。这些是设置，不是操作。它们应该存在，但作为一个后院工具，不是前厅的一部分。UI 主体是用来响应故障的，不是用来调参的。隐藏它。

### 7. 留言、@同事、标记"我在处理"（协作）
**DILUTES** — 这是一个社交层，解决的是"团队协调"问题。但故障时刻，操作员的行为是**单人反射弧**：看到问题 → 理解它 → 决定行动。协作可以发生在 Slack，可以发生在事后——不是在秒数内的诊断时刻。加上它会增加 UI 竞争、增加数据库写入、制造出"我在处理"和"其实失败了"之间的同步问题。移出产品。

### 8. PDF/Excel 报表导出
**DEFER_IS_A_LIE** — 导出是一个**事后分析的需求**。事故发生，结束后，有人想写一份报告。这完全不属于故障响应。这是一个分析工具的功能，不是操作工具。完全拒绝。报告是另一个产品。

### 9. 暗色/亮色主题切换、多语言、可拖拽自定义布局
**DILUTES** — 主题切换和多语言有合理性，但可拖拽自定义**是一个陷阱**。可定制化承诺给用户"自己的工作区"，但在故障时刻，你需要的是**标准的、可预测的布局**。自定义增加了新用户的迷茫，增加了 UI 代码的复杂度，还要担心数据持久化。多语言是合理的（用户来自不同国家）。主题可以做，但最小化——单色主题足够。拖拽自定义：完全拒绝。

---

## 3. 推荐的最小真实产品 (Minimum Real Product)

### 产品内
- **单机诊断面板** (served) — 当选中一台机器时，展示：
  - 实时状态：电量、温度、CPU、网络延迟、当前任务、位置
  - 告警指示（如果有）
  - 过去 5 分钟的趋势线（电量、温度、CPU）：是在恶化吗？
  
- **告警入口** (served) — 一个列表或推送：哪些机器现在有故障。一键跳到诊断。

- **数据规范化层** (servant) — 后端处理 JSON/protobuf 混乱，向前端呈现一致的字段和单位。

- **基础样式** (served) — 暗色主题为主（易于长时间盯着看，减少眼睛疲劳），简洁布局，无拖拽。

- **告警阈值管理** (servant) — 一个隐藏的设置面板（不在主界面），让管理员调整。

### 产品外
- **车队整体仪表盘（环形图、热力图）** — 稀释焦点，不属于故障响应层。应该是一个分离的"Insights"或"Analytics"工具。
  
- **30 天历史曲线** — 这是容量规划工具，不是操作工具。数据存下来，但不在主界面暴露。
  
- **协作层（留言、@、状态标记）** — 协作属于 Slack 或票务系统。故障响应是单人反射弧，事后协调是团队层。混在一个工具里制造噪声。
  
- **PDF/Excel 导出** — 这是事后分析工具的功能，不属于实时操作。报告工具是分离的产品。
  
- **可拖拽自定义布局** — 增加复杂度，减少可预测性。标准布局足够。

---

## 4. 风险 (Risks of This Cut)

**客户期望**。客户说"希望功能尽量完整"，枚举了九项。我的建议剔除了 4 项（完整）+ 2 项（降级到后院）。客户可能会说"我是付钱的，我要这些功能"。应对方式：明确说，这些功能是存在的，但它们属于*不同的产品*。一个工具不能同时是"故障响应平台"和"协作平台"和"分析平台"——试图做三个事会把每个都做坏。

**告警设计的细节**。如果告警系统设计不好（响应慢、误报率高、无法追踪根因），单机诊断面板也救不了。后端数据管道和告警逻辑是这个产品的隐藏基础。如果基础不稳，前端漂亮也没用。必须同时投入。

**"过去 5 分钟的趋势"是否足够**。对于某些故障（例如某个关节渐进式失效），5 分钟的窗口可能太短。可能需要调整到 15-30 分钟。但核心原则不变：历史是助手，不是主角。

---

## Completion Report

```yaml
what_was_done: |
  First-principles analysis of fleet ops dashboard requirements, applying the Salk principle 
  (subtraction unto the true act) to distinguish served features from diluting ones.

key_decisions:
  - decision: "The one true act is fault diagnosis in seconds: which machine, what's wrong, how long is left."
    rationale: "A fleet operator's critical moment is when a machine fails. Everything else is either supporting this moment or stealing attention from it."
  
  - decision: "Cut fleet-wide visualization, 30-day history, collaboration layer, and export functionality."
    rationale: "These are real business needs, but they belong to different products (analytics, reporting, coordination). Bundling them dilutes the clarity of the fault-response tool."
  
  - decision: "Normalize data plumbing as a servant layer, not a user-facing problem."
    rationale: "The customer sees JSON/protobuf mess; the product should hide it. Backend work, not UI work."
  
  - decision: "Make diagnostic UI data-driven, not aesthetic-driven. No customizable layouts, minimal theming."
    rationale: "Fault response needs predictability and speed. Customization trades both for user autonomy that doesn't matter in an emergency."

handoff_focus:
  - "Tell the customer explicitly: These nine features belong to 3-4 products, not one. This is the fault-response core. Analytics, reporting, and coordination are separate tools."
  - "Invest heavily in the data pipeline and normalization layer. The UI is thin; the backend is where this lives or dies."
  - "Design the alert system for zero latency and high signal-to-noise. This is the gateway."
  - "Prototype with a single-machine view first. Get the diagnostic moment right before adding any breadth."

open_questions:
  - "What is the SLA for alert delivery? Sub-second? Seconds? This drives architecture."
  - "What machines are monitored together? One operator per machine, or one operator per fleet?"
  - "What external systems does the operator need to act? (inventory, schedules, repair tracking?)"

known_constraints:
  - "Customer enumerated nine features, likely expects most/all. Conversation required."
  - "Data format inconsistency is a backend problem, not UI. Backend must solve it first."
  - "The 'minutes left' question requires prediction logic. May require ML or heuristics."

confidence_differential: 0.85
dissent_if_alone: |
  "I might be wrong about '5 minutes is enough.' Different failure modes have different timescales.
  Thermal failures build slowly; network failures are instantaneous. A 15-30 minute window might be safer.
  But this is calibration, not refusal. The principle holds: serve the fault-diagnosis moment."
```

---

## 尾注 (Epilogue)

这个分析的核心不是"少即是多"。核心是：**一个工具做一件事，做好。** 

客户要的九个功能都是有道理的。在一个大型运维平台里，它们都能活。但在*这个*工具里，它们相互竞争。选择的时候到了。

我建议的答案不是"削减功能到无生命"，而是"认真看清这台机器故障的秒数，然后设计一个把那个秒数做得正确的工具，其他的都放到地方去。"

这样的产品会更难，不会更容易。因为你必须得**对诊断的逻辑有绝对的清晰**。但如果你做对了，用户会感受到区别。
