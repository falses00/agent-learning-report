# RAG 跨层契约与版本治理

生成日期：2026-06-30  
用途：说明 RAG 如何穿过 Gateway、Tool、Policy、Memory、Eval、Observability 和 Release，而不是作为一个孤立向量库存在。

## 1. 基本原则

工业级 RAG 的核心不是“能搜到”，而是：

```text
每一次检索都可授权、可追踪、可复现、可评测、可回滚。
```

因此 RAG 不能绕过 Agent Runtime Gateway。所有检索必须作为受控工具进入：

```text
User Request
-> Agent Gateway
-> Runtime Step
-> Tool Gateway
-> Policy Decision
-> Retrieval Tool
-> Context Pack
-> Generation
-> Citation Check
-> Eval / Trace / Audit
```

## 2. 跨层责任

| 层级 | 对 RAG 的责任 | 不允许发生 |
|---|---|---|
| Agent Gateway | 绑定 request_id、tenant、principal、trace | 匿名检索企业知识库 |
| Runtime | 把检索作为 Step 记录并支持 resume | 检索结果只存在聊天上下文 |
| Tool Gateway | 校验 RetrievalTool schema 和风险等级 | Agent 直接访问向量库凭据 |
| Policy Gateway | 判断 source、classification、purpose 是否允许 | prompt 说允许就允许 |
| Retrieval Layer | 执行 parse、index、retrieve、rerank、filter | 返回无版本、无来源证据 |
| Memory Gate | 区分知识库、会话记忆、长期记忆 | 把临时回答写成长期事实 |
| Context Pack | 控制进入模型的证据包 | 检索结果未经裁剪直接塞给模型 |
| Eval Gate | 评估召回、忠实度、引用、安全、成本 | 只看最终答案好不好听 |
| Observability | 记录 retrieval、rerank、context、answer span | 出错后不知道哪层失败 |
| Release Governance | 管理索引、embedding、reranker、评测集版本 | 索引变更无评测、无回滚 |

## 3. 必须版本化的对象

| 对象 | 版本字段 | 为什么必须版本化 |
|---|---|---|
| 文档集 | document_version | 文档更新会改变答案证据 |
| 解析器 | parser_version | 表格、PDF、标题解析会影响 chunk |
| Chunk 策略 | chunker_version | chunk 大小和边界影响召回 |
| 索引 | index_version | 索引是可回滚的发布对象 |
| Embedding 模型 | embedding_version | 向量空间变化会影响相似度 |
| Sparse/BM25 配置 | sparse_index_version | 关键词召回配置会影响覆盖 |
| Reranker | reranker_version | 排序变化会影响上下文质量 |
| Query Rewrite 策略 | rewrite_policy_version | 改写可能提升召回也可能扩大风险 |
| Retrieval Policy | retrieval_policy_version | 权限和过滤规则必须可审计 |
| Context Pack | context_pack_version | 最终上下文决定模型可见证据 |
| Prompt | answer_prompt_version | 回答风格和引用要求会变化 |
| 评测集 | eval_set_version | 没有固定评测集无法比较 |

## 4. 发布门禁

RAG 相关变更不得直接上线。不同变更至少经过下面门禁：

| 变更 | 必跑评测 | 阻塞条件 |
|---|---|---|
| 文档解析器变更 | parsing regression、citation support | 表格/标题丢失、引用错位 |
| chunking 变更 | context recall、chunk hit rate | 关键证据召回下降 |
| embedding 变更 | hit@k、MRR、安全样例 | 召回下降或越权召回 |
| reranker 变更 | context precision、nDCG | 噪声升高或关键证据降序 |
| query rewrite 变更 | hit@k、sensitive query review | 改写引入敏感或越权查询 |
| context pack 变更 | faithfulness、context truncation | 证据被截断或混入无关内容 |
| prompt 变更 | unsupported answer、citation support | 无证据回答上升 |
| policy 变更 | ACL、tenant isolation、red team | 任一越权样例通过 |

## 5. 架构评审问题

每次 RAG 设计评审至少问：

- 这次优化影响哪几个版本对象？
- 如果线上答案退化，能不能回滚到上一版索引和 reranker？
- 检索请求是否一定经过 Tool Gateway 和 Policy Gateway？
- 评测集是否覆盖了正常、困难、越权、注入和新鲜度样例？
- trace 能不能分辨是 retrieval 失败、rerank 失败、context pack 失败还是 generation 失败？
- 成本或延迟优化有没有降低 citation、权限或安全指标？

## 6. Design-only 学习验收

你不需要写出索引发布脚本，但必须能画出并解释：

```text
RAG 变更
-> 影响对象版本
-> 跑对应评测
-> 生成实验报告
-> 通过 release gate
-> 小流量或正式发布
-> 可回滚到上一版本
```

如果一个方案不能说明“怎么评测、怎么审计、怎么回滚”，它就只能算 demo，不能算工业级设计。
