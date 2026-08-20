# RAG × Vibe Coding 工程学习路径（2026）

更新日期：2026-08-20
适用对象：已经能读 Python/TypeScript、会运行测试，希望从 RAG demo 进阶到可上线 Agent 知识系统的学习者。

## 1. 一句话定义与关键概念

**RAG × Vibe Coding 是一种证据驱动的协作开发法：人定义用户结果、风险和发布责任，Coding Agent 读取现场、实现小批变更并运行工具，自动化门禁用真实数据证明 RAG 每一层是否更好。**

关键不是“用自然语言写 RAG”，而是把生成速度约束在七个工程环节中：

| 环节 | 人负责 | Agent 负责 | 机器证据 |
|---|---|---|---|
| Frame | 用户结果、非目标、风险、停止条件 | 发现歧义并整理任务契约 | 可观察验收表 |
| Survey | 指定可信范围和 owner | 读仓库、语料 schema、测试、git 状态与当前文档 | 已确认事实、假设、未知项 |
| Plan | 决定优先级和责任边界 | 拆成 3–7 个可验证步骤 | 每步的输入、输出、停止条件 |
| Contract | 接受质量/安全/成本门禁 | 生成正常、失败、边界和对抗样例候选 | 版本化 eval set 与 blocker |
| Implement | 处理业务规则和高风险批准 | 按仓库模式完成最小实现 | 小 diff、trace、可运行结果 |
| Verify | 认可剩余风险 | 运行目标测试、对抗探针、浏览器或负载检查 | expected vs actual、回归结果 |
| Review | 架构、安全和发布责任 | 审查 diff、依赖、secret、迁移与回滚 | 独立 reviewer、release evidence |

## 2. 为什么 RAG 特别需要这条闭环

RAG 的结果由语料、解析、切块、索引、查询、召回、排序、上下文和生成共同决定。Coding Agent 很容易快速生成一个“能回答”的 demo，但以下错误不会因为代码写得快而消失：

- 权威文档根本没入库，Agent 却不断更换 embedding。
- tenant ACL 放在生成后，越权内容已进入 reranker、模型、trace 和 cache。
- 解析把表格列打乱，检索只能稳定返回错误证据。
- 引用链接真实，但 quote 不支持关键 claim。
- semantic chunking、GraphRAG 或 agent loop 同时加入，收益无法归因。
- Agent 修改测试或放宽阈值，制造“优化成功”。
- 上游 API 已迁移，模型仍从训练记忆生成旧写法。

Vibe Coding 在这里不是放松工程纪律，而是把调查、实验和验证反馈变成更短、更快的闭环。

## 3. 贯穿项目：OpsPilot 可信政策助手

用户故事：客服询问“当前客户是否满足退款例外”。系统只能使用当前租户、当前生效版本的政策和合同证据；每个关键结论返回页码与原文；证据不足时拒答；任何间接注入都不能触发工具。

最终作品至少包含：

1. `RAGRequest`、`RAGResult`、`Citation`、`RAGEvalCase` 契约。
2. source/tenant/version/effective time/checksum 数据合同。
3. 结构感知解析和可回滚 chunk/index 版本。
4. lexical/dense/hybrid/rerank 的同预算消融。
5. ACL before retrieval、freshness、source trust 和 refusal。
6. claim-span citation validator 与篡改引用测试。
7. retrieval、answer、citation、安全、时效、延迟、成本分层评测。
8. shadow index、read alias、canary query、rollback 和维护记录。

## 4. 七阶段学习路径

### 阶段 1：Frame，定义可观察结果

先写：谁在什么场景遇到什么问题，正确与错误结果如何被观察，本轮不做什么，最坏事故是什么。

最小提示词：

```text
目标：让 tenant-a 客服查询当前退款政策，答案逐 claim 给出 source/version/page/quote。
非目标：不接生产数据库，不自动执行退款，不引入 GraphRAG。
失败行为：无授权证据、过期证据、低相关、间接注入一律拒答并写 audit。
停止：需要真实客户数据、生产凭据或改变退款规则时暂停。
```

常见问题：用“做一个先进 RAG”“提高准确率”代替用户结果。
解决：给出 3 个正常样例、3 个失败样例和一个明确非目标。

### 阶段 2：Survey，读取现场与资料

让 Agent 先读：

1. `AGENTS.md`、README、相邻实现、测试、数据 schema 和 `git status`。
2. 语料 owner、格式、版本、ACL、更新频率、删除要求。
3. 当前 parser、index、model、prompt、policy 和 eval set 版本。
4. 本地事实不足时，再查官方文档、原始论文和上游固定 commit。

常见问题：检索到博客或旧教程后直接生成代码。
解决：来源分为“当前采用、持续观察、历史基础、已退出主线”；易变 API 必须核验当前官方入口。

### 阶段 3：Plan + Contract，先锁评测与强基线

在实现前固定：

| 评测层 | 最小指标 | 必须阻塞的 case |
|---|---|---|
| Source/parse | corpus coverage、parse fidelity、table cell F1 | 权威答案不存在、表格错列 |
| Retrieval | recall@k、MRR、nDCG、path coverage | exact ID 丢失、gold evidence 未进入候选 |
| Context | precision/recall、redundancy、token budget | 例外条件被压缩掉 |
| Answer | correctness、faithfulness、abstention precision | 无证据硬答 |
| Citation | claim support、page/span validity | 引用真实但不支持 claim |
| Security | cross-tenant leak、attack success、poison hit@k | 任一未授权候选或工具越权 |
| Operations | p95、cost/query、index lag、wrong-cache hit | 关键答案陈旧、超预算且无降级 |

强基线至少包括：结构保真的解析、fixed/structural chunk、lexical 或 dense 单路、可验证引用、拒答和完整 trace。企业精确词与语义混合场景可把 BM25 + dense + RRF 作为候选强基线，但仍要与单路比较。

常见问题：Agent 同时改 parser、chunk、embedding 和 prompt。
解决：冻结 dataset、gold evidence、token 预算与其他组件，每次只替换一个变量。

### 阶段 4：Implement，按责任面小批实现

推荐批次：

```text
Batch 1: source/tenant/version contract + bad cases
Batch 2: parse golden set + page/cell anchors
Batch 3: structural chunk + stable parent/span ids
Batch 4: baseline retrieval + ACL pre-filter + trace
Batch 5: claim-span citation + refusal
Batch 6: layered eval + release blockers
```

每批要求 Agent 报告：改了什么、为什么、没有改什么、运行了哪些命令、哪条假设仍未证明。

常见问题：原型成立后直接部署生产。
解决：原型只证明方向；生产前重新定义数据模型、权限、失败路径、容量、迁移和维护责任。

### 阶段 5：Verify，按十层证据链诊断

验证顺序：

1. 复现失败并记录首个异常层。
2. 运行最便宜的 schema/unit 检查。
3. 运行目标 retrieval/citation 集成测试。
4. 运行至少一个失败、边界或对抗探针。
5. 比较同预算 baseline 与候选方法。
6. 检查 diff 中测试是否被删除、skip 或弱化。
7. 运行完整 quality gate。

复杂升级的触发条件：

| 候选 | 只有何时才测试 | 回退条件 |
|---|---|---|
| Parent-child | 小块命中但条件上下文不完整 | parent 带来噪声或 middle loss |
| Semantic/contextual chunk | 结构块在明确边界切片稳定失败 | 不胜简单块或生成上下文漂移 |
| Domain embedding | 内部术语/跨语种切片召回不足 | shadow index 无增益或回归 |
| ColBERT/reranker | 候选有 gold，但有限 context 排序差 | p95/索引成本超过收益 |
| GraphRAG/RAPTOR | decomposition 仍无法覆盖关系/全局问题 | edge/summary 不可信或建索引过贵 |
| Multimodal page retrieval | OCR 无法还原图表、箭头、版式关系 | 无区域定位或 visual judge 不可靠 |
| Agentic/corrective loop | 固定路径无法判断何时检索和修复 | route 错、循环、预算或无证据硬答 |

### 阶段 6：Review，对抗审查与责任分离

独立审查至少回答：

- 这个 diff 是否解决了正确的失败切片？
- 语料、tenant、版本和权限是否来自可信边界？
- 检索内容是否始终作为不可信数据？
- 是否引入停更、陌生、许可证冲突或拼写投毒依赖？
- 自动 judge 是否由人标集校准？
- critical blocker 能否被平均分错误抵消？
- rollback 是一句话，还是实际可执行的 alias/index/config 切换？

常见问题：同一 Agent 生成实现、生成测试、解释测试并批准上线。
解决：确定性断言、独立 reviewer 和发布 owner 形成职责分离；高风险动作必须人工批准。

### 阶段 7：Release + Learn，发布与维护

发布包应固定：

```text
dataset_version
source_snapshot / ACL policy
parser_version / chunk_version
index_version / embedding_version / reranker_version
model_version / prompt_version / controller_version
eval_report / trace_samples / cost_report
canary queries / rollback target / owner
```

事件驱动维护：来源更新、模型/embedding 变化、parser 变化、权限模型变化、安全公告、上游大版本迁移时，重跑目标切片和 critical suite。事故样例必须先进入回归集，再进入修复。

## 5. RAG 专用完整提示词

```text
目标：为【用户/场景】实现【可观察的 RAG 结果】。
非目标：【本轮明确不做的高级方法、生产动作或业务规则】。
风险：错误答案、越权、陈旧、投毒、伪引用、成本超限分别会造成什么；何时必须停止。

先调查：
- 读取 AGENTS/README、相邻实现、测试、eval set、数据 schema 和 git 状态。
- 盘点 source owner、tenant、version、effective time、trust、delete 和 index lag。
- 易变 API/项目只用当前官方文档或固定 commit；列出事实、假设和未知项。

先锁验收：
1. 正常：gold evidence 进入候选，关键 claim 有 source/version/page/chunk/quote。
2. 失败：无答案、低相关、过期时结构化拒答。
3. 边界：精确 ID、表格、长文、多轮省略、跨语种。
4. 安全：ACL before retrieval、间接注入、投毒、trace/cache 隔离。
5. 运营：p95、cost/query、index lag、rollback。

工作方式：
- 先建立最简单强基线，再按十层证据链定位首个异常。
- 每批只改变一个可归因变量；固定 dataset、gold evidence、token 预算和其他组件。
- 复杂方法必须在目标切片、同预算下胜过 baseline，并保留 deterministic fallback。
- 测试失败不得删除、skip、放宽断言或只调 judge prompt 制造绿色。

交付：列出 diff、命令与实际结果、失败/对抗证据、来源版本、残余风险和可执行回滚。
```

## 6. 工业最佳实践

1. ACL 和 tenant namespace 在候选生成前执行。
2. source、document、chunk 和 citation 共用稳定 ID、版本和 provenance。
3. parser 先过真实格式 golden set，再进入索引。
4. chunk 以结构和引用完整性为起点，大小/overlap 只是可调参数。
5. exact、semantic、relationship、visual 需求分通道，不迷信单一向量。
6. 同预算比较 recall、precision、latency 和 cost，不只比较答案平均分。
7. context pack 记录选入、丢弃、压缩原因，并保留原文 span。
8. 关键 claim 必须逐条验证；证据不足时拒答，不允许模型补事实。
9. 自动 judge 用人标校准；ACL、泄漏、工具副作用使用确定性断言。
10. cache key 包含 source/index/model/prompt/policy/tenant 版本。
11. embedding、chunk、graph 和 reranker 通过 shadow index + read alias 发布。
12. controller 有最大步数、token、延迟、成本、route confidence 和 fallback。
13. trace 避免保存未授权全文、secret 和不必要 PII。
14. 固定 commit 只证明机制存在，不证明你的生产适用性。
15. 资料、依赖和课程结论都进入复核日期与淘汰机制。

## 7. 五道自测

1. Coding Agent 建议直接上 GraphRAG，但当前没有 multi-hop failure set。你如何重写任务？
2. Agent 让 citation 测试通过的方法是只校验 URL。为什么错误，最小修复是什么？
3. semantic chunking 平均分略高，但表格切片和 p95 回退。应如何决定？
4. RAG judge 打 0.95 分，trace 却含 tenant-b chunk。哪条规则拥有最高优先级？
5. 模型升级后答案更流畅，但 source/index 不变。需要重跑哪些层，为什么？

答错后用：`误区 -> 可能事故 -> 正确原理 -> 最小实验 -> 新回归` 补讲。

## 8. 一页速记与预习核对

```text
Vibe 负责缩短反馈，不负责取消工程门禁。
人定义结果、风险和发布责任；Agent 调查、实现、验证；机器保存证据。
RAG 先 source/ACL/version，再 parse/chunk/retrieve，再 answer/citation。
先 strong baseline，后条件升级；一次一个变量；同预算比较。
自动 judge 不是安全控制，固定 commit 不是生产背书。
所有索引和资料都必须可版本化、可复验、可回滚、可维护。
```

- [ ] 能写出一个包含非目标、风险和停止条件的 RAG task brief。
- [ ] 能找到当前项目的 source schema、eval set、测试命令和未提交修改。
- [ ] 能列出至少 6 个 critical failure cases。
- [ ] 能定义 lexical/dense/structure baseline 和统一 token 预算。
- [ ] 能说明某个高级方法的触发切片、最小消融和回退条件。
- [ ] 已准备一个越权、一个陈旧、一个投毒、一个篡改引用探针。
- [ ] 知道哪些结论来自论文，哪些来自源码，哪些仍是工程推断。
- [ ] 知道如何固定版本、生成发布证据并切回上一索引。

## 9. 当前一手资料

- [Stronger Baselines for RAG with Long-Context LMs（EMNLP 2025）](https://aclanthology.org/2025.emnlp-main.1656/)
- [LaRA：RAG 与长上下文路由基准](https://arxiv.org/abs/2502.09977)
- [RAGRouter-Bench（2026）](https://arxiv.org/abs/2602.00296)
- [Route Before Retrieve（2026）](https://arxiv.org/abs/2605.10235)
- [MIRAGE（NAACL 2025）](https://aclanthology.org/2025.findings-naacl.157/)
- [GroUSE（COLING 2025）](https://aclanthology.org/2025.coling-main.304/)
- [GaRAGe（ACL Findings 2025）](https://aclanthology.org/2025.findings-acl.875/)
- [RAGEval（ACL 2025）](https://aclanthology.org/2025.acl-long.418/)
- [SoK: Agentic RAG（2026）](https://arxiv.org/abs/2603.07379)
- [RAGCap-Bench（2025）](https://arxiv.org/abs/2510.13910)
- [Securing RAG taxonomy（2026）](https://arxiv.org/abs/2604.08304)
- [Microsoft GraphRAG releases](https://github.com/microsoft/graphrag/releases)
- [OpenAI vector store files API](https://platform.openai.com/docs/api-reference/vector-stores-files)

资料状态、复核频率和退出标准见项目根目录[维护规范](../../MAINTENANCE.md)。
