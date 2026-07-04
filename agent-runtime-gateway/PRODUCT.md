# Product

## Register

product

## Users

主要用户是半懂学习者：听过 Agent、RAG、MCP、记忆、评测和多智能体，但还没有稳定的系统图。他不想写代码，也不想背 API，希望通过和 Codex 对话、看图、复述、判断坏设计，逐步学会工业级 Agent Runtime/Gateway 的设计和验收。

第二类用户是未来 AI 产品负责人、Agent 架构负责人和 Codex 协作者。他们需要把抽象设计转成 PRD、门禁、评测、trace、audit、release packet 和后续工程任务。

使用场景是长时间学习和复盘。用户通常在桌面端阅读、点选、对照文档、追问 Codex，并阶段性提交 Design-only 产物。

用户的真实偏好是：不写代码、不记代码，而是在和 Codex 交互时逐步学会如何设计系统、如何追问、如何调用 subagent、如何评审和验收。

## Product Purpose

这个产品把工业级 Agent 教学过程可视化。它不是生产控制台，也不是营销页，而是学习控制台：用工单故事、链路图、失败推演、trace 回放、eval 门禁、LLM-Wiki 知识层和 release 学习模拟，帮助用户理解 Agent 不是聊天窗口，而是受控长线任务系统。

成功标准不是页面漂亮，而是用户能复述：

- 这一步防什么失控。
- 哪一层负责拦截、记录、恢复或评测。
- 缺少这一层会造成什么事故。
- 当前 Design-only 证据是什么。
- 后续 Implementation-later 需要哪些工程证据。
- 这一次应该如何增强提示词，是否需要 planner、researcher、reviewer 或 verifier subagent。
- 外部资料、GitHub 项目和 LLM 生成知识为什么必须先经过来源审核、知识卡版本和低分回流。

## Brand Personality

安静、可信、可扫描、教学导向。

语气要像经验丰富的工程导师：直接、清楚、不给幻觉，不把 demo 说成生产能力。界面要让用户感觉自己在掌控一个工业系统的学习地图，而不是被一堆概念压住。

## Language Strategy

默认采用中文优先双语：

- 导航、按钮、教学问题、复述卡、错误提示、阶段说明使用中文。
- 关键工业术语保留英文括注，例如：运行时 Runtime、网关 Gateway、策略 Policy、检索增强 RAG、轨迹 Trace、审计 Audit、评测 Eval、发布门禁 Release Gate。
- 首次出现术语时给白话解释，后续页面只保留中文主标签 + 英文短标签。
- 生成视觉方向、线框和代码原型时，界面文案优先中文；英文只作为技术锚点，不抢主视觉。

这样做的目的不是装饰，而是帮助用户既能听懂课程，又能读懂 GitHub、官方文档和英文技术资料。

## Anti-references

不要像：

- 营销 landing page。
- 大面积紫蓝渐变 SaaS 页面。
- 装饰性 bento card 墙。
- 炫技型 3D 或复杂动画。
- 真实生产治理控制台。
- no-code workflow builder。
- BI 大屏。
- 只展示指标卡、没有坏设计和复述验收的泛 dashboard。

禁止出现会误导用户的生产文案：真实发布入口、连接真实企业系统、执行真实退款、导入真实凭据、生产 SLO 已达标。

## Design Principles

1. 教学流程先于界面形式  
   每个页面先回答“这一步教什么、验证什么、什么时候停”，再决定布局。

2. 所有概念都绑定事故  
   Runtime、Gateway、Memory、Eval、Observability、Sandbox、Governance 不能只解释定义，必须展示缺失时会发生什么事故。

3. 可视化必须可复述  
   页面通过与否看复述评分。用户答案必须包含事故、负责层和验收证据。

4. Mock 边界永远可见  
   MVP 页面必须显示学习模式 Learning mode、模拟数据 Mock data、不执行真实操作 No real execution、来源文件 Source files。任何让用户误以为可以真实执行的设计都失败。

5. 为长期迭代而设计  
   内容、mock run、trace、eval case、release packet 都要能版本化，并能回流到课程文档和后续工程任务。

6. 学习记录驱动下一版  
   每次复述低分、卡点、误解和新问题，都要变成可追踪的学习 backlog，推动下一版课程、页面、评测样例和 RAG 优化。

7. Codex 协作能力也是教学对象  
   前端不仅教 Agent 系统本身，还要教用户如何指挥 Codex：先明确目标和约束，再增强提示词，必要时调用 subagent，最后按证据合并结论。

8. 外部知识必须可治理  
   GitHub star、RAG 检索命中、LLM 总结和热门课程都不能直接变成课程正文。外部资料必须先经过 KnowledgeSource、SourceReview、KnowledgeCard、KnowledgeVersion 和 ImportQueue，再进入学习页、RAG 诊断或评测样例。

## Accessibility & Inclusion

目标按 WCAG 2.2 AA 设计。正文对比度不低于 4.5:1，关键状态不能只靠颜色表达，必须有文字、图标或结构辅助。支持键盘导航、清晰 focus ring、减少动画模式、移动端可读布局。

术语解释要允许“半懂不懂”的用户进入：每个核心概念都配白话解释、事故示例和复述题。
