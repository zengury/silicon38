# Issue Decomposition: 机器人车队运维监控面板

## Issues

### Issue 1: 数据归一化适配器框架
- **description**: 设计并实现数据归一化适配器框架，定义统一内部Schema（robot_id, battery_level, joint_temperatures, cpu_usage, network_latency, task, gps, status, timestamp）。实现一个示例适配器（如JSON协议），验证框架可扩展。
- **acceptance_criteria**:
  - [ ] 定义统一Schema接口
  - [ ] 实现JSON协议适配器，将示例JSON数据转换为统一Schema
  - [ ] 适配器可热插拔，新增协议只需添加新文件
  - [ ] 单元测试覆盖适配器转换逻辑
- **estimated_size**: M
- **blocked_by**: none

### Issue 2: 后端基础架构与实时数据推送
- **description**: 搭建Node.js + Express后端，集成WebSocket用于实时数据推送。设置PostgreSQL数据库存储历史数据，Redis缓存最新状态。创建数据接收API端点，接收归一化后的数据并存储。
- **acceptance_criteria**:
  - [ ] Express服务器启动，提供健康检查端点
  - [ ] WebSocket连接建立，客户端可订阅实时数据
  - [ ] PostgreSQL表结构设计并迁移
  - [ ] Redis缓存最新状态，API返回缓存数据
  - [ ] 数据接收API端点接收POST请求并存储到数据库
- **estimated_size**: L
- **blocked_by**: Issue 1

### Issue 3: 总览仪表盘前端框架
- **description**: 搭建React + TypeScript前端项目，集成ECharts和react-grid-layout。实现总览仪表盘布局，包含环形图（电量分布）、折线图（CPU/温度趋势）、热力图（地理位置）。数据从后端WebSocket实时更新。
- **acceptance_criteria**:
  - [ ] React项目搭建，TypeScript配置
  - [ ] ECharts集成，环形图、折线图、热力图组件可渲染
  - [ ] react-grid-layout实现可拖拽布局
  - [ ] WebSocket连接后端，图表实时更新
  - [ ] 仪表盘显示所有机器人关键指标概览
- **estimated_size**: L
- **blocked_by**: Issue 2

### Issue 4: 异常告警引擎
- **description**: 实现基于规则引擎的告警系统，支持阈值告警（电量<20%）、状态告警（摔倒、关节失联）。告警触发时在面板内通知，支持静默期和升级策略。
- **acceptance_criteria**:
  - [ ] 规则引擎可配置阈值和状态规则
  - [ ] 告警触发时生成告警记录并存储
  - [ ] 面板内通知显示告警（如弹窗或通知栏）
  - [ ] 静默期配置生效，相同告警不重复触发
  - [ ] 升级策略：若告警持续超过设定时间，升级通知级别
- **estimated_size**: M
- **blocked_by**: Issue 2

### Issue 5: 机器人详情页与30天历史曲线
- **description**: 实现单台机器人详情页，展示30天历史曲线（电量、温度、CPU、网络延迟）。从后端API获取历史数据，使用ECharts绘制时间序列图。
- **acceptance_criteria**:
  - [ ] 后端API返回指定机器人30天历史数据
  - [ ] 前端详情页展示四个折线图（电量、温度、CPU、网络延迟）
  - [ ] 图表支持时间范围选择（如7天、30天）
  - [ ] 页面可导航从总览仪表盘点击进入
- **estimated_size**: M
- **blocked_by**: Issue 2

### Issue 6: 配置面板
- **description**: 实现配置面板，允许用户自定义告警阈值、采样频率和重连策略。配置保存到后端并持久化。
- **acceptance_criteria**:
  - [ ] 前端配置表单：告警阈值（电量、温度等）、采样频率、重连策略
  - [ ] 配置保存到后端API，存储到数据库
  - [ ] 配置生效后实时更新告警引擎行为
  - [ ] 配置面板可从导航访问
- **estimated_size**: M
- **blocked_by**: Issue 2

### Issue 7: 团队协作功能
- **description**: 实现基于WebSocket的实时留言板，支持@提及同事和标记“我在处理”。留言与机器人关联，实时推送。
- **acceptance_criteria**:
  - [ ] 留言板UI，可发送消息
  - [ ] @提及功能，输入@弹出用户列表
  - [ ] “我在处理”按钮，标记后显示状态
  - [ ] 消息实时推送至所有在线用户
  - [ ] 消息存储到数据库，历史可查
- **estimated_size**: M
- **blocked_by**: Issue 2

### Issue 8: 导出报表功能
- **description**: 实现导出当前视图为PDF或Excel。后端使用Puppeteer生成PDF，exceljs生成Excel。前端提供导出按钮。
- **acceptance_criteria**:
  - [ ] 后端PDF生成API，接收视图数据返回PDF文件
  - [ ] 后端Excel生成API，接收数据返回Excel文件
  - [ ] 前端导出按钮，选择格式后下载
  - [ ] 导出内容包含当前仪表盘或机器人详情数据
- **estimated_size**: M
- **blocked_by**: Issue 3

### Issue 9: 主题、多语言与可拖拽布局
- **description**: 实现暗色/亮色主题切换（CSS变量）、多语言支持（中文/英文，react-i18next）、可拖拽布局（react-grid-layout已集成）。
- **acceptance_criteria**:
  - [ ] 主题切换按钮，切换暗色/亮色，所有组件响应
  - [ ] 语言切换按钮，切换中文/英文，所有文本翻译
  - [ ] 布局可拖拽调整，位置持久化到本地存储或后端
- **estimated_size**: S
- **blocked_by**: Issue 3

## Completion Report

```yaml
completion_report:
  what_was_done: 将机器人车队运维监控面板PRD分解为9个独立的可执行issue，每个issue包含描述、验收标准、预估大小和依赖关系。
  key_decisions:
    - decision: 采用垂直切片分解，每个issue端到端实现完整功能
      rationale: 确保每个issue可独立验证，减少集成风险
    - decision: 数据归一化适配器作为第一个issue，因为它是后续所有功能的基础
      rationale: 后端和前端都依赖统一数据格式
    - decision: 主题、多语言和拖拽布局合并为一个issue
      rationale: 这些功能相对独立且规模较小，合并可减少开销
  handoff_focus:
    - 确保每个issue的验收标准清晰可测
    - 依赖关系图无环
  open_questions:
    - 告警通知方式是否需要邮件/短信？当前仅面板内通知，后续可扩展
    - 是否需要角色权限管理？当前未包含，可能影响协作功能
  known_constraints:
    - 初始支持10台机器人
    - 数据格式不统一需归一化
    - 需支持暗色/亮色主题、多语言、可拖拽布局
  confidence_differential: 0.9
  dissent_if_alone: null
  iteration_context: null
```

## Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read:
      - to-prd-prd-v1
    handoffs_read:
      - handoffs/to-prd→to-issues-20260530-165541.yaml
  retained_context:
    decisions:
      - 使用适配器模式进行数据归一化
      - 后端采用Node.js + Express + WebSocket
      - 前端采用React + TypeScript + ECharts
      - 告警引擎基于规则引擎
      - 协作功能基于WebSocket实时通信
    constraints:
      - 初始支持10台机器人
      - 数据格式不统一需归一化
      - 需支持暗色/亮色主题、多语言、可拖拽布局
    assumptions:
      - 机器人通过HTTP/WebSocket上报数据
      - 运维团队使用桌面浏览器访问面板
      - 历史数据保留30天
    open_questions:
      - 告警通知方式是否需要邮件/短信？
      - 是否需要角色权限管理？
      - 机器人数量上限是多少？
  omitted_context:
    - 具体文件路径和代码片段（避免过时）
    - 第三方库版本号（由开发阶段决定）
  compression_rationale:
    method: 保留与issue分解直接相关的决策、约束和假设，省略实现细节和版本信息。
    loss_notes:
      - 省略了具体文件路径，因为可能变化
      - 省略了第三方库版本号，由开发阶段决定
  quality_checks:
    - name: 每个issue有验收标准
      passed: true
    - name: 依赖图无环
      passed: true
    - name: 无issue被未指定的依赖阻塞
      passed: true
```