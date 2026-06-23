# Mobile UX Design Specification — WisglowAgent

## Research Foundation

### User Personas (Enterprise Context)

**Persona 1: 张经理 — 审批驱动型**
- 角色：部门经理，管理 15 人团队
- 场景：会议间隙收到工作流审批通知，需要快速查看并批准/拒绝
- 移动端使用频率：每天 5-10 次，每次 < 2 分钟
- 核心需求：审批速度、通知可见性、一键操作
- 痛点：桌面端需要打开笔记本 → 登VPN → 打开浏览器 → 找到审批页 → 太慢

**Persona 2: 李工程师 — 知识查询型**
- 角色：技术工程师，经常需要查询内部知识库
- 场景：在现场/机房用手机查 FAQ、技能文档、历史对话
- 移动端使用频率：每天 3-5 次，每次 3-5 分钟
- 核心需求：搜索速度、流式回答、离线缓存历史记录
- 痛点：知识库在桌面端，现场没有电脑

**Persona 3: 王分析员 — 日常对话型**
- 角色：数据分析师，用 AI 助手做数据分析和报表解读
- 场景：通勤路上查看 AI 昨晚跑的分析结果，追问细节
- 移动端使用频率：每天 2-3 次，每次 5-10 分钟
- 核心需求：对话连续性、长文本可读性、文件查看
- 痛点：长回答在手机上难以阅读

### Usability Heuristics Applied
1. **Fitts's Law**: 高频操作（发送、审批）置于拇指热区（屏幕底部）
2. **Hick's Law**: 底部 Tab 仅 4 项，不做二级菜单
3. **Jakob's Law**: 采用微信/Telegram 式对话 UI 模式（用户熟悉）
4. **Miller's Law**: 工作流列表每屏 ≤ 7 项

---

## Navigation Architecture

### Tab Structure (Bottom Tab Bar)
```
┌──────────────────────────────────────┐
│           Screen Content              │
│                                       │
├──────────┬──────────┬─────────┬──────┤
│   💬     │   📋     │   🧩    │  👤  │
│  对话    │  工作流   │  技能   │ 我的  │
└──────────┴──────────┴─────────┴──────┘
```

### Screen Flow (Stack Navigation)
```
Login ──→ Tab Navigator
             ├─ 对话 Tab
             │   ├─ ConversationList (列表)
             │   └─ ChatScreen (对话详情) ← push
             ├─ 工作流 Tab
             │   ├─ WorkflowList (待处理列表)
             │   └─ WorkflowDetail (详情/审批) ← push
             ├─ 技能 Tab
             │   ├─ SkillList (技能目录)
             │   └─ SkillDetail (技能详情) ← push
             └─ 我的 Tab
                 ├─ Profile (个人信息)
                 └─ Notifications (通知列表) ← push
```

---

## Screen Layout Specifications

### 1. ChatScreen (核心屏幕)
```
┌──────────────────────────────────────┐
│ ← 返回   对话标题        🔔 ⋮       │ 48px header
├──────────────────────────────────────┤
│                                      │
│  ┌──────────────────────────┐        │
│  │         AI 消息          │        │
│  │  流式文本逐 token 渲染    │        │
│  └──────────────────────────┘        │
│                                      │
│            ┌──────────────────┐      │
│            │    用户消息       │      │
│            └──────────────────┘      │ 消息列表
│                                      │ (flex-col,
│  ┌──────────────────────────┐        │ 自动滚动)
│  │  工具调用: 🔍 搜索中...   │        │
│  │  ┌──────────────────┐    │        │
│  │  │ 搜索结果卡片      │    │        │
│  │  └──────────────────┘    │        │
│  └──────────────────────────┘        │
│                                      │
├──────────────────────────────────────┤
│ 🎤  │ 输入消息...          │ 📎  ➤  │ 56px input bar
└──────────────────────────────────────┘
  ↑ 语音按钮    ↑ textarea    ↑ 发送
```

**关键交互**:
- 消息气泡：AI 左对齐（#171D26 bg），用户右对齐（#1A3A2E accent-soft bg）
- 流式文本：逐 token 追加，自动滚动到底部
- 工具调用卡片：可折叠，展开显示详情
- 输入框：多行 textarea，自动增高（max 4 行），键盘弹起时输入框上移
- 发送按钮：仅在有输入内容时点亮（accent-primary）

### 2. WorkflowDetail (审批屏)
```
┌──────────────────────────────────────┐
│ ← 返回   工作流详情                   │ 48px
├──────────────────────────────────────┤
│                                      │
│  ⏳ 待审批                           │
│  📝 合同审批 — 采购部                 │
│  👤 发起人: 张三   🕐 2小时前         │
│                                      │
│  ┌──────────────────────────────┐    │
│  │  步骤 2/5: 部门审核            │    │
│  │  ████████░░░░░░  40%          │    │
│  └──────────────────────────────┘    │
│                                      │
│  ┌──────────────────────────────┐    │
│  │  审批内容                     │    │
│  │  ...表单/文本/附件...          │    │
│  └──────────────────────────────┘    │
│                                      │
├──────────────────────────────────────┤
│  [  拒绝  ]      [  ✓ 批准  ]       │ 64px 操作栏
│  error-soft      accent-primary     │
└──────────────────────────────────────┘
```

### 3. SkillScreen (技能浏览)
```
┌──────────────────────────────────────┐
│         技能市场                      │ 48px
├──────────────────────────────────────┤
│  🔍 搜索技能...                       │ search bar
├──────────────────────────────────────┤
│  ┌──────────────────────────────┐    │
│  │ 📊  数据分析助手              │    │
│  │ 连接数据库，自动生成图表...     │    │
│  │ 🏷 SQL · 图表     ⭐ 4.8     │    │
│  └──────────────────────────────┘    │
│  ┌──────────────────────────────┐    │
│  │ 📝  文档摘要                  │    │ 技能卡片列表
│  │ 上传文档，自动提取要点...      │    │
│  │ 🏷 NLP · 摘要     ⭐ 4.5     │    │
│  └──────────────────────────────┘    │
│                                      │
└──────────────────────────────────────┘
```

---

## Interaction Patterns

### Touch & Gesture
| 手势 | 场景 | 反馈 |
|------|------|------|
| **Tap** | 发送消息、审批按钮、选择项 | 120ms ripple 动画 |
| **Long press** | 消息复制、引用回复 | Haptic feedback + 上下文菜单 |
| **Swipe left** | 对话列表项 → 删除/归档 | 显示红色操作按钮 |
| **Swipe down** | 下拉刷新对话列表 | Pull-to-refresh indicator |
| **Pinch** | 附件图片缩放 | 标准 pinch-to-zoom |

### States (每屏必须覆盖)
1. **Loading**: Skeleton 占位符（保留布局结构，非全屏 spinner）
2. **Empty**: 空状态插图 + 引导文案 + 主要操作按钮
3. **Error**: 具体错误描述 + 重试按钮
4. **Offline**: 顶部 Banner 提示 "当前离线" + 缓存内容可查看

### Error Handling
- SSE 断连：底部 Toast 提示 "连接中断，正在重连..."，3 秒后指数退避重连
- API 超时：顶部 Banner 提示 "网络较慢，请稍候..."
- 认证过期：自动跳转登录，保留当前路径用于登录后恢复
- 审批失败：内联错误提示（不跳页），保留用户已填写的内容

---

## Design Tokens (Mobile Extension)

```css
/* 继承 DESIGN.md 基础 tokens */
/* 移动端扩展 */

/* Spacing */
--space-xs: 4px;
--space-sm: 8px;
--space-md: 12px;
--space-lg: 16px;
--space-xl: 20px;
--space-2xl: 24px;

/* Touch Targets (WCAG 2.5.5) */
--touch-min: 44px;

/* Typography (移动端略大 1px 补偿小屏) */
--font-body: 15px;
--font-small: 13px;
--font-caption: 12px;
--font-h1: 22px;
--font-h2: 18px;

/* Mobile Navigation */
--bottom-nav-height: 56px;
--header-height: 48px;
--safe-bottom: env(safe-area-inset-bottom, 0px);

/* Message Bubbles */
--bubble-ai-bg: #171D26;
--bubble-user-bg: #1A3A2E;
--bubble-radius: 16px;
--bubble-padding: 12px;

/* Animation */
--transition-fast: 150ms ease-out;
--transition-normal: 250ms ease-out;
```

---

## Completion Report
```yaml
completion_report:
  what_was_done: "产出移动端 UX 规范：3 个 persona、4 屏布局、5 种手势交互、完整状态覆盖、移动端 design tokens"
  key_decisions:
    - decision: "底部 Tab 4 项导航 (对话/工作流/技能/我的)"
      rationale: "Fitts 定律：高频操作放在拇指热区。微信/Telegram 模式用户熟悉"
    - decision: "审批操作固定在底部 64px 操作栏"
      rationale: "审批是移动端最高频的 HITL 操作，必须一手可达"
    - decision: "工具调用卡片可折叠"
      rationale: "手机上空间有限，但高级用户需要看到工具调用细节"
  handoff_focus:
    - "senior-frontend: 按规范实现 ChatScreen + WorkflowDetail 两屏（最高频）"
    - "ui-design-system: 将 mobile tokens 实现为 Tailwind config 或 CSS variables"
  open_questions:
    - "是否需要深色/浅色主题切换（当前仅设计暗色）"
    - "语音输入的语言选择和准确度要求"
  known_constraints:
    - "iOS Safari 对 PWA 的支持弱于 Android Chrome（部分 API 不可用）"
    - "SSE 在某些代理网络下可能被缓冲，需测试"
```
