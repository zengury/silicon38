# PRD: WisglowAgent 移动端客户端

---

## Problem Statement

WisglowAgent 企业智能体平台当前**只能在桌面浏览器使用**。企业用户需要在手机上随时：
- 查看和回复 AI 对话
- 审批工作流节点（HITL 人机协同）
- 浏览知识库和技能
- 查看工作流执行状态

缺失移动端导致用户在会议、通勤、现场作业等场景下无法使用产品，降低了企业级产品的实用价值。

## Solution

构建一个**移动端 Web 应用（PWA）**，复用现有 FastAPI 后端 API，提供触屏优先的对话、工作流和知识管理体验。采用独立移动端构建（非响应式改造），与桌面端共享 API 层但拥有独立 UI 层。

---

## User Stories

### 对话交互
1. 作为企业员工，我想要在手机上向 AI 助手提问，以便在离开办公桌时也能获取帮助
2. 作为企业员工，我想要看到 AI 的流式回复（逐字输出），以便及时了解 AI 的思考进度
3. 作为企业员工，我想要在手机上上传图片/文件作为对话附件，以便让 AI 分析现场照片或文档
4. 作为企业员工，我想要查看历史对话列表并切换对话，以便回顾之前的问答
5. 作为企业员工，我想要创建新对话，以便开始一个新的咨询主题
6. 作为企业员工，我想要看到 AI 执行了哪些工具调用（如搜索、查询数据库），以便理解答案的来由
7. 作为企业员工，我想要在对话中看到 AI 引用的知识库来源，以便验证信息可信度
8. 作为企业员工，我想要语音输入问题，以便在打字不便时使用

### 工作流交互
9. 作为管理者，我想要在手机上查看待审批的工作流节点，以便及时处理审批
10. 作为管理者，我想要在手机上批准/拒绝工作流步骤，以便不阻塞业务流程
11. 作为管理者，我想要查看工作流的整体执行进度，以便了解当前状态
12. 作为企业员工，我想要收到工作流节点需要我操作的通知，以便及时响应
13. 作为企业员工，我想要填写工作流中的表单，以便完成数据采集步骤

### 浏览与探索
14. 作为企业员工，我想要浏览可用的技能列表，以便了解 AI 助手能帮我做什么
15. 作为企业员工，我想要查看知识库目录和内容，以便找到相关文档
16. 作为企业员工，我想要在应用中心切换不同 Agent，以便使用不同领域的 AI 助手
17. 作为企业员工，我想要查看系统通知，以便了解与我相关的更新

### 认证与基础
18. 作为用户，我想要使用账号密码登录，以便安全访问系统
19. 作为用户，我想要登录状态持久化（7天免登录），以便不必频繁输入密码
20. 作为用户，我想要在弱网（3G/4G）下也能正常使用基本功能，以便在信号差的地方工作

---

## Implementation Decisions

### 1. 技术选型：独立移动端 PWA
- **决策**：新建 `frontend/mobile/` 子项目，使用 React + TypeScript + Vite + Tailwind CSS
- **理由**：桌面端 51K 行 React 代码未做任何移动端设计，响应式改造成本高于新建。独立项目可针对移动端交互模式（底部导航、手势、半屏面板）做根本性设计
- **API 复用**：100% 复用后端 API，`VITE_API_BASE_URL` 指向同一 FastAPI 服务

### 2. 路由与导航结构
- **决策**：底部 Tab 导航（4 项：对话 / 工作流 / 技能 / 我的）+ Stack 页面推送
- **理由**：移动端标准导航模式，单手可操作。与桌面端侧边栏+面包屑模型不同

### 3. 组件架构
- **决策**：构建独立移动端组件库（MobileChat, MobileWorkflow, MobileSkillCard 等），不复用 desktop 组件
- **理由**：触摸目标、信息密度、布局完全不同。强行复用会导致两套代码互相妥协

### 4. 流式对话适配
- **决策**：使用 EventSource (SSE) 接收流式响应，逐 token 渲染
- **理由**：与桌面端相同的 SSE 协议，网络层无需改动。移动端需处理网络切换重连

### 5. PWA 能力
- **决策**：实现 Service Worker 缓存静态资源，支持添加到主屏幕
- **理由**：PWA 提供接近原生体验（全屏、启动图、离线缓存），无需应用商店审核

### 6. 设计系统
- **决策**：继承 DESIGN.md 设计语言，新增移动端 tokens
- **理由**：保持品牌一致性，但需要移动端专用的间距、字号、触摸目标规范

### 7. 状态管理
- **决策**：使用 React Context + useReducer，不需要引入 Redux/Zustand
- **理由**：移动端状态相对简单（auth、conversations、notification count），避免过度抽象

---

## Testing Decisions

### What makes a good test
- 测试用户可感知的行为（能登录、能发消息、能看回复），不测试实现细节（Redux action type、CSS class name）
- 集成测试优先于单元测试：对话流 e2e > 单组件渲染
- 在真实移动端视口尺寸下测试（375×812 为基准）

### Modules to test
- `authService` — 登录/注册/token 管理
- `chatService` — SSE 流式对话、消息发送、历史加载
- `workflowService` — 工作流列表、审批操作
- 核心 UI 组件 — MobileChatView, MobileWorkflowList, LoginScreen

### Prior art
- 参考 `tests/test_sse_assistant_text.py` 的 SSE 测试模式
- 参考 `tests/test_conversation_history_flow.py` 的对话流测试

---

## Out of Scope
- 原生 iOS/Android 应用（React Native / Flutter）
- 离线对话（需要本地 LLM 推理，当前不可行）
- 语音通话功能
- 管理后台功能（`admin/` 模块 — 桌面端功能）
- 会员/支付管理
- 个人数据库管理
- 定时任务管理
- 与桌面端所有功能的 1:1 对等（移动端聚焦高频核心场景）

---

## Success Criteria
- 用户可在 375px 宽屏幕上完成：登录 → 发起对话 → 收到流式回复 → 查看工作流 → 审批节点
- 首屏加载 < 3 秒（4G 网络）
- SSE 流式首 token 延迟 < 2 秒
- 触控目标 ≥ 44×44px（符合 WCAG 移动端触摸目标标准）
- PWA 可添加到主屏幕，离线展示缓存页面
- 支持 iOS Safari 和 Android Chrome 最近两个主版本

---

## Completion Report
```yaml
completion_report:
  what_was_done: "产出 WisglowAgent 移动端 PRD：20 条用户故事、7 项技术决策、测试策略、明确范围边界和成功标准"
  key_decisions:
    - decision: "独立 PWA 子项目而非响应式改造桌面端"
      rationale: "桌面端 51K 行无移动设计，改造成本 > 新建。移动端交互模式本质不同"
    - decision: "底部 Tab + Stack 导航而非侧边栏"
      rationale: "单手操作是移动端核心需求，侧边栏不符合移动端人体工程学"
    - decision: "焦点为高频场景（对话/审批/浏览），不做功能 1:1 对等"
      rationale: "管理后台、支付等在桌面端完成，移动端只做实时交互场景"
  handoff_focus:
    - "architect: 需要确定移动端子项目工程结构、构建配置、API base URL 策略"
    - "ux-researcher-designer: 需要产出移动端线框图和交互规范"
    - "senior-frontend: 需要开始构建 mobile/ 项目骨架和核心组件"
  open_questions:
    - "移动端是否需要独立的部署域名/CNAME"
    - "通知推送是否通过 Web Push API 还是仅应用内轮询"
  known_constraints:
    - "DESIGN.md 的桌面端暗色主题需适配移动端 AMOLED 暗色模式"
    - "SSE 在移动网络不稳定时可能频繁断开，需实现自动重连"
```
