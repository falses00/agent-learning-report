# 第 1 阶段 - RAG 契约层补充手册

生成日期：2026-06-30  
适用阶段：Phase 1 契约层  
用途：在不写代码的情况下，学会为 RAG 设计可治理、可评测、可审计的结构化契约。

## 1. 为什么 Phase 1 就要讲 RAG 契约

RAG 看似是知识库功能，实际会穿透多个治理边界：

- 它会读取企业数据，所以必须受身份、租户、权限和数据等级约束。
- 它会影响模型回答，所以必须能追踪证据和引用。
- 它会参与长线任务，所以必须记录索引版本和上下文版本。
- 它会被评测和回归，所以必须把失败样例结构化。

如果契约层不提前设计，后面很容易出现“向量库能查，但不知道谁查了什么、为什么查、查到的证据能不能用”的问题。

## 2. 本课不要求你记住字段

你不需要背 `RAGRequest` 或 `RAGResult` 的每个字段。你要理解字段背后的责任：

| 责任 | 需要回答的问题 | 典型字段 |
|---|---|---|
| 身份与租户 | 谁在查？属于哪个 workspace？ | tenant_id、workspace_id、principal_id |
| 追踪与恢复 | 这次检索属于哪个 run/step/trace？ | request_id、run_id、step_id、trace_id |
| 权限与数据等级 | 允许看哪些 source 和 classification？ | allowed_sources、data_classification_max |
| 检索策略 | 查询能不能 rewrite、graph、long context？ | allow_query_rewrite、allow_graph_retrieval |
| 结果证据 | 查到了哪些 chunk，分数和来源是什么？ | retrieved_refs、reranked_refs、citations |
| 版本治理 | 用了哪个索引、embedding、reranker？ | index_version、embedding_version |
| 审计与策略 | 哪个 policy 决策允许了这次检索？ | policy_decision_id、audit_event_id |
| 评测回归 | 这个 case 期望什么，不允许召回什么？ | expected_doc_ids、must_not_retrieve |

## 3. 必须能设计的契约

| 契约 | 设计目的 | 必须挡住的坏情况 |
|---|---|---|
| RetrievalTool | 把 RAG 注册成受控工具 | Agent 绕过 Tool Gateway 直接查库 |
| RAGRequest | 描述一次检索请求 | 缺身份、缺 trace、无限 top_k、请求越权数据 |
| RAGResult | 描述检索结果和证据 | 返回无来源片段、跨租户片段、无版本结果 |
| RetrievedChunk | 描述单个证据块 | chunk 没有 doc_id/source/classification |
| Citation | 连接答案与证据 | 答案无法证明来自哪段材料 |
| ContextPack | 记录最终喂给模型的上下文 | 检索正确但上下文被截断或混入脏数据 |
| RAGError | 结构化表达失败 | 检索失败被模型包装成自信答案 |
| RAGEvalCase | 把失败写入评测集 | 同样的错误下次又发生 |

## 4. 设计卡模板

每设计一个契约，都填一张卡：

| 项目 | 内容 |
|---|---|
| 契约名称 |  |
| 它属于哪一层 | Gateway / Tool / Policy / Memory / Eval / Observability |
| 它防止什么失控 |  |
| 最小必填字段 |  |
| 可选字段 |  |
| 失败时返回什么错误 |  |
| 谁消费它 |  |
| 如何被审计 |  |
| 如何进入评测 |  |

## 5. 坏输入推演

Phase 1 的 RAG 契约验收不需要真实向量库，只需要能解释下面请求为什么必须被拒绝：

| 坏输入 | 应拒绝原因 | 应归类错误 |
|---|---|---|
| 缺少 tenant_id | 无法做租户隔离 | `missing_identity_scope` |
| 缺少 trace_id | 无法审计和复盘 | `missing_trace` |
| top_k = 1000 | 成本和上下文不可控 | `policy_limit_exceeded` |
| 请求 confidential 数据但用户只有 internal 权限 | 数据等级越权 | `classification_violation` |
| allowed_sources 为空却请求企业知识库 | 来源边界不清 | `source_scope_required` |
| 结果包含其他租户 doc_id | 跨租户泄漏 | `tenant_escape_detected` |
| citation 指向不存在的 chunk_id | 引用不可验证 | `invalid_citation` |
| index_version 缺失 | 无法回滚和复现实验 | `missing_version` |

## 6. 架构评审问题

你要学会用这些问题挑战设计：

- 如果 Agent 把知识库当普通工具直接调用，哪一层会拦住？
- 如果检索结果里混入其他租户的 chunk，谁负责发现？
- 如果模型回答引用了不存在的证据，属于生成问题还是契约问题？
- 如果索引更新后答案变了，怎么知道是哪一版索引导致？
- 如果 query rewrite 生成了敏感查询，是否需要 Policy 再检查？
- 如果 long context fallback 被打开，会不会绕过 rerank 和 citation？

## 7. 用户复述验收

本课结束后，你应该能这样复述：

```text
RAG 契约层不是为了让我背字段，而是为了让每次检索都知道谁查、查什么、能看什么、用了哪个版本、证据在哪里、失败怎么归类、以后怎么回归。
如果没有这些契约，RAG demo 可能能回答问题，但不能进入工业级长线 Agent。
```

如果你只能说“RAGRequest 是请求，RAGResult 是结果”，但说不清它们防止什么事故，本课就还没有通过。
