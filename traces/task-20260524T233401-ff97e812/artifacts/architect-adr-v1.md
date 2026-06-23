# Architecture Decision Record — task-20260524T233401-ff97e812

## Context
WisglowAgent 是一个 165K 行的企业级智能体编排平台。本次任务关注两个目标：
1. **架构优化**：消除已知债务（三引擎并存、import 循环、storage→agent 反向耦合）
2. **移动端构建**：新建手机端 Web 应用（PWA）

## ADR-001: 三引擎收敛策略

**Decision**: 本轮**不合并**三套引擎。采取「统一 Runtime 抽象层」策略，为未来收敛铺路。

**Rationale**:
- DAG Engine、PE Engine、SBS Loop 虽然概念重叠 70%+，但各自绑定 LangGraph checkpoint 机制和已有 `workflow_instance` 语义
- 强行合并风险高：已有测试套件（`test_peor_*` 等）依赖 PE 语义，SBS 绑定 Skill DAG 执行
- Phase 2 注释已在代码中标注方向，本轮先做低风险清理

**Alternatives rejected**:
- ❌ 立即合并三引擎 → 测试回归风险过大，需要专门的测试周期
- ❌ 保持现状不做任何改进 → 技术债务持续累积

**Consequences**:
- 引擎层维持 3 个执行器，但共享层（runtime/、workflow_graph/、infra/）需要收敛
- 工程师需要在 `engine/executor/dag_runner.py` 和 `engine/pe_engine/dag.py` 中选择时参考文档
- 建议在下一个 release cycle 中做专门的三合一专项

## ADR-002: Import 循环清理

**Decision**: 本轮修复所有已知反向 import，建立 import-lint CI guard。

**Rationale**:
- 已识别 4 处 `storage → agent` 反向 import（持久化层不应依赖编排层）
- `agent/workflow → agent/session` 反向依赖已标注 Phase 2，需要清理
- 修复成本低：通常是将 shared 类型移到 `utils/` 或 `contracts/` 即可

**Specific fixes**:
1. `storage/ → agent/` (4 occurrences): 将租户/会话 ID 等横切类型下沉到 `utils/`
2. `agent/workflow/ → agent/session/`: 提取共享 context key 到 `agent/contracts/`
3. 添加 `scripts/lint-imports.sh` 检查反向 import

**Alternatives rejected**:
- ❌ 推迟到 Phase 2 → 用户明确要求本轮优化

**Consequences**:
- 需要更新 `utils/conversation_id.py` 或提取新 shared 模块
- 涉及 10-15 个文件的 import 路径修改
- CI 需要新增 import 边界检查

## ADR-003: 移动端架构 — 独立 PWA

**Decision**: 新建 `frontend/mobile/` 子项目，React + TypeScript + Vite + Tailwind CSS，PWA-ready。

**Rationale**:
- 桌面端 `frontend/react/` 51K 行无任何移动端适配（无响应式断点、无触摸优化）
- 响应式改造桌面端的成本 > 新建独立项目（需要改动 layout、所有组件、路由）
- 移动端交互模式本质不同：底部 Tab 导航 vs 侧边栏、Stack 推送 vs 面包屑、半屏面板 vs 全屏 Modal
- PWA 提供接近原生体验（可安装、离线缓存、全屏），无需应用商店审核
- API 层 100% 复用，仅需 `VITE_API_BASE_URL` 配置

**Project structure**:
```
frontend/mobile/
├── public/
│   ├── manifest.json       # PWA manifest
│   ├── sw.js               # Service Worker
│   └── icons/              # App icons (192, 512)
├── src/
│   ├── App.tsx             # Root with auth gate + router
│   ├── main.tsx            # Entry point
│   ├── router/
│   │   └── index.tsx       # Stack + Tab navigator
│   ├── screens/
│   │   ├── ChatScreen.tsx       # 对话主屏
│   │   ├── ConversationList.tsx # 对话列表
│   │   ├── WorkflowScreen.tsx   # 工作流列表
│   │   ├── WorkflowDetail.tsx   # 工作流详情/审批
│   │   ├── SkillScreen.tsx      # 技能浏览
│   │   ├── KnowledgeScreen.tsx  # 知识库浏览
│   │   ├── ProfileScreen.tsx    # 个人中心
│   │   └── LoginScreen.tsx      # 登录
│   ├── components/
│   │   ├── chat/
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   ├── StreamingText.tsx
│   │   │   └── ToolCallCard.tsx
│   │   ├── workflow/
│   │   │   ├── WorkflowCard.tsx
│   │   │   └── ApprovalButton.tsx
│   │   ├── common/
│   │   │   ├── BottomTabBar.tsx
│   │   │   ├── ScreenHeader.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   └── Toast.tsx
│   │   └── ui/
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       └── Card.tsx
│   ├── services/
│   │   ├── api.ts            # Axios/ky instance with auth interceptor
│   │   ├── authService.ts    # Login, token refresh
│   │   ├── chatService.ts    # SSE streaming, message send
│   │   └── workflowService.ts # Workflow list, approve/reject
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useChat.ts
│   │   ├── useSSE.ts         # SSE stream hook with auto-reconnect
│   │   └── useNetwork.ts     # Online/offline detection
│   ├── stores/
│   │   └── appStore.ts       # React Context for auth, conversations
│   ├── styles/
│   │   └── tokens.css        # Mobile design tokens (extends DESIGN.md)
│   └── utils/
│       ├── format.ts
│       └── storage.ts
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts
└── package.json
```

**Dependency stack**:
- `react` + `react-dom` (18.x)
- `react-router-dom` (6.x, Stack + Tab navigation)
- `tailwindcss` (styling)
- `ky` or `axios` (HTTP client)
- `event-source-polyfill` (SSE for mobile browsers)
- `workbox` (PWA service worker generation)

## ADR-004: 移动端设计系统

**Decision**: 继承 `DESIGN.md` 核心 tokens，新增移动端专属 tokens。

**Rationale**:
- 品牌一致性：颜色、排版基础沿用桌面端
- 移动端特殊需求：触摸目标 ≥ 44px、底部安全区、AMOLED 暗色优化
- 新的 mobile tokens 文件独立维护，不与桌面端 CSS 耦合

**New mobile tokens** (extends DESIGN.md):
```css
/* Mobile-specific tokens */
--safe-area-bottom: env(safe-area-inset-bottom, 0px);
--touch-target-min: 44px;
--bottom-nav-height: 56px;
--screen-header-height: 48px;
--content-max-width: 100%;  /* mobile: no max-width */
--page-padding: 16px;       /* mobile: reduced from 24px */
--panel-gap: 12px;          /* mobile: reduced from 16px */
--card-radius: 10px;        /* mobile: slightly tighter */
--font-body: 15px;          /* mobile: slightly larger for readability */
--font-caption: 12px;
```

## ADR-005: SSE 移动端稳定性

**Decision**: 实现指数退避自动重连 + 网络状态监听。

**Rationale**:
- 移动网络 (4G/5G/WiFi 切换) 导致 SSE 断开是常见问题
- 流式对话断开后静默失败是糟糕的 UX

**Implementation**:
- `useSSE` hook: 自动重连（1s → 2s → 4s → 8s cap）
- `useNetwork` hook: 监听 `navigator.onLine`，断网显示离线提示，恢复后自动重连
- 重连时携带 `Last-Event-ID` header 用于断点续传

---

## Completion Report
```yaml
completion_report:
  what_was_done: "产出 5 份架构决策记录 (ADR)：三引擎策略、import 清理、移动端 PWA 架构、移动端设计系统、SSE 稳定性"
  key_decisions:
    - decision: "三引擎本轮不合并且先做统一 Runtime 抽象层"
      rationale: "合并风险高需专门测试周期。先清理 import 循环这类低风险高收益项"
    - decision: "移动端为独立 PWA 子项目 frontend/mobile/"
      rationale: "桌面端 51K 行无移动设计，独立构建比响应式改造成本低且结果更好"
    - decision: "修复 4 处 storage→agent 反向 import，引入 import-lint CI guard"
      rationale: "低风险、高收益的结构改进，修复成本 < 1 天"
  handoff_focus:
    - "senior-frontend: 按 frontend/mobile/ 结构搭建项目骨架和 8 个核心 screen 组件"
    - "senior-engineer: 修复 import 循环 (storage→agent, workflow→session)"
    - "code-reviewer: 审查所有交付代码"
  open_questions:
    - "三引擎收敛是否有用户场景不可合并的差异（PE 的 Plan-first vs SBS 的 Step-driven）"
  known_constraints:
    - "移动端不支持 on-device LLM，需始终连接后端 API"
    - "LangGraph checkpoint 机制与执行引擎耦合，分离需要深入 kernel 层"
```
