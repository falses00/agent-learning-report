# 大厂 Agent 岗位面试知识地图（2026）

- 核验日期：2026-08-20
- 国内岗位下次复核：2026-09-03
- 国际岗位、GitHub 与社区样本下次复核：2026-09-20

## 1. 一句话定义与真实性边界

**大厂 Agent 面试验收，是用可运行项目证据回答编码、系统设计、AI 深挖和行为追问，而不是背框架名词。**

本章的岗位能力来自核验日仍能访问的公司官方招聘页；面试方式来自公司官方招聘说明。后面的 OpsPilot 难题是根据公开要求构造的综合训练题，不是 OpenAI、Google、Amazon、TikTok、Microsoft 或 Anthropic 的泄露原题，也不能保证某场面试按同样顺序进行。

来源分三层：A 类企业官方岗位只能证明核验日的职责要求；B 类 GitHub 上游仓库只能证明工程实现与活跃状态；C 类 Linux DO、牛客等带日期社区样本只能提出训练假设。三类证据不能互相冒充。

公开职位会关闭。职位关闭后只能进入历史证据区，不继续作为“当前岗位”宣传。课程不承诺 offer、职级、薪资或特定公司的录用结果。

## 2. 最新官方岗位交集

| 官方岗位 | 核验到的能力信号 | 对课程的影响 |
|---|---|---|
| [OpenAI AI Systems Engineer, Codex Agents](https://openai.com/careers/ai-systems-engineer-codex-agents-san-francisco/) | harness、execution loop、sandbox、state/workflow、eval/debug、可靠性、延迟与成本 | S1、S4、S6-S8 必须能从证据跨层归因 |
| [OpenAI Performance & Systems Engineer, Codex](https://openai.com/careers/performance-and-systems-engineer-codex-san-francisco/) | agent behavior、inference、container orchestration、profiling、速度/成本/体验 | S7、S10 必须加入性能预算和 profile |
| [Google Senior ML Engineer, AI-Driven SDLC Quality](https://www.google.com/about/careers/applications/jobs/results/113159848073274054-senior-ml-engineer/) | LLM/Agent、online/offline eval、dataset、robustness、security、reliability | 作品不能只有 demo，必须有数据集和发布门禁 |
| [Amazon Sr. Applied Scientist, Ads AI Core Infrastructure](https://www.amazon.jobs/en/jobs/10380588/sr-applied-scientist-ads-ai-core-infrastructure) | MCP、orchestration、context optimization、RAG、实时数据、低延迟、实验与生产化 | S3、S6、S7 要做同预算实验并解释线上约束 |
| [TikTok AI Agent Engineer, Search](https://lifeattiktok.com/search/7665617702183225653) | CS 基础、RAG/MCP、AI coding、测试、监控、稳定性、A/B 实验 | F0 与 Vibe Coding 不能从路线中删掉 |
| [TikTok Software Engineer, AI Agent](https://lifeattiktok.com/search/7626968373985429765) | planning、tool use、memory、multi-agent、RAG、LLMOps、系统设计 | S1-S10 要形成完整责任链，不按框架分课 |
| [TikTok AI Agent Algorithm Engineer Graduate, 2027 Start](https://lifeattiktok.com/search/7667719905318111493) | 明确希望候选人做过 runtime/harness、memory/context、RAG/tool agent 或 eval，而不只是 API 调用 | 校招作品也要包含最小 runtime 和真实工程证据 |
| [TikTok Security Engineer, Detection & Response](https://lifeattiktok.com/search/7667924371042814213) | 受控工具、权限、HITL、审计、引用、golden/regression、隐私 | S2、S3、S6-S8 是同一条可信执行链 |

共同结论不是“多学几个 Agent 框架”，而是：

1. 保留编码、数据结构、网络、数据库、并发、分布式系统和调试基础。
2. 能自己解释并实现 runtime、tool/policy、RAG、memory、eval、observability 与 security。
3. 用实验区分模型、提示词、上下文、检索、工具和基础设施问题。
4. 同时优化质量、P95 延迟、成本、容量、可靠性和用户结果。
5. 能把独立项目、开源贡献、事故复盘和量化指标变成可追问证据。

## 2A. 中国国内官方岗位基线

国内岗位不是国际岗位的翻译版。核验日可访问的官方招聘入口显示，应用落地、智能体算法、RAG/Search、Harness/Infra 与模型训练已经明显分层，但它们共同要求编码、工程交付、评测、成本与业务结果。

| 国内官方岗位 | 当前信号 | 训练落点 |
|---|---|---|
| [字节跳动 Agent 算法工程师 · AI Platform](https://jobs.bytedance.com/experienced/m/position/detail/7599598898747656453) | Agent 架构、工具、上下文、编排、Agentic RL/Post-Training | S0-S2、S5-S6：实现 loop/context/eval，并做算法消融 |
| [字节跳动大语言模型 AI 搜索 Agent 算法工程师](https://jobs.bytedance.com/experienced/m/position/detail/7473064938787244306) | LLM 训练、检索排序、搜索 Agent、线上效果 | S3、S6：拆 retrieval/rank/answer 指标与线上实验 |
| [腾讯 HR 领域大模型及 AI Agent 应用落地](https://careers.tencent.com/jobdesc.html?postId=2082043721595138048) | RAG、微调、Agent 编排、业务抽象、组件复用和交付 | S3、S9-S10：从单业务实现抽象出平台契约 |
| [腾讯混元强化训练框架研发工程师](https://careers.tencent.com/jobdesc.html?postId=2061810859658887168) | Python、Asyncio、并发、强化训练框架、LLM/Agent 工程化 | F0、S4、S6：补并发、可靠训练与性能证据 |
| [百度 2027 AIDU 智能体算法工程师](https://talent.baidu.com/jobs/detail/GRADUATE/4f1cbc80-8332-4a92-b8fa-c0132b17d47e) | planning、tool、reflection、memory、多 Agent、RAG、评测、延迟与成本 | S1-S7：机制、baseline、失败切片和上线指标都要能答 |
| [百度 2027 AIDU Agent 应用全栈工程师](https://talent.baidu.com/jobs/detail/GRADUATE/6f9c3a86-6557-409d-8fa7-e6f4c68d6765) | Planning-Acting-Reflection、Tool/API、Memory、状态、多 Agent、RAG、Eval | F0、S1-S7：前后端可运行主链与评测闭环 |
| [阿里巴巴企业级 AI Agent 平台研发](https://campus-talent.alibaba.com/campus/position/199907780033) | Agent、RAG 与企业平台模块 | S9-S10：多租户、policy、tool、release 的复用边界 |
| [华为 AI 大模型训练 / 推理系统优化](https://career.huawei.com/reccampportal/portal5/social-recruitment-detail.html?dataSource=1&jobId=28183) | Python/C++、训练可靠性、推理、量化、KV 压缩、投机推理、国产算力 | F0、S7：profile、容量、模型服务和硬件约束 |
| [华为供应链生成式 AI / Agent 应用](https://career.huawei.com/reccampportal/portal5/social-recruitment-detail.html?dataSource=1&jobId=22643) | Transformer、SFT、RAG、Agent、集群、行业需求与系统设计 | S0、S3、S10：模型、知识与行业流程共同验收 |
| [美团 LongCat 招聘](https://zhaopin.meituan.com/longcatprogram) | Agentic RL、RAG、多模态、Memory/Cognition、AI Infra 和评测 | S3、S5-S7：算法与系统必须用同一业务集评估 |
| [京东 AI 架构师](https://zhaopin.jd.com/web/job-info-detail?requementId=221903) | Agent、多 Agent、RAG+TDD AI Coding、流处理、微服务、云原生与大促 SLO | F0、S3-S4、S7、S10：高并发交付与发布门禁 |
| [DeepSeek 招聘](https://talent.deepseek.com/) | Agent Harness、Agent Infra、AI 搜索与 Agent 后端并列 | S1-S7：context、tool、memory、subagent 与性能不可只停留在 SDK |
| [MiniMax Careers](https://www.minimaxi.com/careers) | 模型算法、机器学习系统与 AI 应用并列 | 按目标岗位选择算法深挖或工程交付证据 |

国内重复信号可压成七条：Harness/Context、搜索化 RAG、质量-延迟-成本联合评测、后端与分布式、模型适配与后训练、业务平台化、上游开源证据。单个 JD 不能把某个框架升级为课程必修；只有跨公司重复信号和项目验证才能改变主线。

## 3. 官方说明中的面试方式

- [Amazon Software Development Interview Topics](https://amazon.jobs/content/en/how-we-hire/interview-prep/software-development-topics) 明确列出 coding、system design、数据结构、算法、数据库、分布式计算、操作系统、网络和 ML/AI；官方说明也强调评估应用能力，不是死记细节。
- [Microsoft Technical interviews](https://careers.microsoft.com/v2/global/en/hiring-tips/technical-interviewing.html) 强调技术原则、问题求解、技术敏捷性和战略思考。候选人应主动澄清问题、声明假设并解释选择。
- [Anthropic Careers](https://www.anthropic.com/careers) 说明编程面试要实际写、运行和调试方案，并关注候选人的思考过程与方案取舍；独立研究、技术文章和开源贡献可以作为能力证据。

因此本课程把岗位验收拆成四轮：

```text
Coding / Debugging
-> Agent 与 RAG 深挖
-> 端到端 System Design
-> 项目证据与行为追问
```

具体公司、团队和职级会调整轮次。拿到面试邀请后仍要向 recruiter 确认范围。

## 4. 四类岗位画像

### Agent 应用工程师

目标：把模型、工具、知识和业务流程交付成可用产品。

主修：Agent workflow、RAG、Eval、产品指标、上线与跨团队交付。

合格证据：OpsPilot 正常、受阻、恢复三条路径；有离线指标、在线假设、回滚和事故复盘。

### Agent Systems 工程师

目标：构建 execution loop、隔离、状态、评测、性能和可靠性底座。

主修：分布式系统、runtime/harness、sandbox、恢复、profiling、成本与容量。

合格证据：中断恢复不重复副作用；能从 trace 区分模型、harness、检索、工具和基础设施问题。

### RAG / AI Search 工程师

目标：让 Agent 在大规模、动态、受权限控制的数据上找到可验证证据。

主修：IR、数据管道、hybrid/rerank、引用、ACL、freshness、评测和低延迟。

合格证据：分别报告 retrieval、answer、citation、ACL、freshness、P95 和成本。

### 智能体算法工程师

目标：研究并优化 planning、reasoning、tool learning、memory、retrieval 与后训练，使真实任务产生可测增益。

主修：Transformer/LLM、SFT/DPO/RL、Agentic RL、数据构造、baseline、消融和失败切片，同时保持可运行实现。

合格证据：同任务、同预算比较 prompt/RAG/harness/训练方案；说明 reward hacking、泛化失败和如何接入线上门禁。

## 5. 必须记住的八域知识

不要只背定义。每个知识点都按这六句回答：

```text
定义：它解决什么问题，边界是什么？
机制：输入、状态、决策、输出如何流动？
取舍：为什么选它，替代方案何时更好？
失败：最危险的事故是什么，在哪里检测和恢复？
指标：质量、延迟、成本、安全如何验收？
证据：我的代码、测试、trace、eval 或 ADR 在哪里？
```

| 能力域 | 必记知识 | 面试最危险的误区 | 课程证据 |
|---|---|---|---|
| 编码与 CS | 数据结构、复杂度、async、HTTP、SQL 事务、缓存、队列、网络、OS、测试 | 用框架掩盖基础；写超时后无条件重试 | F0 API/SQL/pytest/幂等实验 |
| LLM 与 Context | token、sampling、structured output、tool use、context budget、prompt version、ablation | 低温度等于确定性；prompt 等于权限 | S0 bad cases、S5 context ablation |
| Runtime 与工具 | Run/Step/Event、状态机、预算、policy、approval、MCP、handoff | while true 隐藏状态；模型能决定权限 | S1-S2 状态与 allow/deny/approval 测试 |
| RAG 与 IR | source contract、parse/chunk、ACL、hybrid、rerank、routing、citation、freshness | 只调 top_k；过滤放在召回后 | S3 分层 eval、ACL blocker、版本化 index |
| 可靠性 | checkpoint、retry taxonomy、idempotency、ledger、outbox、reconcile、SLO | 把重试当恢复；不知道副作用是否提交 | S4 crash/replay、S7 SLO 与故障注入 |
| Eval 与观测 | golden、trajectory、tool/RAG/security eval、judge calibration、trace/metric/audit | 平均分稀释关键失败；一个 judge 包办全部 | S6 release gate、S7 trace 到 regression |
| 安全与隐私 | injection、tenant isolation、least privilege、secret、sandbox、egress、supply chain | 关键词过滤代替强控制；Docker 等于绝对隔离 | S8 adversarial suite 与阻断 audit |
| 设计与交付 | 澄清、容量、API/数据模型、trade-off、canary、rollback、ADR、STAR(R) | 从组件名开始；无数量级和替代方案 | S10 release packet、答辩与复盘 |

## 6. 面试难题：OpsPilot 全球多租户 Agent

### 题目

为全球企业客户支持团队设计 OpsPilot。它要检索政策与工单、给出带引用的退款建议，并在满足权限和审批后执行退款。请给出从入口到发布的架构、关键数据契约、容量估算、失败恢复、评测与安全方案。

### 约束

- 20,000 个企业租户，任何跨租户泄漏都阻塞发布。
- 1,000 万份版本化文档，更新后 5 分钟内可检索。
- 峰值 2,000 QPS，端到端 P95 小于 2.5 秒。
- 退款必须审批、幂等、可对账，恢复不能重复执行。
- 重要结论必须有 claim-level citation，证据不足时拒答或转人工。
- 模型、检索、工具和网络会超时；长任务必须可取消和恢复。
- 上线前给出 token、检索、存储和重排预算及降级策略。

### 推荐 60 分钟节奏

| 时间 | 任务 | 必须说清 |
|---:|---|---|
| 0-6 分钟 | 澄清与数量级 | 读写流量、更新率、审批 SLA、SLO、拒答条件 |
| 6-14 分钟 | 责任边界 | Gateway、Runtime、Policy、RAG、Tool、Storage、Trace/Audit |
| 14-24 分钟 | RAG 与引用 | source/version、ACL-first、增量索引、hybrid/rerank、citation/eval |
| 24-34 分钟 | 工具与恢复 | immutable ToolCall、approval、operation id、ledger/outbox、reconcile |
| 34-43 分钟 | Eval 与观测 | 分层数据、critical gate、judge 校准、run_id、线上回流 |
| 43-50 分钟 | 安全 | injection、cache isolation、短期凭据、sandbox/egress、MCP 准入 |
| 50-60 分钟 | 性能与发布 | profile、路由、预算、消融、canary、降级、rollback |

### 连续追问

1. 某文档更新后 20 分钟仍检索到旧版本，怎样定位并止损？
2. retrieval recall 提升，但 citation correctness 下降，先做什么实验？
3. 退款供应商成功后连接断开，恢复时怎样避免第二次退款？
4. 平均分 95，但一个跨租户 case 失败，能否给 1% 用户灰度？
5. 恶意政策文档要求调用导出工具，为什么关键词过滤不够？
6. P95 从 2.2 秒升到 4 秒，如何区分模型、检索、队列和工具问题？
7. 为什么现在不拆成 planner、researcher、executor、reviewer 四个 Agent？

回答追问仍用“定义、机制、取舍、失败、指标、证据”六句结构。

## 6A. 国内企业 Agent 面试难题

设计一个支持公有 API 与私有模型切换、可私有化部署的集团办事 Agent：300 家子公司、20 万员工、500 万份制度/FAQ/表格/扫描件、峰值 800 QPS。身份、数据域和审批链不能由模型推断；知识更新 10 分钟内可检索；工单与写操作要授权、审批、幂等、可取消、可对账；GPU 和外部 API 都有硬预算。

60 分钟按七段完成：场景与边界、模型与部署、企业 RAG、Harness 与工具、评测与迁移、安全治理、容量与发布。重点追问：

1. OpenAI-compatible 接口为什么不等于行为兼容？怎样做模型切换回归与回滚？
2. 扫描件解析、ACL、十分钟 freshness、claim citation 如何分别评测？
3. context compaction、工具结果卸载、长期记忆和 checkpoint 怎样避免互相覆盖？
4. 外部写操作结果未知时，operation id、ledger 与 reconcile 怎样配合？
5. GPU 紧张时怎样按任务价值做 admission control，而不是所有请求一起降级？
6. MCP/skill、恶意文档、敏感字段和 trace 分别由哪一层控制？

该题仍是 A 类国内岗位重复信号的课程合成题，不是任何公司的原题。评分同样要求 80/100，并把跨组织泄漏、迁移无 blocker、未知结果直接重试、敏感信息出域列为硬失败。

## 7. 100 分评分尺

| 维度 | 分值 | 满分锚点 |
|---|---:|---|
| 需求、容量与 SLO | 10 | 有数量级、关键假设、用户目标和禁止条件 |
| 架构与契约 | 15 | 责任层、可信事实、状态和接口归属清楚 |
| RAG 与引用 | 15 | 数据、权限、检索、引用、时效、评测和回滚完整 |
| Runtime、工具与恢复 | 15 | 审批、幂等、checkpoint、ledger 和不确定结果完整 |
| Eval 与可观测 | 15 | 分层评测、critical gate、归因、trace 和回归闭环 |
| 安全与隐私 | 10 | 注入、跨租户、凭据、沙箱、egress、供应链有强控制 |
| 性能、成本与发布 | 10 | profile、预算、消融、canary、降级和 rollback |
| 表达与项目证据 | 10 | 结构清楚，主动取舍，并打开自己的代码、指标和事故 |

80 分才算本地自评通过，而且以下任一项出现直接失败：

- 模型或文档内容能决定租户、角色或退款权限。
- 跨租户检索或缓存泄漏没有确定性阻断。
- 工具结果未知时直接重试高风险写操作。
- critical security case 失败仍允许发布。

## 8. 常见易错点与修复

| 易错点 | 为什么失分 | 修复动作 |
|---|---|---|
| 从 LangGraph、向量库或模型名开始 | 没有先定义问题和约束 | 先问流量、数据、风险、SLO、拒答条件 |
| 只讲 happy path | Agent 面试重点是长任务、权限和不确定失败 | 每层主动讲一个事故、检测点、恢复和回归 |
| 只说“加缓存/重试/多 Agent” | 缺少一致性、成本和回滚条件 | 明确 key、TTL、幂等、预算、对照实验和撤销条件 |
| 只报整体正确率 | 无法发现 ACL、引用、工具等关键失败 | 按 failure slice 分层，critical case 独立阻塞 |
| 背框架 API | 上游版本变化后知识迅速失效 | 用契约、状态、权限、证据解释不可替代原理 |
| 项目讲成技术清单 | 面试官无法判断你真的解决过问题 | 用事故、取舍、量化结果、约束和可打开证据组织 |

## 8A. GitHub 上游项目深挖

项目学习不是读 README 后复述功能。每个仓库都要回答四件事：责任边界在哪里、最危险失败是什么、现有测试没证明什么、你能提交的最小改进是什么。

| B 类上游项目 | 先读什么 | 可用于哪类追问 |
|---|---|---|
| [AgentScope](https://github.com/agentscope-ai/agentscope) | `src/agentscope`、memory、agent service、tests | context compaction、tool/MCP/skill、permission/HITL、workspace/sandbox 与 agent team |
| [RAGFlow](https://github.com/infiniflow/ragflow) | `deepdoc`、`rag`、`agent`、`memory`、`mcp` | 解析、chunk、retrieval、rerank、citation 和索引迁移怎样分层验收 |
| [DB-GPT](https://github.com/eosphoros-ai/DB-GPT) | core、RAG、AWEL、serve、tests | AI+Data、SQL/代码工具、workflow 与私有化部署的权限和执行边界 |
| [agentUniverse](https://github.com/agentuniverse-ai/agentUniverse) | agent、memory、RAG、planner、observability | PEER/DOE、多 Agent 决策、memory 与 trace 责任分工 |
| [Qwen-Agent](https://github.com/QwenLM/Qwen-Agent) | agent、tools、memory、examples、tests | tool calling、MCP、RAG、code interpreter；基础 Docker 隔离为什么仍需威胁模型 |
| [MaxKB](https://github.com/1Panel-dev/MaxKB) | apps、workflow、knowledge、model_provider、tests | 企业 RAG、workflow、MCP、私有模型和产品化运维如何形成可复验项目 |

仓库活跃或 release 新，只说明值得继续审计，不说明默认安全、适合你的语料或生产最优。最终采用必须回到固定版本、自己的 eval、trace、成本和对抗结果。

## 8B. Linux DO 与中文社区证据

C 类样本的用途是生成训练活动，不是宣布“高频真题”。本轮保留以下可读原帖：

- [Linux DO：面试了十几家 Agent 岗位，整理了面试题](https://linux.do/t/topic/2365650)，2026-06-10。用于练容量、token 成本、多 Agent 取舍、Docker/K8s 和业务收益；作者匿名且录音经 AI 整理。
- [Linux DO：4-5 月 Agent 社招面经手记](https://linux.do/t/topic/2416951)，2026-06-16。用于练记忆冲突、shared state、context 压缩、eval、sandbox 与成本；不能外推公司题库。
- [Linux DO：大模型应用开发面试中的 RAG 场景题](https://linux.do/t/topic/648771)，2025-05-14。用于做指代消解、元数据过滤、query rewrite 延迟与检索策略的 failure drill；社区答案互有冲突。
- [牛客：百度 AI 应用工程师社招一面复盘](https://www.nowcoder.com/feed/main/detail/26578b46ce064ac6a5f67d41adb07eb7)，2026-07-17。用于准备权限、上下文压缩、动态 Tool 注册和完整 RAG 链路的项目追问；单人失败面经不代表百度统一标准。

使用规则：把每条线索改写成“可运行实验 + 评分标准 + 失败边界”；不要把公司名、题目频率、轮次或标准答案从匿名帖子推断出来。

## 9. 五道自测

1. 退款工具超时但可能已经成功，恢复的第一动作是什么？
   答案：用相同 operation id 查询或对账既有结果；无法确认则转人工或补偿，不能直接重试。
2. retrieval recall 提升但引用错误率上升，下一步做什么？
   答案：固定语料与问题，单独检查 rerank、context assembly 和 citation validator，定位证据第一次失真。
3. 总平均分 95，但一个跨租户 case 失败，能否发布？
   答案：不能。跨租户泄漏是 deterministic critical blocker。
4. 为什么不默认使用多 Agent？
   答案：先测单 Agent baseline；只有专业化、上下文隔离或独立验证带来同预算可测增益才拆。
5. 什么项目回答最接近岗位级证据？
   答案：说明事故、方案取舍、量化结果和剩余边界，并现场打开对应代码、测试、trace、eval 或复盘。

答错后不要背答案。回到对应阶段复现一次失败，再把失败写入 regression set。

## 10. 面试学习路径

```text
岗位诊断
-> F0 编码与 CS 基础
-> S0-S3 契约、Runtime、Tool/Policy、RAG
-> S4-S5 恢复、Memory 与 Context
-> S6-S8 Eval、Observability、Security
-> S9-S10 架构取舍、发布与作品集
-> I1 高难题、连续追问、四轮完整模拟
```

标准准备周期为 2-4 周。课程没有通过证据时，不要靠一周背题掩盖工程缺口。

## 11. 一页速记清单

- 先澄清用户目标、数量级、SLO、禁止条件和非目标。
- 可信身份、租户、风险与凭据不来自模型。
- 聊天历史不是 Run/Step/Event，也不是 checkpoint。
- 高风险工具必须 policy、approval、idempotency、ledger、reconcile。
- RAG 按 source、parse、chunk、index、retrieve、rerank、answer、citation、operate 分层。
- ACL 在检索前；claim-level citation 必须支持具体结论。
- 测试硬边界，eval 质量分布，trace 定位一次请求，audit 证明责任事实。
- 平均分不能稀释 critical failure；judge 不能覆盖确定性断言。
- 先单 Agent baseline，后用同预算实验决定是否多 Agent。
- 发布锁定 code、prompt、model、tool、policy、index、dataset 和配置。
- 每个方案都讲替代、成本、失败、指标、回滚和自己的证据。

## 12. 面试前预习核对清单

- [ ] 我能在 45 分钟内写、跑、调通一段有边界测试的代码。
- [ ] 我能闭卷画出 OpsPilot 请求、状态、工具、检索、证据和审计链路。
- [ ] 我能讲清一次重复副作用、一次跨租户风险、一次检索退化和一次发布回滚。
- [ ] 我准备了三项量化结果，并能说明 baseline、数据集和测量误差。
- [ ] 我能打开代码、测试、trace、eval、ADR 和复盘，而不是只展示截图。
- [ ] 我能说明未实现和未验证的生产条件。
- [ ] 我已完成一次 60 分钟难题，评分至少 80 且没有硬边界失败。
- [ ] 我已按目标公司的 recruiter 信息校准具体轮次，而不是假设所有公司相同。

## 13. 资料维护门禁

1. 国内当前岗位每 14 天抽样核验，国际岗位最长 30 天；记录公司、岗位、地区、访问日期、能力信号和可访问状态。
2. 职位关闭后标记 historical，不删除曾影响课程的决策记录。
3. 单个 JD 不能改变主线；至少两个独立公司的重复信号才能升级为核心能力。
4. A / B / C 分层展示：官方岗位说明职责，GitHub 说明实现，社区经验只生成训练假设；面经、论坛和题库不能标成官方原题。
5. 任何新增知识点必须映射到课程阶段、可运行证据和一道故障追问。
