# UX Specification: 机器人车队运维监控面板

## 1. User Persona

### 运维工程师 王工
- **年龄**: 28-40
- **技术熟练度**: 高级
- **使用场景**: 桌面浏览器，日常监控多台机器人
- **目标**: 快速掌握整体健康状态，及时处理异常，分析历史趋势
- **痛点**: 数据分散、格式不统一、告警不及时、缺乏协作工具
- **设计启示**: 信息密度高，支持快捷键，可自定义布局

## 2. User Journey Map

| 阶段 | 动作 | 触点 | 情绪 | 痛点 | 机会 |
|------|------|------|------|------|------|
| 登录 | 打开面板，查看总览 | 仪表盘 | 😊 期待 | 加载慢 | 预加载缓存 |
| 监控 | 扫描关键指标 | 环形图、折线图、热力图 | 😐 专注 | 图表过多眼花 | 可折叠卡片 |
| 告警 | 收到异常通知 | 告警列表、弹窗 | 😟 紧张 | 告警不明确 | 详情链接 |
| 诊断 | 查看机器人详情 | 详情页、历史曲线 | 🤔 分析 | 数据维度少 | 增加对比 |
| 协作 | 留言、@同事 | 协作面板 | 😊 高效 | 通知不及时 | 实时推送 |
| 配置 | 调整阈值 | 配置面板 | 😐 偶尔 | 配置项多 | 模板预设 |
| 导出 | 导出报表 | 导出按钮 | 😊 满意 | 格式单一 | 支持PDF/Excel |

## 3. Interaction Model

### 3.1 总览仪表盘
- **布局**: 可拖拽网格（react-grid-layout），默认三列
- **组件**:
  - 电量环形图：显示各电量区间机器人数量
  - CPU/温度折线图：最近1小时趋势，可切换时间范围
  - 热力图：地图上显示机器人位置，颜色表示状态
  - 告警列表：最新5条告警，可展开详情
- **交互**: 点击图表钻取到机器人列表；悬停显示tooltip

### 3.2 机器人详情页
- **实时数据卡片**: 电量、温度、CPU、网络延迟，带阈值颜色指示
- **历史曲线**: 30天可缩放折线图，支持多指标叠加
- **地理位置**: 静态地图显示位置
- **操作**: 标记“我在处理”、留言、查看告警历史

### 3.3 告警系统
- **触发**: 规则引擎实时检测
- **展示**: 右上角弹窗 + 侧边栏告警列表
- **交互**: 点击告警跳转到机器人详情；可确认、静音

### 3.4 协作面板
- **留言板**: 按时间倒序，支持@提及（自动补全用户）
- **状态标记**: 按钮“我在处理”、“已解决”
- **通知**: WebSocket实时推送新消息

### 3.5 配置面板
- **告警阈值**: 滑块或输入框，支持按机器人分组
- **采样频率**: 下拉选择（1s/5s/10s/30s）
- **重连策略**: 重试次数、间隔

### 3.6 导出
- **按钮位置**: 仪表盘右上角
- **选项**: PDF（当前视图截图）、Excel（数据表格）
- **进度**: 加载状态提示

## 4. Wireframe (ASCII)

```
+----------------------------------------------------------+
| [Logo] 机器人运维监控面板    [主题] [语言] [导出] [用户]   |
+----------------------------------------------------------+
| [告警条] 机器人A摔倒！  [确认] [静音]                      |
+----------------------------------------------------------+
| +------------------+ +------------------+ +----------------+ |
| | 电量分布          | | CPU趋势          | | 热力图          | |
| | [环形图]          | | [折线图]          | | [地图]          | |
| | 高:5 中:3 低:2   | | 最近1小时         | | 位置标记        | |
| +------------------+ +------------------+ +----------------+ |
| +------------------+ +------------------+ +----------------+ |
| | 告警列表          | | 协作留言          | | 快速操作        | |
| | - 机器人A摔倒     | | 王工: 已处理      | | [添加机器人]    | |
| | - 机器人B电量低   | | 李工: @王工 看看  | | [配置]          | |
| +------------------+ +------------------+ +----------------+ |
+----------------------------------------------------------+
```

## 5. Usability Risks

| 风险 | 严重度 | 缓解措施 |
|------|--------|----------|
| 信息过载 | 高 | 可折叠卡片、自定义布局 |
| 告警疲劳 | 中 | 静默期、升级策略、分组 |
| 协作信息淹没 | 中 | 消息可回复、@通知 |
| 配置复杂 | 低 | 预设模板、向导式配置 |
| 导出数据不完整 | 中 | 明确导出范围、预览 |

## 6. Validation Approach

- **可用性测试**: 5名运维工程师，完成监控、告警响应、协作、配置任务
- **度量指标**: 任务完成率>90%，任务时间<2分钟，错误率<10%
- **A/B测试**: 布局方案对比（固定 vs 可拖拽）
- **启发式评估**: 一致性、系统状态可见性、用户控制

## 7. Design Decisions

| 决策 | 理由 |
|------|------|
| 可拖拽布局 | 适应不同用户偏好，提高效率 |
| 实时WebSocket推送 | 低延迟，及时告警 |
| 暗色主题优先 | 运维人员常长时间使用，减少眼疲劳 |
| 图表使用ECharts | 性能好，交互丰富 |
| 协作采用留言板而非聊天 | 保留上下文，便于追溯 |

## 8. Completion Report

```yaml
completion_report:
  what_was_done: 完成了机器人运维监控面板的UX设计，包括用户画像、旅程地图、交互模型、线框图、可用性风险及验证方法。
  key_decisions:
    - decision: 采用可拖拽网格布局
      rationale: 满足不同运维人员的个性化需求，提高效率
    - decision: 告警采用弹窗+侧边栏列表
      rationale: 平衡及时性和不干扰当前操作
    - decision: 协作采用留言板形式
      rationale: 保留完整上下文，便于追溯
  handoff_focus:
    - 前端组件实现（拖拽布局、图表、地图）
    - 告警规则配置界面
    - 协作实时通信
  open_questions:
    - 是否需要移动端适配？
    - 告警通知方式是否扩展邮件/短信？
    - 协作是否支持文件附件？
  known_constraints:
    - 初始支持10台机器人
    - 数据格式不统一需归一化
    - 需支持暗色/亮色主题、多语言、可拖拽布局
  confidence_differential: 0.85
  dissent_if_alone: null
  iteration_context: null
```

## 9. Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read:
      - to-prd-prd-v1
    handoffs_read:
      - handoffs/to-prd→ux-researcher-designer-20260530-165541.yaml
  retained_context:
    decisions:
      - statement: 使用适配器模式进行数据归一化
        source: upstream
        impact: 影响数据接入设计
      - statement: 后端采用Node.js + Express + WebSocket
        source: upstream
        impact: 影响实时通信方案
      - statement: 前端采用React + TypeScript + ECharts
        source: upstream
        impact: 影响图表库选择
      - statement: 告警引擎基于规则引擎
        source: upstream
        impact: 影响告警配置界面
      - statement: 协作功能基于WebSocket实时通信
        source: upstream
        impact: 影响协作交互设计
    constraints:
      - statement: 初始支持10台机器人
        source: upstream
        impact: 影响布局和性能设计
      - statement: 数据格式不统一需归一化
        source: upstream
        impact: 影响数据展示方式
      - statement: 需支持暗色/亮色主题、多语言、可拖拽布局
        source: upstream
        impact: 影响UI组件设计
    assumptions:
      - statement: 机器人通过HTTP/WebSocket上报数据
        source: upstream
        risk: 若协议不同需调整适配器
      - statement: 运维团队使用桌面浏览器访问面板
        source: upstream
        risk: 若需移动端需额外设计
      - statement: 历史数据保留30天
        source: upstream
        risk: 影响历史曲线时间范围
    open_questions:
      - statement: 告警通知方式是否需要邮件/短信？
        source: upstream
        owner: runtime
      - statement: 是否需要角色权限管理？
        source: upstream
        owner: runtime
      - statement: 机器人数量上限是多少？
        source: upstream
        owner: runtime
  omitted_context:
    - source: 具体文件路径和代码片段
      reason: 背景信息，非设计必需
    - source: 第三方库版本号
      reason: 由开发阶段决定
  compression_rationale:
    method: 保留与UX设计直接相关的决策、约束和假设，省略实现细节
    loss_notes:
      - 省略了具体文件路径
      - 省略了第三方库版本号
  quality_checks:
    - name: primary_workflow_present
      passed: true
    - name: usability_risks_named
      passed: true
```