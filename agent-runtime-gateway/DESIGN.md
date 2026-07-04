# Design

## Design Intent

这是一个学习型产品 UI，不是营销页，也不是生产后台。设计目标是让用户在一个安静可信的控制台里，看见工业级 Agent 教学过程如何一步步推进。

物理使用场景：用户坐在桌面电脑前，左侧看课程阶段，中心看链路或时间线，右侧对照事故、证据和复述卡；他会长时间阅读、点选、追问和复盘，所以界面要克制、稳定、可扫描。

## Surface Strategy

- 默认 register：product。
- 视觉策略：restrained product UI。
- 第一屏采用 C 学习路线地图作为可操作学习入口，不做 hero。
- 核心链路采用 A 分层控制台，突出 Runtime / Gateway / Policy / Eval 的系统边界。
- 失败学习采用 B 事故推演工作台，突出事故、负责层、拦截证据和低分回流。
- 页面结构优先使用 app shell、侧边导航、顶部状态条、主工作区、右侧证据面板。
- 页面不使用卡片堆砌表达结构。卡片只用于独立对象，例如失败案例、eval case、release packet 条目。

## Color Tokens

使用 OKLCH。颜色要有语义，不做单一蓝紫主题，不做米色纸感主题。

```css
:root {
  --bg: oklch(0.985 0.006 190);
  --surface: oklch(0.965 0.008 190);
  --surface-raised: oklch(0.995 0.003 190);
  --ink: oklch(0.225 0.025 210);
  --ink-muted: oklch(0.455 0.026 210);
  --line: oklch(0.875 0.012 205);
  --accent: oklch(0.55 0.105 172);
  --accent-soft: oklch(0.925 0.04 172);
  --info: oklch(0.58 0.12 245);
  --success: oklch(0.56 0.12 145);
  --warning: oklch(0.69 0.14 78);
  --danger: oklch(0.57 0.16 28);
  --blocked: oklch(0.5 0.11 330);
  --focus: oklch(0.62 0.13 172);
}
```

语义规则：

- accent 只用于当前阶段、主要行动和可点击链路节点。
- warning 表示需要人工判断或复述不足。
- danger 表示越权、泄漏、危险工具、生产误读。
- blocked 表示 eval 或 release gate 阻塞。
- success 只表示通过了明确门禁，不表示生产可用。

## Typography

- 字体：中文优先使用 `system-ui`、`Microsoft YaHei UI`、`PingFang SC`、`Noto Sans CJK SC`，英文和代码可使用 Inter 或 system-ui。
- 不使用 display font。
- 正文字号 14-16px。
- UI 标签 12-13px。
- 页面标题 24-28px。
- 面板标题 16-18px。
- 行高 1.45-1.65。
- 字间距保持 0，不使用负 letter spacing。

## Language And Localization

默认界面是中文优先双语。

主标签使用中文，英文作为技术括注或副标签：

| 中文主标签 | 英文辅助标签 | 用途 |
|---|---|---|
| 学习模式 | Learning mode | 顶部状态 |
| 模拟数据 | Mock data | 顶部状态 |
| 不执行真实操作 | No real execution | 顶部状态 |
| 来源文件 | Source files | 证据面板 |
| 运行时 | Runtime | 架构节点 |
| 网关 | Gateway | 架构节点 |
| 策略 | Policy | 决策节点 |
| 检索增强 | RAG | RAG 模块 |
| 轨迹 | Trace | 调试证据 |
| 审计 | Audit | 合规证据 |
| 评测 | Eval | 门禁模块 |
| 发布门禁 | Release Gate | 发布学习模拟 |
| 知识层 | LLM-Wiki | 来源审核、知识卡、版本记录 |
| 来源审核 | SourceReview | 判断外部资料能否进入课程 |
| 知识卡 | KnowledgeCard | 可复述、可审核、可回流的学习单元 |

文案层级：

- 导航和按钮只用中文，例如“查看受控链路”“记录复述评分”“判断是否阻塞”。
- 架构节点使用中文 + 英文短标签，例如“策略 Policy”。
- 教学说明先用中文解释，再在括号中保留英文术语。
- 代码、schema、字段名和外部项目名保留英文。

排版要求：

- 双语标签必须允许换行，不能压缩到溢出。
- 移动端可隐藏英文副标签，但术语详情页必须保留中英对照。
- 任何截图或生成图如果英文过多，必须在进入原型前重做中文化版本。

## Layout System

桌面默认布局：

```text
Top status bar
Left phase rail | Main visual workspace | Right evidence panel
Bottom reflection / next action strip
```

建议尺寸：

- 左侧阶段栏：240-280px。
- 主工作区：自适应，最小 640px。
- 右侧证据面板：320-380px。
- 顶部状态条：56-64px。
- 页面最大内容宽度不硬锁，工具型界面允许横向信息密度。

移动端：

- 左侧阶段栏折叠为顶部 segmented control。
- 右侧证据面板下移为 tabs。
- 链路图切换为纵向 stepper。

## Components

核心组件必须包含 default、hover、focus、active、disabled、loading、error 状态。

- PhaseRail：阶段导航、完成度、卡点标记。
- LearningModeBadge：学习模式 / 模拟数据 / 不执行真实操作。
- FlowCanvas：运行时 Runtime / 网关 Gateway / 策略 Policy / RAG / 记忆 Memory / 评测 Eval / 发布门禁 Release Gate 节点图。
- EvidencePanel：事故、负责层、source_files、验收证据。
- RestatementCard：复述题、0-5 评分、卡点记录。
- FailureCaseList：坏设计、事故链路、阻塞级别。
- TraceTimeline：mock run 的 step/span/event 时间线。
- EvalGateTable：case 类型、版本、结果、是否阻塞。
- ReleasePacketView：版本组合、重跑评测、rollback 目标。
- GateDecisionBanner：pass、review、blocked、stop。
- RAGProblemLens：问题标签、诊断路径、优化策略、RAG eval case。
- LLMWikiKnowledgeLayer：来源队列、来源审核、知识卡、版本记录和低分回流。
- KnowledgeSourcePanel：外部来源 URL、license、freshness、采用方式和 source_files。
- SourceReviewQueue：待审核、已通过、已废弃、license 阻塞等状态。
- KnowledgeVersionDiff：知识卡版本差异、变更原因和替代版本。
- MemoryLifecycleLane：写入门禁、TTL、撤销、过期、审计。
- SandboxRiskSelector：工具风险、sandbox profile、人工审批条件。
- MultiAgentHandoffMap：planner、executor、reviewer、verifier 的输入输出和停止条件。
- PromptEnhancementPanel：原始提问、增强提示词、推荐 subagent、期望证据。
- LearningBacklogBoard：卡点、重讲任务、内容回流、下次复习。

## Premium Craft Standard

高级感来自信息秩序和产品成熟度，不来自装饰。

| 维度 | 必须做到 | 禁止 |
|---|---|---|
| 首屏 | C 路线地图直接显示当前 Phase、当前任务、复述状态和下一步 | 营销 hero、愿景大字、装饰背景 |
| 主工作区 | A 链路页清楚显示节点、路径、阻塞点和证据流 | 泛 dashboard 指标卡堆叠 |
| 事故页 | B 工作台一次聚焦一个事故，同时保留其他事故入口 | 一屏塞满所有事故 |
| 知识层 | LLM-Wiki 只展示来源审核、知识卡状态、版本和回流 | GitHub star 排行榜、资料瀑布流 |
| 视觉层级 | 任务、链路、证据、复述四层分明 | 所有卡片同样抢眼 |
| 色彩 | 语义色只表达状态，且配文字和图标 | 紫蓝渐变、单一色系、只靠颜色传达 |
| 组件 | tabs、drawer、segmented control、timeline、matrix、stepper 各司其职 | 用圆角卡片替代所有结构 |
| 文字 | 中文主标签短而准，英文只做术语锚点 | 英文主导或中英混乱 |
| 学习闭环 | 低分直接进入卡点和回流对象 | 只显示分数，不改变下一步 |

设计 QA 时必须逐项检查：

```text
当前 Phase 是否可见？
当前学习问题是否可见？
事故和负责层是否可见？
mock 边界是否可见？
复述评分和低分回流是否可见？
是否没有真实生产操作暗示？
```

## Radius, Borders, Shadows

- 默认 radius：8px。
- 小控件 radius：6px。
- 不使用 24px 以上大圆角。
- 默认分隔优先用线和间距，不依赖阴影。
- 不在同一元素上同时使用 1px 边框和大模糊阴影。

## Motion

- 只用于状态变化：节点展开、路径切换、评分提交、门禁状态变化。
- 默认 150-220ms。
- 支持 `prefers-reduced-motion: reduce`。
- 不做页面加载编舞，不做装饰性运动。

## Copy Rules

- 按“动作 + 对象”写按钮，例如“查看受控链路”“记录复述评分”“模拟发布判断”。
- 不使用营销词。
- 不使用“生产已就绪”描述 PRD、线框、静态原型。
- 每页都要出现固定 mock 边界提示：学习模式 Learning mode / 模拟数据 Mock data / 不执行真实操作 No real execution / 来源文件 Source files。
- 默认中文按钮，不用英文按钮。英文只出现在术语括注、schema 字段、外部工具名和技术说明中。

## Sustainable Learning Iteration

每一轮学习都要留下可迭代证据：

- 用户复述原文。
- 0-5 评分。
- 卡点标签。
- 误解类型。
- 对应 Phase。
- 对应系统层。
- 回流动作。

低分复述不能只作为记录，必须推动下一轮内容更新：

```text
低分复述
-> 术语解释改写
-> 失败案例增补
-> RAG 评测样例增补
-> SourceReview / KnowledgeCard 修订
-> 复述卡重写
-> 页面线框或交互更新
-> 下一轮学习验证
```

## Implementation Notes

MVP 前端技术建议：

- Next.js App Router
- TypeScript
- Tailwind CSS
- shadcn/ui
- lucide-react
- React Flow
- Zustand
- Recharts
- MDX + local JSON
- Vitest + Playwright

后续后端延展：

- FastAPI Runtime/Gateway demo/sandbox
- Pydantic schema
- SQLite 到 PostgreSQL
- JSON trace/audit store
- eval runner
- OpenTelemetry later

MVP 不接真实后端、真实凭据、真实企业数据、真实生产写操作。
