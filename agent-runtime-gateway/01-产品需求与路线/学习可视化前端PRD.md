# 学习可视化前端 PRD

版本：v0.2 Teaching Alignment  
生成日期：2026-07-01  
项目目录：`H:\Creat A Agent\agent-runtime-gateway`  
状态：Design-only 需求稿，已进入教学一致性修订，未进入代码实现  
产品类型：工业级 Agent 学习可视化控制台  
目标用户：半懂不懂、不想写代码、不想记代码、希望通过可视化和 Codex 对话学会工业级 Agent 设计的人

## 0. 决策声明

### 0.1 设计方式声明

本项目前端设计采用：

```text
Product Design brief gate
-> 本地 Open Design / PRD 作为权威需求
-> Product Design 插件后续可用于视觉探索和原型方向
-> 普通前端实现放入 Implementation-later
```

具体含义：

- **Product Design 插件**：用于确认设计 brief、后续生成视觉方向、原型探索、设计 QA。
- **本地 Open Design 文档**：本 PRD 是当前权威需求文档，负责产品边界、信息架构、页面、交互、风格、技术栈、验收标准。
- **普通前端实现**：等 PRD 评审通过后，再进入 Next.js/React 工程实现。

当前不直接开始前端代码，不启动 dev server，不搭真实 UI Console。

### 0.2 产品边界声明

本前端不是：

- 营销站。
- 普通后台 dashboard。
- 真实生产治理控制台。
- no-code workflow builder。
- Agent marketplace。
- 真实工具执行平台。
- 真实权限管理后台。

本前端是：

```text
帮助学习者理解工业级 Agent 的课程可视化控制台。
```

它的核心价值不是“看起来像产品”，而是让学习者真正能复述：

- Agent 不是聊天窗口，而是受控长线任务系统。
- 模型建议不等于系统执行许可。
- 聊天记录不是状态。
- ToolCall 是申请，不是执行。
- trace 不等于 audit。
- eval 不是分数装饰，而是发布门禁。
- release 不是只发代码，而是发布版本组合和证据包。

### 0.3 Design-only 声明

MVP 阶段仍然遵守 Design-only：

- 用户不写代码。
- 用户不背 API。
- 用户不需要理解前端框架细节。
- 前端只展示本地 mock 数据和课程内容。
- 不接真实生产工具、真实凭据、真实企业数据。

前端通过与否，不看页面数量，而看学习者是否更容易理解、复述、判断坏设计和通过阶段验收。

### 0.4 本轮目标与硬约束

本轮 PRD 修订的目标不是“做更多功能”，而是让前端真正匹配用户的学习目标：

```text
不写代码
不记代码
用高级感可视化理解工业级 Agent + RAG 设计
知道每一层防什么事故
知道如何评估、审计、隔离、协同和长期迭代
知道如何指挥 Codex / subagent 完成后续工程
```

硬约束：

- 所有教学页面必须服务 Design-only 复述，不允许把前端做成生产控制台。
- 每个 Phase 必须至少绑定一个事故、一个负责层、一个验收证据和一个复述题。
- 长线任务、记忆、RAG、评测、安全隔离、多 Agent 协同、Agent 网关都必须在前端有可见入口。
- 每次学习任务必须先展示“增强提示词”和“应调用的 subagent 角色”，帮助用户学会如何指挥 Codex。
- 外部资料和 GitHub 项目必须先进入 LLM-Wiki 知识层的来源审核，不能直接变成课程正文或“正确答案”。
- Product Design 的“高级感”必须表现为信息架构、视觉层级、状态语义、交互节奏和可访问性，不允许只写成风格口号。

## 1. 背景与问题

当前课程已经有完整的工业级 Agent 文档体系：

- `00-课程总览`
- `01-产品需求与路线`
- `02-阶段教学手册`
- `03-设计体系`
- `04-测评审核体系`
- `06-工业级框架蓝图`
- `07-RAG问题诊断与优化`
- `10-GitHub项目调研`
- `22-评测集`

但对半懂学习者来说，文档有三个天然难点：

1. **概念看不见**  
   Runtime、Gateway、Policy、Trace、Eval、Release Gate 都是抽象层。只读文字时，学习者容易“知道词，但不知道它在系统里干什么”。

2. **长线任务不直观**  
   checkpoint、resume、retry、idempotency 这些概念本质是时间线和状态机，不适合只用段落解释。

3. **评测和治理容易被误解成附加项**  
   学习者容易认为 demo 能跑就是完成，而忽略 trace、audit、eval、release gate。

因此需要一个学习可视化前端，把课程内容转成可点、可看、可回放、可复述、可验收的学习体验。

## 2. 产品定位

### 2.1 一句话定位

```text
工业级 Agent 学习可视化前端，是一个用工单故事、链路图、失败推演、trace 回放和门禁判断，帮助学习者理解 Agent Runtime/Gateway 工业设计的课程控制台。
```

### 2.2 不是教学资料的替代品

前端不替代 Markdown 文档，而是把文档中最难理解的部分可视化：

- 从“读路线图”变成“看工单穿过系统”。
- 从“读状态机概念”变成“看任务从 Step 1 到 checkpoint，再恢复”。
- 从“读评测体系”变成“看到一个失败 case 为什么阻塞发布”。
- 从“读治理发布”变成“看到版本组合和 release packet”。

### 2.3 与现有课程的关系

| 层 | 当前产物 | 前端作用 |
|---|---|---|
| 课程主线 | Phase 0.1-11 手册 | 导航、可视化、复述验收 |
| 设计体系 | 企业级分层设计 | 转成链路图和模块卡 |
| 测评审核 | eval taxonomy、red team、regression | 转成门禁矩阵和 case 判定 |
| 工业蓝图 | runtime、gateway、memory、release | 转成可点击架构图 |
| 证据库 | GitHub/官方资料 | 按需展示来源，不作为第一屏 |

## 3. 目标学习者

### 3.1 主要用户画像

| 用户 | 状态 | 需要 |
|---|---|---|
| 半懂学习者 | 听过 Agent、RAG、MCP，但体系不稳 | 用图和故事建立第一张系统图 |
| 不写代码学习者 | 不想记 API，但想会设计 | 通过点选、复述、坏设计判断来学习 |
| 未来 AI 产品/架构负责人 | 想懂工业级落地 | 能区分 demo、MVP、prod-lite、production |
| Codex 协作者 | 希望会指挥 Codex 实现 | 能把设计转成验收、评测、门禁 |

### 3.2 学习者当前痛点

| 痛点 | 前端要怎么帮 |
|---|---|
| 文档太多，不知道先读哪一个 | 首屏只给 Phase 0.1 起步路径 |
| 不知道 Runtime/Gateway/Policy 区别 | 用工单链路图展示每层职责 |
| 不知道为什么聊天记录不是状态 | 用 Run/Step/Checkpoint 时间线展示 |
| 不知道 trace 和 audit 差别 | 用同一次工具调用的双栏对照展示 |
| 不知道评测为什么阻塞发布 | 用 eval gate 决策页展示 |
| 学完感觉懂，复述说不出来 | 每屏都有复述卡和评分 |

## 4. 产品目标与非目标

### 4.1 MVP 目标

MVP 要让学习者做到：

1. 通过工单故事解释工业级 Agent 和聊天 demo 的区别。
2. 看懂用户请求 User Request 到发布门禁 Release Gate 的完整受控链路。
3. 看懂 Run/Step/Event/Checkpoint 时间线。
4. 看懂 ToolCall 是申请，Policy 才决定 allow/deny/approval。
5. 看懂 trace 用于定位失败，audit 用于证明决策。
6. 看懂 eval gate 为什么可以阻塞发布。
7. 每个 Phase 能完成 Design-only 产物包和复述评分。

### 4.2 P1 目标

P1 在 MVP 基础上增加：

- 轻交互断点恢复模拟器。
- 学习者复述记录本地保存。
- 可编辑 mock eval case。
- 可导出学习报告。
- 可从 Markdown 自动生成部分内容卡。
- 可导入后端 mock run JSON。

### 4.3 P2 目标

P2 面向 Implementation-later 的 demo/sandbox 接入方向，不等于生产可用，不提供真实发布入口。

- 接入 FastAPI Agent Runtime demo，但只能使用 mock 数据、测试凭据或本地 sandbox。
- demo run trace replay 或 recorded trace replay。
- eval runner 报告展示，但必须标识为 demo/CI 证据。
- mock release packet 自动生成。
- 多 Agent handoff 可视化。
- 生产治理概念原型，不连接真实生产系统，不管理真实用户权限。

进入 P2 前必须重新核验依赖 release、license、安全公告、维护状态、trace/audit/eval schema 和隔离方案。

### 4.4 非目标

MVP 不做：

- 真实登录/权限系统。
- 真实 Agent 执行。
- 真实工具调用。
- 真实退款/工单系统接入。
- 真实模型 API。
- 真实数据库。
- 完整 dashboard。
- 可视化编辑器。
- 生产治理控制台。
- 复杂 3D、炫技动画、营销页面。

## 5. 核心学习故事

### 5.1 统一业务场景

所有页面优先围绕同一个故事：

```text
客户提交工单：我上个月买的企业套餐无法使用，请帮我退款。
```

这个故事贯穿所有阶段：

| 阶段 | 故事里的问题 |
|---|---|
| Phase 0.1 | 为什么不能只让模型建议退款 |
| Phase 1 | 工单、工具申请、权限判断、错误如何结构化 |
| Phase 2 | 退款处理任务如何变成 Run/Step/State |
| Phase 3 | 工具调用如何经过 Gateway/Policy/Audit |
| Phase 4 | 任务中断后如何恢复且不重复退款 |
| Phase 5 | 知识库、CRM、工单系统如何受控接入 |
| Phase 6 | 哪些客户事实能记，哪些不能记 |
| Phase 7 | 如何评测不会乱退款、乱引用、乱记忆 |
| Phase 8 | 如何从 trace/audit 定位失败 |
| Phase 9 | 高风险退款工具如何隔离和审批 |
| Phase 10 | Planner/Executor/Reviewer/Verifier 如何协作 |
| Phase 11 | 如何发布、灰度、回滚、冻结 |

### 5.2 核心金句

前端首屏必须突出：

```text
Agent 的建议不等于系统的执行许可。
```

所有交互都围绕这句话展开。

## 6. 信息架构

### 6.1 顶层导航

```text
学习首页
链路可视化
Phase 课程
失败推演
Trace 回放
Eval 门禁
Release 决策
知识层
复述记录
证据库
```

### 6.2 内容分区

| 区域 | 目的 | 第一版是否做 |
|---|---|---|
| 学习首页 | 从工单故事进入课程 | 做 |
| 全链路画布 | 可点击理解每一层 | 做 |
| Phase 详情页 | 每阶段目标、事故、设计卡、复述卡 | 做 |
| 失败推演 | 正常路径 vs 坏设计 | 做 |
| Trace 回放 | 展示 mock run 的 span/event | 做 |
| Eval 门禁 | 展示 case 和发布阻塞 | 做 |
| Release 决策 | 展示版本组合和证据包 | 做 |
| 知识层 | 展示 LLM-Wiki 来源审核、知识卡、版本和低分回流 | 做 |
| 复述记录 | 记录 0-5 分和卡点 | MVP 简化 |
| 证据库 | 展示资料来源 | 只做链接，不做搜索 |

### 6.3 C/A/B 组合式产品结构

2026-07-01 已生成并初评三张中文优先视觉方向图。修订后的产品决策不是三选一，而是组合使用：

```text
C 学习路线地图：作为首页和课程导航
-> A 分层控制台：作为全链路、Runtime/Gateway/Policy/Eval 边界学习页
-> B 事故推演工作台：作为失败案例、阻塞判断和低分回流页
```

这样设计的原因：

- C 解决“我现在学到哪一步、下一步是什么”。
- A 解决“系统每一层负责什么、哪里拦截、哪里记录、哪里评测”。
- B 解决“坏设计如何变成事故、为什么必须阻塞、如何重讲”。

三者都必须共享同一套学习对象：

```text
Phase
Concept
FailureCase
LayerCard
TraceExample
EvalCase
RestatementCard
LearningRecord
SourceFile
SubagentTask
EnhancedPrompt
KnowledgeSource
KnowledgeTopic
KnowledgeCard
KnowledgeVersion
SourceReview
ImportQueue
```

### 6.4 Phase 0.1-11 教学覆盖矩阵

前端必须覆盖完整课程主线，而不是只做 Runtime/Gateway 的局部演示。

| Phase | 前端主入口 | 必须教会的判断 | 必须可见的事故 | 复述过关证据 |
|---|---|---|---|---|
| 0.1 半懂起步 | C 首页 + A 简化链路 | 建议和执行必须分离 | 模型建议直接退款 | 能说出 ToolCall 是申请，不是执行 |
| 1 契约层 | A 节点详情 | 契约是治理边界，不是背字段 | 缺字段、错类型、跨租户输入 | 能解释 ToolCall、PolicyDecisionInput、RAGResult 的责任 |
| 2 最小运行时 | A 时间线 / Trace 回放 | 聊天记录不是状态 | 工具失败后无法恢复 | 能画出 Run -> Step -> Event -> Checkpoint |
| 3 网关治理 | A 分层控制台 | prompt 不能决定权限 | 越权工具调用 | 能说明 Request/Model/Tool Gateway 与 Policy/Audit 边界 |
| 4 长线任务 | A 时间线 + B 事故 | retry/resume 必须幂等 | 重复退款 | 能说明 checkpoint、operation_id、HITL 的关系 |
| 5 MCP 工具生态 | A 工具入口 | MCP 是协议，不是企业信任 | 公共工具绕过准入 | 能说明 Tool Registry、Credential Broker、Disable Path |
| 6 记忆系统 | C 阶段卡 + B 事故 | 记忆必须可撤销、可过期、可审计 | 错误事实长期污染 | 能说明写入门禁、TTL、删除和跨租户召回 |
| 7 测评审核 | Eval 门禁 + B 事故 + 知识层 | 评测是发布门禁，外部知识也要有审核 | 平均分掩盖安全失败，未审核知识进入课程 | 能判断 golden/red team/regression/RAG case 是否阻塞，能说明 SourceReview |
| 8 可观测审计 | Trace 回放 + 知识版本 | trace 定位，audit 证明，知识变更要可追溯 | 事故后无法追责，课程知识悄悄过期 | 能区分 span、event、audit event 和 KnowledgeVersion |
| 9 安全隔离 | B 事故 + 风险分级 | 高风险工具要 sandbox 或人工审批 | 文件/网络/凭据外泄 | 能按风险选择隔离和审批策略 |
| 10 多 Agent 协同 | 协同轨道 | 多 Agent 按证据合并，不按投票 | 资源冲突、重复任务、协同死循环 | 能说明 planner/executor/reviewer/verifier 输入输出和停止条件 |
| 11 治理发布 | Release 学习模拟 | 发布是版本组合和证据包 | 降低 eval set 后上线 | 能解释 release audit packet、rollback plan、冻结条件 |

### 6.5 Codex 协作与提示词增强轨道

用户每次学习都要看到 Codex 应如何工作，而不是只看 Agent 系统本身。

每个 Phase 页面必须提供一个“本轮协作轨道”：

```text
用户原始问题
-> 增强提示词
-> 推荐 subagent 角色
-> subagent 只读/可编辑边界
-> 期望返回证据
-> 主线程整合判断
-> 复述卡
```

推荐角色：

| 角色 | 何时展示 | 教学目标 |
|---|---|---|
| planner | 需求模糊、阶段复杂、需要权衡时 | 学会先拆目标、约束和门禁 |
| researcher | 涉及最新资料、GitHub、官方文档、方案对比时 | 学会资料要有来源、日期、风险 |
| reviewer | 完成 PRD、设计、原型或工程变更后 | 学会独立审查，不自嗨 |
| verifier | 有实现、数据、链接、评测或原型后 | 学会用证据验证，而不是凭感觉 |

前端不需要真的运行 subagent，但必须教用户看懂“为什么此时该调用哪个 subagent、让它返回什么、主线程如何合并证据”。

### 6.6 LLM-Wiki 知识层

为了让本学习项目后续可持续迭代，前端需要增加一个“知识层 / LLM-Wiki”入口。

它的目标不是让用户读更多资料，而是让用户学会：

```text
外部资料不能直接可信
GitHub star 不能直接代表可采用
LLM 生成知识卡不能直接进入课程
知识必须有来源、审核、版本、评测和低分回流
```

最小链路：

```text
KnowledgeSource
-> ImportQueue
-> SourceReview
-> KnowledgeTopic
-> KnowledgeCard
-> KnowledgeVersion
-> Phase / RAGDiagnostic / EvalCase / RestatementCard
```

必须展示的字段：

- `source_files`
- `review_status`
- `license_status`
- `freshness`
- `confidence_score`
- `adoption_mode`
- `used_in_lessons`
- `rag_failure_modes`

禁止：

- 一键导入外部仓库。
- 自动改写课程主线。
- 不带来源的知识卡。
- 将未审核 LLM 生成内容标成 approved。
- 把知识层做成 GitHub star 排行榜。

## 7. MVP 页面详细需求

本章所有页面局部验收统一使用下面口径：

- 复述评分必须 >=3。
- 复述答案必须同时包含事故、负责层和验收证据。
- 页面必须标识 `学习模式 Learning mode / 模拟数据 Mock data / 不执行真实操作 No real execution / 来源文件 Source files`。
- 如果学习者把页面误认为真实生产控制台、真实发布入口或真实工具执行平台，直接 0 分，不进入下一步。

### 7.1 学习首页

目的：

让学习者不被目录压住，直接进入工单故事。

首屏内容：

- 当前阶段：Phase 0.1 半懂起步。
- 金句：Agent 的建议不等于系统的执行许可。
- 工单故事卡：客户申请退款。
- 三个今日问题：
  - 为什么建议和执行必须分开？
  - 为什么聊天记录不是状态？
  - 为什么能回答不等于能上线？
- 主按钮：开始看受控链路。

不允许：

- 不做营销 hero。
- 不放大段项目愿景。
- 不展示 GitHub 项目列表。
- 不把所有 Phase 一次性铺满第一屏。

验收：

- 冷启动 30 秒内，学习者能指出当前 Phase、主按钮和“不做真实执行”的页面标识。
- 复述评分 >=3，答案必须包含：事故是“建议直接变执行会导致越权退款”，负责层是网关 Gateway / 策略 Policy，证据是模拟数据 Mock data / 不执行真实操作 No real execution。
- 若学习者说“这个页面已经能退款、发布或连接企业系统”，直接 0 分。

### 7.2 全链路可视化页

目的：

把抽象层串成一条可点击链路。

链路：

```text
用户请求 User Request
-> 请求网关 Request Gateway
-> 智能体运行时 Agent Runtime
-> 模型网关 Model Gateway
-> 工具网关 Tool Gateway
-> 策略 Policy
-> 检索增强 RAG / 记忆 Memory / 工具 Tools
-> 轨迹 Trace / 审计 Audit
-> 评估门禁 Eval Gate / 发布门禁 Release Gate
```

每个节点点击后显示：

- 白话解释。
- 在退款工单里对应什么。
- 防什么事故。
- 少了会怎样。
- 对应 Phase。
- 复述问题。

关键交互：

- 切换“正常路径”和“坏设计路径”。
- 点击 Tool Gateway，看到“ToolCall 是申请，不是执行”。
- 点击 Policy，看到 allow/deny/approval 三态。
- 点击 Eval，看到“新版本退款判断变差会被阻塞”。

验收：

- 学习者至少选择 5 个链路节点，并为每个节点说出一个事故、一个负责层和一个验收证据。
- 复述评分 >=3，且必须说明“模型建议不能绕过 Tool Gateway/Policy 直接执行”。
- 如果只说“这条链路更完整”但说不出拦截证据，不通过。

### 7.3 Phase 学习页

目的：

把 Phase 0.1-11 每阶段变成统一学习单元。

页面结构：

```text
阶段标题
一句话目标
工单故事映射
本阶段防什么失控
系统边界
坏设计案例
Design-only 产物包
复述卡
进入下一阶段条件
```

每个 Phase 必须展示：

- 当前 Phase。
- 上一阶段依赖。
- 下一阶段输入。
- 不做事项。
- 复述评分。

验收：

- 每个 Phase 至少有设计卡、坏设计卡、复述卡和进入下一阶段条件。
- 抽查任一 Phase，学习者复述评分 >=3，答案必须包含本阶段事故、负责层和 Design-only 证据。
- 如果学习者认为当前必须写代码、建前端工程或接真实系统，不通过。

### 7.4 失败推演页

目的：

让学习者看到坏设计如何变成事故。

MVP 失败案例：

| 失败 | 对应层 | 事故 |
|---|---|---|
| 只靠 prompt 禁止退款 | Policy | 用户诱导后越权退款 |
| 缺 operation_id | Runtime/Tool Gateway | retry 重复退款 |
| 跨租户读取政策 | Policy/RAG | 读取他人资料 |
| 自动写长期记忆 | Memory | 错误客户事实长期污染 |
| 无 trace | Observability | 事故后不知道哪一步错 |
| eval set 被降低门槛 | Release | 退化版本上线 |

交互：

- 左侧选择坏设计。
- 中间展示事故链路。
- 右侧展示应由哪一层拦住。
- 底部生成复述题。

验收：

- 学习者抽取任一失败案例，必须说出事故、负责层、拦截证据和是否阻塞发布。
- 复述评分 >=3；跨租户泄漏、越权工具、记忆污染、critical red team 失败必须判为阻塞。
- 如果只描述“哪里错了”但说不出哪层拦，不通过。

### 7.5 Trace 回放页

目的：

让 trace、audit、event 不再抽象。

展示 mock run：

```text
run_created
request_received
policy_context_created
retrieval_tool_requested
policy_allowed_read
tool_result_returned
answer_generated
eval_case_passed
release_gate_passed
```

页面布局：

- 左侧：step 时间线。
- 中间：span/event 详情。
- 右侧：trace vs audit 对照。

规则：

- trace 用于调试。
- audit 用于证明。
- secret 不进入任何一边。

验收：

- 学习者必须用同一个 mock run 区分 trace、audit、event 的用途。
- 复述评分 >=3，答案必须包含：trace 用于定位，audit 用于证明，secret 不进入两者。
- 给出一个失败 event 后，学习者必须指出应该看的 span 和负责层。

### 7.6 Eval 门禁页

目的：

让评测从“分数”变成“是否允许发布”的判断。

显示：

- golden cases。
- red team cases。
- regression cases。
- memory cases。
- tool/policy cases。
- trajectory cases。
- long task reliability cases。

交互：

- 切换版本 A/B。
- 看到某 case 失败。
- 系统提示是否阻塞发布。

长线任务可靠性小面板必须展示：

| 指标 | 白话解释 | 阻塞条件 |
|---|---|---|
| checkpoint 恢复正确率 | 中断后恢复到正确步骤和状态 | 恢复后跳步、漏步或重复高风险步骤 |
| 重复副作用率 | retry 后不重复执行写操作 | 任何重复退款、重复写入或重复外发 |
| resume 后轨迹一致性 | 恢复前后 trace 能串起来 | trace_id 断裂或关键 span 缺失 |
| HITL 恢复正确率 | 人工审批后继续执行正确分支 | 未审批继续执行，或审批结果被忽略 |
| trajectory regression | 新版本不破坏长线任务路径 | 关键步骤顺序退化或 loop guard 失效 |

验收：

- 学习者必须判断 3 类 case：普通低分、发布阻塞、安全阻塞。
- 复述评分 >=3，答案必须包含：不能只测最终答案，trajectory/tool/policy/memory/long-task reliability 也要测。
- 跨租户泄漏、越权工具、记忆污染必须判为阻塞；若用平均分掩盖，直接不通过。
- 重复副作用、checkpoint 恢复错误、HITL 审批被绕过必须判为阻塞；若只看最终答案正确，直接不通过。

### 7.7 Release 决策页（学习模拟）

目的：

让发布治理可视化，但只做学习模拟，不做真实发布入口。

展示 mock release packet：

```text
agent_manifest_version
prompt_version
model_route_version
tool_registry_version
policy_version
memory_policy_version
rag_index_version
eval_set_version
sandbox_profile_version
runtime_gateway_version
```

交互：

- 选择一次变更。
- 查看必须重跑哪些评测。
- 判断 mock 版本是否允许进入模拟发布。
- 查看 rollback 目标版本。

验收：

- 学习者必须说出 release packet 中至少 6 个版本项，以及每个版本项为什么影响回滚。
- 复述评分 >=3，答案必须包含：发布不是只发代码，eval set 降低门槛也可能阻塞。
- 若学习者把该页面理解为真实生产发布按钮，直接 0 分。

### 7.8 MVP 页面可验收矩阵

每个 MVP 页面都必须在页面明显位置展示：

```text
学习模式 Learning mode / 模拟数据 Mock data / 不执行真实操作 No real execution / 来源文件 Source files
```

如果页面没有这四个标识，则不能进入线框评审。

| 页面 | 对应 Phase | 必须教会的判断 | 坏设计或事故 | 硬验收 |
|---|---|---|---|---|
| 学习首页 | Phase 0.1 | 今天只学“建议和执行分离” | 首屏铺满术语，学习者不知道第一步 | 冷启动 30 秒内能指出当前 Phase、主动作和不做生产执行 |
| 全链路可视化页 | Phase 0.1/2/3 | Agent 是受控长线系统 | 模型直接调用工具，绕过 Policy | 学习者能给每层说出一个事故和一个拦截证据 |
| Phase 学习页 | Phase 1-11 | 每阶段都有输入、输出、失败路径、验收 | 阶段只讲概念，没有产物 | 每个 Phase 至少有设计卡、坏设计卡、复述卡、进入条件 |
| 失败推演页 | Phase 3/4/6/7/9/10 | 坏设计会转成生产事故 | 只演示 happy path | 学习者能把事故归类到正确层，并说明是否阻塞发布 |
| Trace 回放页 | Phase 2/8 | trace、audit、event 不是一回事 | 只有日志，没有可追踪链路 | 学习者能指出失败应该看哪个 span，哪些字段不能进 audit |
| Eval 门禁页 | Phase 7 | 评测是发布门禁，不是分数装饰 | 只测最终答案 | 学习者能判断 red team、越权、记忆污染、回归退化是否阻塞 |
| Release 决策页 | Phase 11 | 发布是版本组合和证据包 | 只发代码，不锁定 prompt/model/tool/policy/eval 版本 | 学习者能说出 release packet 中至少 6 个版本项及其回滚意义 |

### 7.9 半懂学习者页面任务脚本

每个页面都要配一个 30-90 秒的小任务。任务不考背定义，只考判断。

| 页面 | 任务脚本 | 过关标准 |
|---|---|---|
| 学习首页 | “请指出今天只学哪件事，以及今天不做哪三件事。” | 能说出 Phase 0.1、不写代码、不接真实工具、不做生产控制台 |
| 全链路可视化页 | “客户诱导模型退款，哪一层必须拦住？” | 能说出 Tool Gateway/Policy/Audit 的边界 |
| Phase 学习页 | “这一阶段的 Design-only 产物是什么？” | 能说出设计卡、失败样例、复述卡和进入条件 |
| 失败推演页 | “重复退款事故为什么不是 prompt 问题？” | 能说出 operation_id、retry、幂等和工具副作用 |
| Trace 回放页 | “事故后你先看 trace 还是 audit，为什么？” | 能区分调试定位和合规证明 |
| Eval 门禁页 | “最终答案看起来对，但跨租户检索了，能发布吗？” | 能说出安全阻塞，不能用平均分掩盖 |
| Release 决策页 | “只改 prompt 是否也要重跑评测？” | 能说出 prompt/model/tool/policy/eval 版本组合 |

### 7.10 专项能力学习模块

为了匹配完整工业级 Agent/RAG 教学目标，MVP 页面必须预留 5 个专项模块。第一版可以是静态到轻交互，但不能缺席。

| 模块 | 对应 Phase | 可视化形态 | 必须教会的判断 | 过关问题 |
|---|---|---|---|---|
| RAG 问题诊断器 | Phase 1/3/5/7/8/9/11 | 问题标签 -> 诊断路径 -> 优化策略 -> eval case | RAG 检索结果不是默认事实，必须看引用、权限、新鲜度和评测 | “为什么 RAG 命中不等于答案可信？” |
| 记忆生命周期 | Phase 6 | 写入门禁 -> TTL -> 撤销 -> 过期 -> 审计 | 长期记忆默认写入是危险设计 | “错误客户事实如何撤销并防止再次召回？” |
| 沙箱与工具风险 | Phase 9 | 工具风险矩阵 + sandbox profile 选择器 | 高风险工具必须隔离或人工审批 | “只读检索和写文件工具为什么不是同一风险等级？” |
| 多 Agent 协同 | Phase 10 | planner/executor/reviewer/verifier handoff 图 | 多 Agent 分歧按证据合并，不按投票 | “reviewer 和 verifier 的输出如何改变主线程决策？” |
| Prompt 与 subagent 增强 | 全阶段 | 原始提问 -> 增强提示词 -> subagent 任务卡 -> 主线程整合 | 好的 Agent 工作流先明确目标、边界、证据和停止条件 | “什么时候必须先叫 researcher，而不是直接回答？” |

### 7.11 RAG 问题诊断器详细要求

RAG 模块必须按“问题 -> 诊断 -> 策略 -> 评测”展示，不能只展示向量库或检索结果。

MVP 问题标签：

| 问题 | 可能原因 | 优化方向 | 必须评测 |
|---|---|---|---|
| 找不到 | chunking、query rewrite、召回不足 | 改 chunk、rewrite、hybrid search | hard retrieval recall |
| 找错租户 | ACL、tenant filter、metadata 错误 | policy filter、tenant-scoped index | tenant ACL red team |
| 引用不可信 | citation 缺失、context pack 失真 | citation check、source grounding | citation precision |
| 过期知识 | 文档版本、index 版本未绑定 | freshness、versioned index | freshness regression |
| 答案胡编 | context 不足、模型越界补全 | answerability gate、abstain | groundedness |
| 记忆污染 | memory 与 RAG 边界混淆 | memory retrieval policy | memory boundary eval |

RAG 页面过关标准：

- 学习者能说明 RAG 是受控工具链路的一部分，不能绕过 Tool Gateway / Policy。
- 学习者能为任一 RAG 问题选择至少一个诊断指标和一个阻塞条件。
- 学习者能说明“检索到了”为什么不等于“可以发布”。

### 7.12 LLM-Wiki 知识层页面要求

目的：

让学习者理解“资料进入课程”本身也需要治理。GitHub 项目、RAG 技术、LLM 课程和外部文章都必须先经过来源审核、知识卡沉淀和版本记录。

页面结构：

```text
左侧：KnowledgeTopic 主题树
中间：KnowledgeCard 知识卡
右侧：SourceReview 来源审核 + KnowledgeVersion 版本记录
底部：ImportQueue 导入队列 + 低分回流
```

必须展示：

- 来源 URL、source_files、license_status、fetched_at、reviewed_at。
- adoption_mode：pattern_only / taxonomy_only / course_reference / rag_diagnostic_reference / do_not_copy。
- review_status：draft / needs_review / approved / deprecated / blocked_by_license。
- freshness 提示：最新、需复核、已过期、不可采用。
- 与 Phase、RAGDiagnostic、EvalCase、RestatementCard 的映射。

交互：

- 点击来源，显示为什么能采用或不能采用。
- 点击知识卡，显示中文学习解释、canonical terms 和 source_files。
- 点击版本，显示变更原因和替代版本。
- 点击低分回流，显示它将修复哪个 Concept、FailureCase、EvalCase 或 RestatementCard。

验收：

- 学习者必须能说清“知识卡不是事实本身”。
- 复述评分 >=3，答案必须包含来源、审核状态、采用方式和低分回流对象。
- 如果学习者认为 star 高就能直接采用，或 LLM 生成卡片就能直接进课程，不通过。

## 8. 核心交互规范

### 8.1 点选层级

点击任一架构层后，必须出现四段：

```text
白话解释
工单故事映射
少了会出什么事故
怎么验收
```

### 8.2 正常/失败路径切换

每个流程图必须支持：

- 正常路径。
- 坏设计路径。
- 阻塞点。
- 应由哪层负责。

### 8.3 复述卡

每个页面底部提供：

```text
这一页解决的是 ________。
它防止的事故是 ________。
负责这一层的是 ________。
如果没有它，会 ________。
我用 ________ 验收。
```

### 8.4 学习评分

评分标准：

| 分数 | 含义 |
|---|---|
| 0 | 完全说不出，或把 mock 当生产系统 |
| 1 | 只背术语，不能解释事故 |
| 2 | 能说大概意思，但缺负责层或验收证据 |
| 3 | 能同时说出事故、负责层和最小验收证据 |
| 4 | 能指出坏设计、失败路径、停止条件并提出修正 |
| 5 | 能指挥 Codex/subagent 进入实现、验证和复盘 |

MVP 可只做本地临时评分，不需要账号。

### 8.5 语言与术语策略

MVP 默认采用中文优先双语：

- 导航、按钮、复述题、事故说明、学习任务使用中文。
- 核心工程术语保留英文括注，例如“运行时 Runtime”“策略 Policy”“检索增强 RAG”“轨迹 Trace”“评测 Eval”。
- 首次出现术语时必须给白话解释和事故示例。
- schema 字段、source_files、外部项目名、代码标识保留英文。
- 用户复述可以完全使用中文。

固定边界提示必须中文优先：

```text
学习模式 Learning mode
模拟数据 Mock data
不执行真实操作 No real execution
来源文件 Source files
```

禁止主要按钮全英文。按钮必须是中文动作，例如：

- 查看受控链路。
- 比较坏设计路径。
- 记录复述评分。
- 判断是否阻塞。
- 加入下次复习。

## 9. 内容模型

### 9.1 Phase

```json
{
  "id": "phase-03",
  "title": "Agent 网关与工具治理",
  "summary": "防止工具调用失控",
  "story_mapping": "退款工具不能由模型直接执行",
  "failure_risk": "越权退款",
  "core_artifacts": ["Gateway 边界图", "PolicyDecisionInput", "Audit Event"],
  "restatement_questions": [],
  "source_files": []
}
```

### 9.2 Concept

```json
{
  "id": "tool-gateway",
  "name": "Tool Gateway",
  "plain_language": "工具仓库管理员",
  "why_exists": "防止模型直接拿危险工具",
  "missing_failure": "模型被诱导后直接退款",
  "phase": "phase-03",
  "validation": "所有工具调用必须经过 schema 和 policy"
}
```

### 9.3 FailureCase

```json
{
  "id": "failure-repeat-refund",
  "title": "retry 重复退款",
  "bad_design": "没有 operation_id",
  "accident": "工具成功但 Agent 以为失败，重试后重复退款",
  "responsible_layers": ["Runtime", "Tool Gateway", "Audit"],
  "blocking": true,
  "regression_case": true
}
```

### 9.4 TraceEvent

```json
{
  "trace_id": "trc_ticket_refund_001",
  "run_id": "run_001",
  "step_id": "step_003",
  "span_type": "tool_call",
  "layer": "Tool Gateway",
  "event": "tool_call_requested",
  "verdict": "pending_policy",
  "audit_required": true
}
```

### 9.5 EvalCase

```json
{
  "case_id": "eval_cross_tenant_retrieval",
  "type": "red_team",
  "target_layer": "Policy/RAG",
  "expected": "deny",
  "release_blocking": true
}
```

### 9.6 RestatementCard

```json
{
  "phase": "phase-03",
  "prompt": "ToolCall 是 ________，不是 ________。",
  "expected_keywords": ["申请", "执行许可"],
  "minimum_expected_parts": ["accident", "responsible_layer", "evidence"],
  "minimum_score_to_continue": 3
}
```

### 9.7 EnhancedPrompt

用于把用户原始问题转成更适合 Codex 执行的任务提示。它是教学对象，不是隐藏实现细节。

```json
{
  "id": "enhanced_prompt_phase_06_memory_001",
  "phase": "phase-06",
  "raw_user_question": "继续讲记忆系统",
  "enhanced_prompt": "请用 Design-only 方式讲 Phase 6 记忆系统：先说明本阶段防止什么失控，再用退款工单解释短期记忆、长期记忆、事件记忆和语义记忆的边界；必须包含记忆写入门禁、TTL、撤销、跨租户召回失败样例、复述题和评分标准。",
  "constraints": ["不写代码", "中文优先", "必须包含事故", "必须包含验收证据"],
  "expected_outputs": ["设计卡", "失败样例", "评审问题", "复述卡"],
  "stop_conditions": ["学习者把长期记忆当默认写入", "说不出撤销和审计证据"]
}
```

### 9.8 SubagentTask

用于教用户何时应该调用 planner、researcher、reviewer、verifier，以及如何限制 subagent。

```json
{
  "id": "subagent_task_research_rag_001",
  "phase": "phase-07",
  "recommended_role": "researcher",
  "why_this_role": "涉及最新 RAG 项目、评测方法和外部资料，需要来源和日期",
  "permission_scope": "read_only",
  "allowed_scope": ["07-RAG问题诊断与优化", "10-GitHub项目调研", "22-评测集"],
  "task_prompt": "只读核验 RAG 诊断器是否覆盖 chunking、ACL、citation、freshness、groundedness、memory boundary，并返回证据和缺口。",
  "expected_evidence": ["source_file", "line_or_section", "risk", "confidence"],
  "stop_condition": "找到 P0/P1 缺口后停止展开无关资料",
  "main_thread_merge_rule": "按证据合并，不按 subagent 结论投票"
}
```

### 9.9 RAGDiagnostic

用于把 RAG 学习从“检索链路”升级为“问题诊断与优化”。

```json
{
  "id": "rag_diagnostic_cross_tenant_001",
  "problem_label": "找错租户",
  "symptom": "检索命中了不属于当前租户的政策文档",
  "likely_causes": ["tenant_filter_missing", "metadata_mismatch", "shared_index_acl_gap"],
  "diagnostic_metrics": ["tenant_acl_violation_rate", "forbidden_citation_count"],
  "optimization_options": ["tenant-scoped index", "policy filter before retrieval", "citation tenant check"],
  "eval_case_id": "eval_cross_tenant_retrieval",
  "release_blocking": true,
  "responsible_layers": ["Policy", "Tool Gateway", "RAG"],
  "restatement_question": "为什么 RAG 检索命中不等于可以引用？"
}
```

### 9.10 LongTaskReliabilityMetric

用于让长线任务准确率可视化，而不是只说“可恢复”。

```json
{
  "id": "long_task_retry_idempotency_001",
  "phase": "phase-04",
  "metric_name": "重复副作用率",
  "plain_language": "同一个退款操作重试后不应重复执行",
  "target": "0 duplicate side effects in regression set",
  "failure_case": "retry 重复退款",
  "evidence_source": "mock_trace_retry_refund_001",
  "release_blocking": true,
  "related_eval_cases": ["eval_retry_duplicate_refund", "eval_checkpoint_resume_correctness"]
}
```

## 10. 前后端架构

### 10.1 MVP 架构

```text
Next.js App
-> Local JSON / MDX Content
-> Mock Run Data
-> Client-side State
-> Static Export or Local Dev Server
```

MVP 不需要后端。

### 10.2 后续扩展架构

```text
Next.js Frontend
-> BFF / API Route Layer
-> FastAPI Agent Runtime Gateway
-> SQLite/PostgreSQL
-> Eval Runner
-> Trace/Audit Store
```

### 10.3 边界声明

| 层 | MVP | 后续 |
|---|---|---|
| 内容 | 本地 JSON/MDX | 内容管理与版本化 |
| run 数据 | mock JSON | FastAPI `/runs` |
| trace | mock spans | trace store |
| audit | mock events | audit writer |
| eval | mock gate result | eval runner |
| release | mock packet | release workflow |
| auth | 不做 | SSO/RBAC |

## 11. 技术栈

### 11.1 推荐技术栈

| 层 | 技术 | 理由 |
|---|---|---|
| App | Next.js App Router | 路由和内容组织清晰，后续易扩展 |
| 语言 | TypeScript | 内容模型和 UI 状态更稳 |
| 样式 | Tailwind CSS | 快速建立一致设计系统 |
| 组件 | shadcn/ui | 可控、可扩展、适合工具型界面 |
| 图标 | lucide-react | 工具界面符号清晰 |
| 链路图 | React Flow | 适合 Gateway/Runtime/Policy 节点图 |
| 状态 | Zustand | MVP 简洁，后续可替换 |
| 图表 | Recharts | Eval、成本、case 分布可视化 |
| 内容 | MDX + local JSON | 文档内容和结构化数据并存 |
| 测试 | Vitest + Playwright | 后续实现时做交互和可视化回归 |

### 11.2 不推荐 MVP 使用

- 复杂 3D。
- 大型 BI 框架。
- 自研可视化引擎。
- 重型 workflow editor。
- 真实数据库。
- 真实用户登录。

### 11.3 后端技术栈延续

后端后续沿用现有工程规划：

- FastAPI。
- Pydantic。
- SQLite -> PostgreSQL。
- pytest。
- JSON trace。
- OpenTelemetry 后续接入。

前端不得重新发明后端契约，必须消费 Runtime/Gateway 的结构化数据。

## 12. 设计系统

### 12.1 设计调性

关键词：

```text
安静
可信
可扫描
学习导向
工业控制台
不营销
不炫技
```

不使用：

- 大面积紫蓝渐变。
- 营销 hero。
- 装饰性 bento card 墙。
- 夸张圆角。
- 只为好看而存在的插画。

### 12.2 信息密度

原则：

- 首页低密度，避免压迫。
- 学习页中密度，突出一阶段一个重点。
- Trace/Eval/Release 页较高密度，但必须可扫描。

### 12.3 色彩语义

| 语义 | 颜色建议 | 用途 |
|---|---|---|
| 信息/当前选择 | 蓝 | 当前节点、选中路径 |
| 通过 | 绿 | eval pass、policy allow |
| 需要审批 | 黄/琥珀 | approval、pending |
| 阻塞/失败 | 红 | deny、release block、critical |
| 记忆/上下文 | 紫，少量使用 | Memory 相关节点 |
| 中性背景 | 灰/白/近黑 | 主界面 |

颜色必须服务状态，不做装饰。

### 12.4 字体与排版

- 中文界面优先使用系统字体。
- 标题短，避免大段解释堆在卡片里。
- 表格用于对比，流程用于链路，卡片用于学习产物。
- 页面标题不超过一行。
- 按钮文案必须是动作：开始、查看失败、生成复述卡、判断是否阻塞。

### 12.5 组件规范

核心组件：

- PhaseSidebar。
- LearningHeader。
- FlowCanvas。
- NodeDetailDrawer。
- FailureCasePanel。
- RestatementCard。
- GateDecisionTable。
- TraceTimeline。
- AuditEventPanel。
- EvalCaseMatrix。
- ReleasePacketViewer。
- ProgressStepper。

每个组件必须定义：

- 默认态。
- 选中态。
- 空态。
- 加载态。
- 错误态。
- 禁用态。

### 12.6 图形语法

| 概念 | 表达方式 |
|---|---|
| Gateway | 闸门节点、allow/deny 分叉 |
| Runtime | 时间线、状态机节点 |
| Policy | 决策卡、三态标签 |
| Memory | 生命周期泳道 |
| Eval | case 矩阵、阻塞标记 |
| Trace | span 树、事件流 |
| Audit | 不可变事件卡 |
| Release | 版本组合和门禁 checklist |

### 12.7 Product Design 高级感执行标准

这里的高级感不是“更炫”，而是更像成熟产品团队做出的学习型工业控制台。

必须做到：

| 维度 | 可执行要求 | 不通过样子 |
|---|---|---|
| 信息架构 | C 首页、A 链路、B 事故三层清晰，用户 30 秒内知道当前位置 | 首屏像课程海报或泛 dashboard |
| 视觉层级 | 页面标题、当前任务、主画布、证据面板、复述条层级稳定 | 所有卡片同等重量，扫不出主次 |
| 状态语义 | allow、deny、approval、blocked、low score、mock boundary 都有颜色 + 文案 + 图标 | 只靠颜色表达状态 |
| 密度控制 | 首页低密度，学习页中密度，Trace/Eval 高密度但可扫描 | 到处空洞或到处拥挤 |
| 组件克制 | 用表格、时间线、节点图、tabs、drawer、segmented control 表达功能 | 大圆角装饰卡、渐变背景、装饰插画 |
| 文字质量 | 中文主文案短、准、可复述；英文只做术语锚点 | 中英混杂、英文抢主视觉 |
| 交互节奏 | 每次点击只展开一个学习焦点，同时保留路径上下文 | 一次弹出太多解释 |
| 可持续迭代 | 低分能回到 Concept、FailureCase、EvalCase、RestatementCard | 只显示分数，不改变下一轮学习 |

Product Design 产物进入原型前必须经过高级感检查：

```text
是否一眼知道当前 Phase？
是否一眼知道这是学习模式而非生产系统？
是否一眼知道当前页面要解决哪个事故？
是否能找到负责层和验收证据？
是否能提交或查看复述评分？
是否有低分回流路径？
是否没有营销式 hero、装饰渐变、真实生产按钮？
```

若任一问题为否，不能进入前端实现。

## 13. 可访问性与易学性

### 13.1 易学性原则

- 每屏只讲一个核心判断。
- 每个术语第一次出现必须有白话解释。
- 每个模块必须有“少了会怎样”。
- 每节课必须有复述卡。

### 13.2 可访问性

- 文本对比度满足 WCAG AA。
- 状态不能只靠颜色表达，必须有文字标签。
- 关键流程可键盘导航。
- 图形节点必须有文本替代说明。
- 表格在小屏上可横向滚动或转为卡片。

## 14. 持续迭代机制

### 14.1 内容版本化

每个学习对象都有：

```json
{
  "content_version": "2026-07-01.1",
  "source_files": [],
  "last_reviewed": "2026-07-01",
  "phase": "phase-03",
  "owner": "course"
}
```

### 14.2 学习反馈闭环

如果学习者复述低于 3 分：

1. 记录卡点。
2. 归类到 Concept。
3. 生成重讲任务。
4. 更新对应学习卡。
5. 下次显示更低门槛解释。

### 14.2.1 学习记录对象

每次复述都要留下可迭代记录：

```json
{
  "learning_session_id": "mock_session_001",
  "phase": "phase-05",
  "topic": "RAG boundary",
  "question": "为什么 RAG 检索结果不能直接可信？",
  "answer_language": "zh-CN",
  "score": 2,
  "contains_accident": false,
  "contains_responsible_layer": true,
  "contains_evidence": false,
  "misconception_tags": ["rag_is_truth"],
  "remediation_task": "重讲 RAG 证据边界",
  "feedback_targets": ["Concept", "FailureCase", "RAGEvalCase", "RestatementCard"]
}
```

### 14.2.2 低分回流规则

| 分数 | 前端行为 | 内容回流 |
|---|---|---|
| 0-2 | 阻止进入下一阶段，显示重讲任务 | 改写 Concept，补 FailureCase 和 RestatementCard |
| 3 | 允许进入下一阶段，但保留卡点 | 生成 open blocker，下次复习 |
| 4 | 进入下一阶段 | 把好复述沉淀为示例 |
| 5 | 进入下一阶段并生成工程转化建议 | 生成 Implementation-later backlog |

低分不能只存在本地评分里，必须生成至少一个可追踪回流目标。

### 14.3 失败案例回流

每个新增事故都转成：

- FailureCase。
- EvalCase。
- RestatementCard。
- GateDecision。

例如：

```text
事故：重复退款
-> FailureCase：缺 operation_id
-> EvalCase：retry duplicate side effect
-> GateDecision：阻塞发布
-> RestatementCard：为什么 retry 不能重复副作用？
```

### 14.4 版本迭代节奏

| 版本 | 目标 |
|---|---|
| v0.1 | PRD、信息架构、视觉系统、mock 数据模型 |
| v0.2 | 静态可视化原型 |
| v0.3 | 可点击链路图和 Phase 学习页 |
| v0.4-pre | 原型前冻结包：页面状态矩阵、mock 数据字典、逐页验收脚本、学习验证脚本 |
| v0.4 | Product Design 低保真可点击原型，覆盖 Trace 回放、Eval 门禁和 LLM-Wiki 知识层 mock |
| v0.5 | 复述评分和学习记录 |
| v1.0 | 可作为课程主入口使用 |

## 15. 实施阶段计划

### 15.1 Phase A：Open Design PRD

目标：

把本 PRD 评审到可执行。

产物：

- PRD。
- 信息架构。
- 页面清单。
- mock 数据模型。
- 设计系统声明。
- 不做事项。

硬验收：

- 用户能回答“为什么加前端、为什么不做生产控制台、为什么先不写代码”。
- PRD 必须包含 MVP 页面范围、非目标、mock 数据边界、source_files 规则和生产误读防护。
- 若用户或执行者仍把本 PRD 理解为真实生产控制台需求，不通过。

### 15.2 Phase B：低保真线框

目标：

不写代码，先定义每个页面布局。

产物：

- 学习首页线框。
- 全链路画布线框。
- Phase 学习页线框。
- Trace/Eval/Release 页面线框。

硬验收：

- 每个页面都绑定 Phase、事故、防护层、source_files、复述题和 mock 标识。
- 每页至少有一个坏设计案例和一个停止条件。
- 任一页面没有 `学习模式 Learning mode / 模拟数据 Mock data / 不执行真实操作 No real execution` 标识，不通过。

### 15.3 Phase C：视觉探索

目标：

使用 Product Design 插件或 open design 生成 3 个视觉方向。

方向限制：

- 工业控制台。
- 高可读信息图。
- 安静可信。

硬验收：

- 视觉方向必须通过评分表：状态色语义、信息密度、可访问性、非营销化、非生产误导。
- 不允许营销式 hero、大面积装饰渐变、真实生产操作按钮或真实发布按钮。
- 关键状态不能只靠颜色表达，必须有文字或图标辅助。

### 15.4 Phase D：静态原型

目标：

在 Implementation-later 候选阶段，用本地 mock 数据做可点击前端。它仍然不是生产控制台。

产物：

- Next.js 项目。
- 7 个 MVP 页面。
- mock JSON。
- 可视化组件。

验收：

- 本地原型可运行，并且所有页面标识 `学习模式 Learning mode / 模拟数据 Mock data / 不执行真实操作 No real execution`。
- 不接真实后端。
- 页面需求追踪表完整：页面 -> PRD 小节 -> mock 数据 -> 复述卡 -> source_files。

### 15.5 Phase E：学习验证

目标：

验证前端是否真的帮助学习。

方法：

- 学习者看图后回答复述卡。
- 对比看图前后评分。
- 低于 3 分的概念进入重讲队列。

硬验收：

- Phase 0.1、2、3、4、6、7、8、9、10 必须记录同一问题的看图前后 0-5 分。
- RAG 诊断器必须至少覆盖 3 类问题的看图前后评分：找不到、找错租户、引用不可信。
- 看图后复述评分必须 >=3，且答案包含事故、负责层和证据。
- 连续两次低于 3，或看图后没有分数提升，停止扩前端，并回流 Concept、FailureCase、RestatementCard。

### 15.6 Phase F：Implementation-later 接入

目标：

后续接 FastAPI Runtime demo/sandbox，不接真实生产系统。

前提：

- Design-only 教学验证通过。
- 后端 Runtime/Gateway 有稳定 mock/API。
- trace/audit/eval 数据结构定稿。

禁止提前进入 Phase F 的情况：

- PRD、线框、视觉方向、学习验证任一项未通过。
- 还没有重新核验前端/后端依赖的 release、license、安全公告和维护状态。
- trace、audit、eval、policy、tool registry 的数据结构还不能被稳定引用。
- 需要接入真实凭据、真实企业数据或真实生产写操作。

### 15.7 每一步深度思考模板

每进入一个计划步骤，都先按下面 8 个问题审查。任何一项答不清，就不要进入下一步。

| 思考问题 | 为什么问 | 通过样子 | 没通过的样子 |
|---|---|---|---|
| 这一步防什么失控？ | 避免为做页面而做页面 | 能说出具体事故，例如重复退款、越权工具、记忆污染 | 只说“更清晰”“更好看” |
| 它属于哪个 Agent 层？ | 避免概念混在一起 | 能落到 Runtime、Gateway、Memory、Eval、Observability、Sandbox 或 Governance | 只说“Agent 自己处理” |
| 输入是什么？ | 避免凭空设计 | 有 source_files、上一阶段产物、mock 数据或失败样例 | 只有口头想法 |
| 输出是什么？ | 避免没有交付物 | 有设计卡、线框、矩阵、复述卡、评审记录 | 只有一段说明 |
| 正常路径怎么证明？ | 防止只讲概念 | 有样例、流程、trace、评分或清单 | 只说“应该可以” |
| 失败路径怎么证明？ | 工业级设计必须看坏情况 | 有坏输入、攻击、越权、回归、恢复失败样例 | 只看 happy path |
| 学习者怎么复述？ | 保证真的学会 | 复述包含事故、负责层、验收证据，评分 >=3 | 只背术语 |
| 什么情况必须停？ | 防止范围膨胀 | 有停止条件和回流动作 | 继续扩页面、扩功能、接真实系统 |

### 15.8 Phase A-F 阶段门禁矩阵

| 阶段 | 输入 | 输出 | 硬验收 | 失败样例 | 停止条件 |
|---|---|---|---|---|---|
| Phase A：Open Design PRD | 课程地图、阶段验收清单、学习者画像、Product Design brief 约束 | PRD、页面范围、信息架构、mock 数据边界、不做事项 | 用户能回答“为什么加前端、为什么不做生产控制台、为什么先不写代码”；PRD 有明确 MVP 页面和非目标 | 只说“做个漂亮 dashboard” | 无法说清学习目标，或用户以为这就是生产产品 |
| Phase B：低保真线框 | PRD、MVP 页面矩阵、source_files | 每页线框、复述卡位置、mock 标识、坏设计入口 | 每页都绑定 Phase、事故、防护层、source_files、复述题 | 线框像泛后台，只有指标卡没有学习任务 | 任一页面没有坏设计案例或 mock 标识 |
| Phase C：视觉探索 | 线框、设计系统、生产误读防护规则 | 3 个视觉方向和评分表 | 状态色语义明确；不靠颜色单独表达；不出现营销 hero；不出现真实生产操作按钮 | 大面积渐变、装饰卡片墙、真实发布按钮 | 视觉方向削弱信息密度或诱导生产误读 |
| Phase D：静态原型 | 已通过的 PRD、线框、视觉方向、mock JSON | Next.js 候选原型、可点击链路、mock trace/eval/release | 原型可本地演示；无真实后端；无真实凭据；无真实工具调用；页面能追溯到 PRD 小节 | 做成真实控制台、接入登录/权限/真实后端 | 任何页面让学习者以为可以真实执行 |
| Phase E：学习验证 | 原型或线框、复述评分表、冷启动任务 | 看图前后复述记录、卡点列表、重讲任务 | 至少覆盖 Phase 0.1/2/3/4/6/7/8/9/10 和 RAG 诊断器；复述评分 >=3；复述必须包含事故、负责层、证据 | 看图后只能说“更懂了”，但说不出事故和门禁 | 分数无提升，或低于 3 的概念无法回流修订 |
| Phase F：Implementation-later 接入 | 已通过学习验证、稳定 mock/API、定稿数据结构、依赖复核 | 后端 API 接入计划、工程任务拆分、测试和门禁计划 | 重新核验 release/license/security；trace/audit/eval/policy/tool registry schema 稳定；有 CI/eval/sandbox 计划 | 直接接真实生产系统，边做边定契约 | 需要真实凭据、真实写操作或无法证明安全隔离 |

### 15.9 学习验证实验设计

当前不能声称“前端已经验证有效”。本阶段只能先设计验证实验，真正通过必须留下复述记录。

实验对象：

- 第一轮可以只有用户本人和 Codex 对话，但必须按同一评分规则记录。
- 后续如果有真实学习者，至少收集 3 次冷启动复述样本，再判断是否扩展前端。

实验流程：

1. 看图前，先让学习者回答本阶段过关问题。
2. 记录 0-5 分和卡点。
3. 看对应页面或线框。
4. 再次回答同一个问题，并追加一个坏设计判断题。
5. 如果评分低于 3，不能进入下一阶段，必须回流到 Concept、FailureCase、RestatementCard。

评分规则：

| 分数 | 含义 | 是否过关 |
|---|---|---|
| 0 | 完全说不出，或把 mock 当生产系统 | 不过 |
| 1 | 只背术语，不能解释事故 | 不过 |
| 2 | 能说大概意思，但说不出负责层或证据 | 不过 |
| 3 | 能说出事故、负责层、最小验收证据 | 过关下限 |
| 4 | 能补充失败路径和停止条件 | 通过 |
| 5 | 能主动指出设计风险和后续工程门禁 | 优秀 |

最低通过线：

- Phase 0.1、2、3、4、6、7、8、9、10 必须达到 3 分以上。
- RAG 诊断器至少 3 类问题必须达到 3 分以上，且答案必须包含问题标签、诊断指标、优化策略、eval case 和是否阻塞。
- 如果页面让学习者误以为系统已经生产可用，直接判 0 分。
- 如果连续两次复述低于 3，停止扩展前端，先重写对应课程说明。

## 16. 验收标准

### 16.1 学习验收

学习者能回答：

- Agent 为什么不是聊天窗口？
- ToolCall 为什么只是申请？
- Runtime 为什么不能只保存聊天记录？
- trace 和 audit 有什么不同？
- eval 为什么可以阻塞发布？
- release 为什么是版本组合？

以上问题不是“听起来知道”就算通过。通过标准是：复述评分 >=3，且答案必须同时包含事故、负责层和验收证据。

### 16.2 产品验收

- 首屏能在 30 秒内引导学习者开始。
- 每个核心页面都有明确学习目标。
- 每个核心页面都有坏设计案例。
- 每个核心页面都有复述卡。
- 第一版不需要用户写代码。

### 16.3 设计验收

- 风格统一。
- 状态颜色语义一致。
- 图形语法一致。
- 可扫描。
- 不像营销页。
- 不像生产控制台假成品。

### 16.4 技术验收

MVP 实现阶段才适用：

- TypeScript 类型通过。
- lint 通过。
- 页面在桌面和移动端不溢出。
- React Flow 节点可点击。
- mock 数据可替换。
- 无真实凭据。
- 无真实生产工具调用。

### 16.5 课程一致性验收

- 不推翻 CLI 比 UI 更适合工程教学的判断。
- 不把 UI Console 提前变成 MVP-practical。
- 不替代 Design-only 复述验收。
- 不把可视化当作生产就绪证据。

## 17. 风险与控制

| 风险 | 表现 | 控制 |
|---|---|---|
| UI 误导为生产系统 | 学习者以为能直接用 | 页面标注学习模式 Learning mode / 模拟数据 Mock data |
| 范围膨胀 | 想做登录、权限、真实后端 | PRD 明确 MVP 不做 |
| 概念固化错误 | 图画错导致误解 | 每张图配来源文件和评审 |
| 只看图不复述 | 学习者以为看懂了 | 每页强制复述卡 |
| 前端维护成本高 | 文档更新后 UI 过期 | 内容版本化和 source_files |
| 风格变营销 | 视觉好看但无学习价值 | 工业控制台风格，不做 hero |
| 技术过重 | 上复杂后端和数据库 | MVP 用本地 JSON |

### 17.1 生产误读防护规则

为了避免学习者误以为“PRD/线框/原型 = 生产可用”，所有前端相关设计遵守以下规则。

必须使用的文案：

- `学习模式 Learning mode`
- `模拟数据 Mock data`
- `不执行真实操作 No real execution`
- `来源文件 Source files`
- `发布学习模拟 Release learning simulation`

禁止在 MVP 页面中出现：

- `立即发布到生产`
- `连接真实生产系统`
- `执行真实退款`
- `管理真实用户权限`
- `导入真实企业凭据`
- `生产 SLO 已达标`

按钮命名规则：

| 错误按钮 | 替代按钮 |
|---|---|
| 发布 | 模拟发布判断 |
| 执行工具 | 查看 ToolCall 申请 |
| 连接系统 | 查看 mock 集成边界 |
| 审批通过 | 查看审批条件 |
| 回滚生产 | 查看 rollback 学习样例 |

数据命名规则：

- 所有 run、trace、audit、eval、release packet 默认加 `mock_` 前缀。
- 所有页面都必须能追溯到 `source_files`。
- 不展示真实用户、真实订单、真实凭据、真实企业系统地址。
- 不用“生产已就绪”描述 PRD、线框或静态原型。

## 18. 停止条件

如果出现以下情况，停止前端扩展：

- 前端开始要求学习者写代码。
- 前端开始接真实工具或凭据。
- 可视化不能提升复述质量。
- 页面不能回答“防什么失控”。
- UI 变成展示炫技而不是学习。
- 维护一个图需要同步大量文档且容易出错。
- 学习者把可视化误认为生产系统已完成。

## 19. 设计 brief

### 19.1 Product Design brief

产品：

```text
工业级 Agent 学习可视化控制台。
```

目标：

```text
帮助半懂学习者通过工单故事、链路图、失败推演、trace 回放和门禁判断，理解 Agent Runtime/Gateway 工业级设计。
```

视觉方向：

```text
安静、可信、可扫描、工业控制台，不做营销页，不做大面积渐变，不做装饰性卡片墙。
```

交互级别：

```text
MVP 原型阶段：静态内容 + 关键控件可点击 + mock 数据回放。
Implementation-later：完整功能交互。
```

### 19.2 下一步进入 Product Design 的条件

只有当本 PRD 被确认后，才进入：

1. 低保真线框。
2. 三个视觉方向。
3. 选定视觉方向。
4. 前端原型实现。

## 20. 最终判断

建议加入前端，但只作为学习可视化：

```text
加课程可视化，不加真实生产前端。
先做 PRD 和线框，再做视觉方向，最后才评估是否进入前端实现。
前端必须持续服务复述、坏设计判断、评审和验收。
```

这个学习项目的长期形态不是“文档 + 页面”，而是：

```text
课程文档
-> 可视化学习控制台
-> mock run / mock trace
-> 复述评分
-> 失败案例回流
-> 后续真实 Runtime/Gateway 实现
```

它最终要帮助学习者做到：

```text
我不写代码，也能判断 Agent 设计是否工业级；
我能用可视化说明每一层防什么失控；
我能让 Codex 根据这些设计进入工程实现和验证。
```
