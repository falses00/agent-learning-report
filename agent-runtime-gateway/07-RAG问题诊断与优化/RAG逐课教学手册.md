# RAG 逐课教学手册

生成日期：2026-06-30  
用途：把 RAG 专项路线拆成可以一课一课跟着问、跟着判断、跟着验收的教学流程。

## 0. 学习原则

这套课程不要求你记住实现代码。你真正要掌握的是：

- 能把一个 RAG 问题拆成数据、检索、重排、上下文、生成、引用、评测、安全和治理层。
- 能向 Agent 下达清楚的设计任务，而不是只说“帮我优化 RAG”。
- 能判断一个优化是否真的有效，而不是被热门项目、论文名或 star 数带着走。
- 能把失败样例沉淀成评测集，保证以后模型、prompt、索引和参数变化时不会倒退。

每一课都按这个循环推进：

```text
失败复现
-> 设计假设
-> 选择最小实验
-> 明确指标
-> 做上线判断
-> 写入回归集
-> 复述设计理由
```

你的输出不是代码，而是设计说明、实验表、评测用例、验收门禁和复盘结论。

## 1. 提问模板

每一课开始时，你可以这样问：

```text
继续 RAG-XX：课程名称。

我不写代码，请你先调用 planner 或 researcher 增强提示词；
然后用架构师视角教我：
1. 这一课解决什么失败；
2. 失败在 RAG 链路哪一层；
3. 最小实验怎么设计；
4. 指标怎么选；
5. 需要沉淀哪些评测集；
6. 什么情况下可以上线；
7. 我应该怎样复述这一课。
```

如果涉及最新项目、论文、库或 GitHub 方案，还要加一句：

```text
请先用 researcher 搜集最新资料，并把大项目和小而尖项目分开评价。
```

## 2. 课程拆解

| 课时 | 主题 | 先复现的失败 | 最小实验 | 核心指标 | 你要能说清 |
|---|---|---|---|---|---|
| RAG-00 | 失败模式导入 | 答案有幻觉、引用不支持、越权召回、旧信息覆盖新信息 | 用 10 个问题标出失败层 | failure reproducibility | RAG 不是向量库，而是可评测链路 |
| RAG-01 | Baseline | 知识库问答能跑但不稳定 | 固定文档、固定问题、固定引用标准 | answer accuracy、citation support | baseline 是以后所有优化的尺子 |
| RAG-02 | Parsing/Chunking | 表格丢列、章节断裂、长文上下文缺失 | 对比 fixed、semantic、late chunking | context recall、chunk hit rate | chunking 改的是证据单元，不是模型智商 |
| RAG-03 | Query Rewrite | 短问题、多轮省略、同义词找不到 | 对比原查询、HyDE、multi-query、decomposition | hit@k、MRR | rewrite 只在召回失败时有价值 |
| RAG-04 | Hybrid/Rerank | 召回多但噪声大，或关键词问题召回差 | BM25、vector、hybrid、rerank 消融 | context precision、nDCG | hybrid 解决覆盖，rerank 解决排序 |
| RAG-05 | Graph/Hierarchy | 多跳问题、跨文档主题、全局总结失败 | 图谱/层级索引与普通索引对比 | multi-hop F1、path validity | 图不是装饰，是为多跳关系服务 |
| RAG-06 | Corrective RAG | 检索失败后模型硬答 | 加入自检、补检、拒答、人工确认 | unsupported answer rate、recovery success | 正确拒答比错误自信更重要 |
| RAG-07 | Memory + RAG | 会话记忆污染知识库，或长期记忆越权 | 区分 knowledge、session、long-term memory | memory precision、leakage rate | 记忆不是知识库，写入必须有门禁 |
| RAG-08 | Eval/Observability | 优化后不知道好没好 | 建评测集、trace、回归报告 | regression pass rate、trace coverage | 没有评测就没有优化 |
| RAG-09 | Security/Multi-Tenant | prompt injection、数据投毒、跨租户召回 | 注入样例、ACL 样例、投毒样例 | attack success rate、access violation | 安全失败必须阻塞上线 |
| RAG-10 | Cost/Latency | 重排太慢、检索太贵、缓存误命中 | top_k、rerank_top_n、cache 策略消融 | cost/query、p95 latency | 成本优化不能牺牲安全和引用 |
| RAG-11 | Industrial Integration | RAG demo 无法接入长线 Agent | 接入 Gateway、Policy、Trace、Eval、Release | audit coverage、release gate pass | 工业级 RAG 必须可追踪、可回滚、可治理 |

## 3. 每课的交付物

每一课结束时至少有四个产物：

| 产物 | 说明 | 不写代码时怎么完成 |
|---|---|---|
| 失败卡片 | 一个可复述的失败场景 | 用自然语言写清问题、期望、实际错误和影响 |
| 实验设计表 | baseline、变量、指标和判定阈值 | 让 Agent 帮你生成表格，你负责追问和判断 |
| 评测样例 | 能进入 regression set 的 JSONL 或表格 | 先用中文表格确认，再转成 JSONL |
| 设计复述 | 为什么选这个方案，为什么不选更复杂方案 | 用“问题 -> 证据 -> 决策 -> 风险”复述 |

## 4. 课堂互动方式

你不需要说“请写代码”。你应该说：

```text
请把这个 RAG 问题按链路分层诊断，并给我一个最小可验证实验。
```

```text
请把这个优化方案改成上线门禁：哪些指标必须过，哪些失败必须阻塞。
```

```text
请模拟 reviewer 质疑这个方案，指出它可能只是在 benchmark 上好看但生产不可用的原因。
```

```text
请把这次失败沉淀成一条评测样例，并说明它属于召回、重排、引用、安全还是治理问题。
```

## 5. 是否掌握的判断

如果你能不看代码回答下面问题，就说明这一课真正学会了：

- 失败发生在哪一层？
- 最小优化是什么？
- 哪个指标能证明它有效？
- 它可能引入什么新风险？
- 哪些样例要进入回归集？
- 什么情况下必须拒绝上线？

反过来，如果你只能说出“用了某某框架”，但说不清失败、指标和门禁，这一课就还没有过关。
