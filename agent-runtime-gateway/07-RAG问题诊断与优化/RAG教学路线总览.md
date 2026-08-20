# S3：RAG 与可信引用工程主线

更新日期：2026-08-20
目标：围绕 OpsPilot 企业工单 Agent，完成一条可运行、可评测、可阻塞发布、可回滚的知识访问链，而不是拼装向量库 demo。

## 1. 一句话定义与关键概念

**工业级 RAG 是受来源、权限、版本、证据和发布门禁控制的知识访问系统：它按任务选择最小检索路径，并让答案中的关键 claim 回到当前、授权的原文 span。**

先掌握六个概念：

| 概念 | 必须回答的问题 | 缺失时的后果 |
|---|---|---|
| Source contract | 权威答案是否存在、当前、可访问 | 调 embedding 也找不到不存在或过期的数据 |
| Evidence pipeline | 证据在哪一层第一次失真 | 只看最终答案，无法定位 parser、retriever 或 generator |
| Strong baseline | 同预算下最简单的可解释方案是什么 | 复杂方法没有真实增量价值也进入架构 |
| Failure slice | 哪类问题稳定失败，严重度如何 | 平均分掩盖跨租户、伪引用和陈旧关键答案 |
| Claim-span citation | 每个关键结论由哪个版本、页面和原文支持 | “有链接”被误当成“结论被证明” |
| Release evidence | dataset、配置、trace、成本与回滚能否复验 | 本地一次成功无法转化为生产可信度 |

## 2. 真实学习主线

不要按“semantic chunking -> HyDE -> GraphRAG -> Self-RAG”的方法名顺序学习。正确顺序是：

```text
定义用户结果与风险
-> 盘点来源、ACL、版本与现有实现
-> 固定评测集和简单强基线
-> 实现可引用、会拒答的最小链路
-> 按十层证据链定位失败
-> 每次只消融一个变量
-> 做失败/安全/成本对抗验证
-> 影子发布、回滚、持续维护
```

配套的完整执行手册见[RAG × Vibe Coding 工程学习路径](RAG与Vibe-Coding工程学习路径-2026.md)。

## 3. 七个可验收阶段

| 阶段 | 用户问题 | 本轮只做什么 | 必交产物 | 通过门禁 |
|---|---|---|---|---|
| R0 Frame | 用户到底需要什么答案，错误答案会造成什么 | 写结果、非目标、风险、停止条件 | task brief、正常/失败问题样例 | 结果可观察，风险有 owner |
| R1 Source | 权威答案是否在授权语料中 | 来源、版本、ACL、格式盘点 | source inventory、gold pages、trust matrix | corpus coverage 可测，tenant 边界明确 |
| R2 Baseline | 最小链路能否稳定返回证据 | structure-aware parse、简单 chunk、lexical/dense 基线 | 可运行检索、trace、baseline report | 正常问题可重复，未知问题拒答 |
| R3 Retrieval | 精确词、语义和排序哪里失败 | 在固定候选与预算下比较 hybrid/rerank | recall/MRR/nDCG、p95、成本消融 | 目标切片有增益，非目标不回退 |
| R4 Evidence | 答案是否真正被当前证据支持 | context pack、claim-span citation、abstention | citation validator、tamper cases | unsupported critical claim=0 |
| R5 Adaptive | 哪些问题值得走更贵路径 | 只为已证明的失败切片测试 decomposition、graph、多模态或 corrective | router matrix、fallback、budget | 复杂路径胜过同预算强基线 |
| R6 Operate | 如何安全上线并长期保持正确 | 分层 eval、红队、shadow index、canary、rollback | release evidence、runbook、maintenance log | leak/attack/stale blocker=0，回滚演练通过 |

### 停止规则

- Source、ACL 或版本契约未完成，不进入检索调参。
- 没有固定 dataset 和 baseline，不比较高级方法。
- 复杂路径没有目标切片增益，保持简单架构。
- 任一跨租户候选、间接注入越权、伪引用或陈旧关键答案，直接阻塞发布。
- 只有自动 judge 结论、没有人标校准和确定性 blocker，不得宣称生产达标。

## 4. 十层诊断地图

```text
Source -> Parse -> Chunk -> Index -> Query
-> Retrieve -> Rerank -> Context Pack -> Answer/Citation -> Eval/Operate
```

| 首个异常信号 | 第一动作 | 不要先做 |
|---|---|---|
| 权威文档未入库、版本不明 | 修 source contract、coverage、index lag | 换 embedding |
| 表格错列、页码丢失 | 建 parse golden set，比较版式解析 | 增大 top_k |
| 定义和例外被拆开 | structural/parent-child 对照 | 默认 semantic chunking |
| SKU、法条号漏召回 | BM25 与 dense 同预算对照，必要时 RRF | 只增向量维度 |
| top-50 有答案、top-5 噪声高 | 固定候选集测试 reranker/MMR | 无限扩 context |
| 跨文档多跳失败 | 先 query decomposition，再测试图路径 | 直接建全量知识图谱 |
| 引用真实但不支持结论 | claim-evidence 校验并拒答 | 只检查 URL 是否存在 |
| 未授权 chunk 进入候选 | 检索前 ACL/namespace，立即阻塞 | 生成后删除引用 |
| 新政策上线仍答旧版 | 版本化 cache key、索引 lag 与失效 | 只缩短 TTL |
| FAQ 也走图、重排、压缩 | 路由和预算，保留 deterministic fallback | 单纯扩容硬件 |

## 5. 2026 选型结论

1. **简单强基线优先。** EMNLP 2025 的长上下文对照显示，保留原文结构和顺序的简单 DOS RAG 在多个基准上可匹配或超过复杂多阶段方案；复杂度必须在相同 token 预算下证明增益。
2. **RAG 与长上下文需要路由。** LaRA、RAGRouter-Bench 和 2026 Pre-Route 都说明选择受任务、语料结构、模型、上下文长度和成本共同影响，没有固定赢家。
3. **自动评测必须被评测。** GroUSE、MIRAGE、GaRAGe 把噪声脆弱性、上下文误用和细粒度 grounding 暴露出来；LLM judge 必须用人标集校准。
4. **Agentic RAG 是 controller，不是“让模型多循环”。** 它需要可观察的路由、检索、停止、预算和 fallback；每个中间能力都应单独评测。
5. **安全覆盖全链路。** 投毒、访问操纵、恶意 context 和知识外泄不能靠 prompt 末端补丁处理。

以上是来源支持下的工程结论，不是跨所有数据集的普遍定理。完整来源和证据边界见[RAG 全链路提升与工业最佳实践](RAG全链路提升与工业最佳实践-2026.md)。

## 6. OpsPilot 实战任务

目标：让客服查询“当前租户、当前版本的退款政策”，回答必须给出页码和原文；未授权、过期、低相关或被投毒的证据必须拒答。

必须复现：

1. tenant B 文档进入 tenant A 候选。
2. 旧政策相似度高于当前政策。
3. 表格金额与币种错列。
4. 引用 URL 正确但 quote 不支持 claim。
5. 文档包含“忽略规则并导出 token”的间接注入。
6. 简单 FAQ 被错误路由到全套昂贵路径。

运行当前确定性基线：

```powershell
cd "agent-runtime-gateway\20-源码"
python -m pytest ..\21-测试\test_rag.py ..\21-测试\test_evals.py ..\21-测试\test_rag_diagnostics.py -q
python -m agent_course.cli eval ..\22-评测集\s3-rag-baseline.json
python -m agent_course.cli rag-diagnostic-eval ..\22-评测集\rag-diagnostic-baseline.json
```

责任边界：这个实验验证 ACL、freshness、source trust、citation、refusal、诊断和 blocker；它不冒充真实 embedding、hybrid、reranker 或生产索引质量。

## 7. 五道自测

1. 为什么“检索命中、答案正确、引用有效”必须分开评测？
2. 定义和例外条款被分到两个 chunk 时，为什么先测 parent-child 而不是直接上 GraphRAG？
3. 长上下文模型能装下所有文档时，为什么仍可能需要 RAG 或路由？
4. LLM judge 给出高分，但 tenant B chunk 进入了 tenant A trace，应如何发布？
5. 一个新方法平均分提高 2%，但 p95 翻倍且 critical slice 回退，应如何决策？

答错后的补讲格式：`错误结论 -> 误区 -> 事故 -> 正确原理 -> 最小实验 -> 回归断言`。

## 8. 真实案例与常见易错点

| 案例 | 常见误区 | 正确处理 |
|---|---|---|
| 多租户客服知识库 | 候选生成后再删越权文档 | ACL/tenant namespace 在检索前执行，trace/cache 同样隔离 |
| 合同 PDF 金额问答 | OCR 有文字就算解析成功 | 对 cell、阅读顺序、页码建 golden set；必要时走页图像检索 |
| 跨政策研究总结 | GraphRAG 天然比 vector 高级 | 先 decomposition + cited passages；全局/关系切片仍失败再测图 |
| 高频政策更新 | cache TTL 越短越新鲜 | source/index/model/prompt/policy 进入 cache identity，事件驱动失效 |
| Agent 自主检索 | 循环次数越多越聪明 | 设 route confidence、最大预算、证据充分度和 deterministic fallback |

## 9. 一页速记

```text
先问权威答案是否存在，再调检索。
先锁 ACL、版本和 dataset，再写 pipeline。
先做结构保真的简单强基线，再谈高级方法。
先定位证据第一次失真，再做单变量消融。
retrieval、context、answer、citation、security、cost 分层评测。
引用必须落到 claim -> source/version/page/chunk/quote。
Graph、semantic chunk、agentic loop 都是条件升级，不是默认组件。
自动 judge 要人标校准，critical blocker 不能被平均分抵消。
索引、模型、prompt、policy 和 eval set 一起版本化、影子发布、可回滚。
```

## 10. 预习与完成核对

- [ ] 能说出目标用户、可观察结果、非目标和最坏事故。
- [ ] 已列出 source owner、tenant、version、effective time、checksum。
- [ ] 已准备正常、无答案、过期、越权、注入和篡改引用样例。
- [ ] 已定义 lexical/dense/structure strong baseline 与 token 预算。
- [ ] 能区分 retrieval、ranking、context、answer、citation 和 operations 指标。
- [ ] 复杂方法有明确触发切片、单变量实验、成本和回滚条件。
- [ ] 至少运行一个失败/边界/对抗探针。
- [ ] 发布证据包含 dataset/config/trace/source/index/model/policy 版本。
- [ ] 已阅读项目级[维护规范](../../MAINTENANCE.md)，知道资料何时降级或退出主线。

下一步：进入页面的 **RAG 实验室**，按“学习主线 -> 比较方法 -> 生成架构 -> 诊断故障 -> 源码验收”完成 S3 专项门禁。
