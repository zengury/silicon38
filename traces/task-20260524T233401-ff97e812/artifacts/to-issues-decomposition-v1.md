# Issue Decomposition — WisglowAgent Mobile Client

## From PRD: to-prd-mobile-client-v1
## Total Issues: 14 | Estimated: ~8 dev-days

---

## Dependency Graph
```
M-00 (project setup)
 ├─ M-01 (auth + router)
 │   ├─ M-02 (chat service + SSE)
 │   │   ├─ M-03 (ChatScreen UI)
 │   │   └─ M-04 (streaming text + tool cards)
 │   ├─ M-05 (workflow service)
 │   │   └─ M-06 (WorkflowList + WorkflowDetail)
 │   ├─ M-07 (skill browsing)
 │   └─ M-08 (profile + notifications)
 ├─ M-09 (PWA manifest + SW)
 ├─ M-10 (design tokens)
 └─ M-11 (offline + error states)

M-12 (import cycle cleanup) [parallel — backend]
M-13 (optimization doc) [parallel — docs]
```

---

## Issues

### M-00: 项目骨架搭建
- **Description**: 新建 `frontend/mobile/` 子项目，Vite + React + TypeScript + Tailwind CSS。配置 package.json、tsconfig、vite.config、tailwind.config。创建目录结构。
- **Acceptance Criteria**:
  - `npm install && npm run dev` 在 localhost 启动空白应用
  - 目录结构匹配 architect ADR 规范
  - Tailwind 构建正常，未使用样式被 purged
- **Size**: M
- **Blocked by**: none

### M-01: 认证系统 + 路由骨架
- **Description**: 实现 LoginScreen（账号密码登录）、authService（token 存储/刷新）、useAuth hook、路由守卫。Tab + Stack 路由框架。
- **Acceptance Criteria**:
  - 未登录用户自动跳转 LoginScreen
  - 登录成功后跳转到对话 Tab
  - token 持久化到 localStorage，7 天内有效
  - 401 响应自动清除 token 并跳转登录
  - 底部 4 Tab 导航可用，各 Tab 显示占位内容
- **Size**: L
- **Blocked by**: M-00

### M-02: 对话服务 + SSE 流
- **Description**: 实现 chatService（发送消息、获取历史、SSE 流式接收）、useSSE hook（自动重连、指数退避）、useChat hook（消息状态管理）。
- **Acceptance Criteria**:
  - `POST /api/v1/conversations/:id/messages` 发送消息返回 200
  - SSE 连接收到流式 token，逐 token 回调
  - SSE 断开后自动重连（1s→2s→4s→8s cap）
  - 重连携带 `Last-Event-ID`
  - 消息列表按时间倒序，加载更多支持分页
- **Size**: L
- **Blocked by**: M-01

### M-03: ChatScreen UI
- **Description**: 实现 ChatScreen 对话界面：消息气泡（AI 左/用户右）、输入框、发送按钮、对话列表切换。输入框多行自动增高（max 4 行），键盘弹起自适应。
- **Acceptance Criteria**:
  - 消息气泡样式符合 UX 规范（#171D26 AI / #1A3A2E 用户）
  - 输入框空时发送按钮置灰，有内容时点亮 accent-primary
  - 键盘弹起时输入框上移（不遮挡消息列表）
  - 新消息自动滚动到底部
  - ConversationList 可左右滑动切换对话
- **Size**: L
- **Blocked by**: M-02

### M-04: 流式文本渲染 + 工具调用卡片
- **Description**: StreamingText 组件（逐 token 追加，Markdown 渲染）、ToolCallCard 组件（可折叠工具调用详情）。
- **Acceptance Criteria**:
  - 流式文本以 typing 效果逐字显示，非整块替换
  - Markdown 正确渲染（代码块、列表、加粗）
  - 工具调用卡片显示工具名 + 状态（执行中/完成/失败）
  - 卡片展开可查看调用的参数和结果
- **Size**: M
- **Blocked by**: M-03

### M-05: 工作流服务
- **Description**: workflowService（获取待处理列表、获取详情、提交审批、获取进度）。适配 `/api/v1/workflow/` 端点。
- **Acceptance Criteria**:
  - `GET /api/v1/workflow/instances` 返回列表，支持分页
  - `GET /api/v1/workflow/instances/:id` 返回详情含步骤
  - `POST /api/v1/workflow/instances/:id/approve` 提交审批
  - 错误时返回可读的中文错误信息
- **Size**: M
- **Blocked by**: M-01

### M-06: WorkflowList + WorkflowDetail UI
- **Description**: WorkflowList（待审批列表卡片）、WorkflowDetail（步骤进度条、审批内容、底部操作栏）。审批成功 toast + 返回列表。
- **Acceptance Criteria**:
  - 列表卡片显示：标题、发起人、时间、当前步骤
  - 详情页显示步骤进度条（current/total）
  - 底部固定操作栏：拒绝（error-soft 色）和批准（accent-primary 色）
  - 审批后显示结果 toast，自动返回列表刷新
  - 空状态显示 "暂无待处理工作流"
- **Size**: L
- **Blocked by**: M-05

### M-07: SkillScreen 技能浏览
- **Description**: 技能列表（搜索框 + 卡片网格）、SkillDetail（技能描述、参数、使用按钮）。
- **Acceptance Criteria**:
  - 技能卡片显示：图标、名称、描述、标签、评分
  - 搜索可实时过滤技能名称和描述
  - 点击卡片进入详情页
  - 详情页显示完整描述、输入参数、使用示例
- **Size**: M
- **Blocked by**: M-01

### M-08: ProfileScreen + 通知
- **Description**: ProfileScreen（用户信息、退出登录）、NotificationsScreen（通知列表、未读角标）。
- **Acceptance Criteria**:
  - 显示用户名、头像（首字母占位）、所属企业
  - 退出登录清除 token 并跳转登录
  - 通知列表显示未读标记
  - 底部"我的" Tab 显示未读通知角标数字
- **Size**: S
- **Blocked by**: M-01

### M-09: PWA 配置
- **Description**: manifest.json（应用名、图标、主题色、全屏模式）、Service Worker（静态资源缓存、离线回退页）、安装提示。
- **Acceptance Criteria**:
  - Chrome Android 可添加到主屏幕（显示安装提示）
  - 启动后全屏显示（无浏览器 chrome）
  - 离线时显示缓存的静态页面（非空白）
  - 图标在 192px、512px 分辨率下清晰
- **Size**: M
- **Blocked by**: M-00

### M-10: 移动端设计系统 (Design Tokens)
- **Description**: 实现 UX 规范中的 mobile tokens：CSS custom properties + Tailwind config 扩展。颜色、间距、字号、触摸目标、安全区。
- **Acceptance Criteria**:
  - CSS variables 覆盖 DESIGN.md 基础 tokens 中移动端需要变更的部分
  - Tailwind config 添加 mobile 专属 utility classes
  - `--safe-area-bottom` 正确处理 iOS notch
  - 所有组件使用 token 变量而非硬编码值
- **Size**: S
- **Blocked by**: M-00

### M-11: 离线和错误状态处理
- **Description**: useNetwork hook（在线/离线检测 + Banner）、各屏 Loading/Empty/Error 状态组件、全局错误边界。
- **Acceptance Criteria**:
  - 离线时顶部显示 "当前离线" Banner (warning 色)
  - 恢复在线后 Banner 消失，自动重连 SSE
  - 每屏包含 Loading (skeleton)、Empty (引导文案)、Error (描述+重试) 三个状态
  - SSE 断连显示 Toast "连接中断，正在重连..."
  - 全局 ErrorBoundary 捕获未处理异常
- **Size**: M
- **Blocked by**: M-01

### M-12: Import 循环清理（后端优化）
- **Description**: 修复 4 处 `storage → agent` 反向 import，清理 `agent/workflow → agent/session` 循环依赖。添加 import-lint CI。
- **Acceptance Criteria**:
  - `grep -r "from agent\." storage/` 返回 0 结果
  - `grep -r "from agent.session" agent/workflow/` 返回 0 结果
  - 现有测试全部通过（`pytest tests/ -x -q`）
  - CI 添加 import 边界检查步骤
- **Size**: M
- **Blocked by**: none (parallel to frontend)

### M-13: 优化文档输出
- **Description**: 汇编所有 Silicon Org 节点产出为一份完整的优化方案文档。包含：triage 分析、caveman 简化、zoom-out 地图、architect ADR、UX 规范、issues 拆解。
- **Acceptance Criteria**:
  - 单个 Markdown 文件，可独立阅读
  - 每个部分有清晰的摘要和执行建议
  - 包含依赖图、估时、风险提示
  - 输出到 `docs/OPTIMIZATION_PLAN.md`
- **Size**: S
- **Blocked by**: all issues above (汇编性质的收尾工作)

---

## Completion Report
```yaml
completion_report:
  what_was_done: "将移动端 PRD 拆解为 14 个独立 issue：11 个前端 + 1 个后端优化 + 1 个文档汇编"
  key_decisions:
    - decision: "项目骨架 (M-00) 和 import 清理 (M-12) 可并行启动"
      rationale: "前后端无依赖，不同工程师可同时工作"
    - decision: "M-02 (对话服务) 和 M-05 (工作流服务) 可并行"
      rationale: "仅依赖 M-01 认证，无相互依赖"
    - decision: "M-03 (ChatScreen) 为最长阻塞链 (M-00→M-01→M-02→M-03→M-04)"
      rationale: "对话是核心场景，需优先保障"
  handoff_focus:
    - "senior-frontend: 按 M-00→M-01→M-02→M-03 顺序实施，其余 issue 可并行补充"
    - "code-reviewer: 每个 PR 对应一个 issue，按编号审查"
  open_questions:
    - "是否需要国际化 (i18n) 支持（当前 PRD 未包含）"
  known_constraints:
    - "SSE polyfill (`event-source-polyfill`) 需测试与后端 FastAPI SSE 的兼容性"
```
