# RAG 长线 Agent 集成手册

生成日期：2026-06-30  
目标：把 RAG 接入可长线运行的 Agent，而不是一次性问答。

## 1. 为什么长线 Agent 的 RAG 更难

普通 RAG 只回答一次。长线 Agent 会：

- 多轮查询同一知识库。
- 在任务中写入记忆。
- 根据检索结果调用工具。
- 暂停、恢复、重试。
- 经过人工审批后继续。
- 在上下文越来越大的情况下保持正确。

因此 RAG 必须具备版本、状态、审计和回放能力。

## 2. 必须版本化的对象

| 对象 | 为什么 |
|---|---|
| document_version | 文档变化会改变答案 |
| index_version | chunking/embedding/index rebuild 会改变召回 |
| embedding_version | embedding 模型变化会改变近邻 |
| reranker_version | rerank 会改变上下文顺序 |
| retrieval_policy_version | 权限和过滤变化影响可见证据 |
| context_packer_version | 上下文裁剪会改变答案 |
| memory_policy_version | 长期记忆会影响未来任务 |
| eval_set_version | 判断标准必须可追踪 |

## 3. Runtime 集成

每个 RAG step 至少记录：

```json
{
  "step_type": "rag.retrieve",
  "run_id": "run_...",
  "step_id": "step_...",
  "trace_id": "trc_...",
  "query": "...",
  "rewritten_queries": [],
  "retrieval_policy_version": "policy_v...",
  "index_version": "idx_v...",
  "retrieved_refs": [],
  "reranked_refs": [],
  "context_pack_ref": "ctx_...",
  "citations": [],
  "latency_ms": 0,
  "cost": 0
}
```

checkpoint 必须保存 RAG refs，而不是把所有文本塞进状态。

## 4. 恢复语义

| 场景 | 处理 |
|---|---|
| 检索服务失败 | 标记 recoverable，允许 retry |
| index_version 变化 | resume 时优先使用 checkpoint 记录的旧版本；如果旧版本被 tombstone、权限撤回或保留期过期，必须 rebase 或暂停人工确认 |
| 文档被删除 | context pack 失效，进入 paused 或重新检索 |
| 权限变更 | resume 前重新做 policy check |
| 记忆被撤回 | 从 context pack 移除，并记录 memory correction |
| reranker 变更 | 不影响旧 checkpoint，影响新 run |

## 4.1 RAG Artifact 保留、Tombstone 与 Rebase

长线恢复需要可重放，但合规要求不允许旧证据无限可用。因此 RAG artifact 必须有生命周期。

| Artifact | 保留策略 | 失效策略 | 审计要求 |
|---|---|---|---|
| document_version | 按租户和数据分类配置 | 删除请求、权限撤回、过期 | 记录 source、owner、delete_reason |
| index_version | 保留最近 N 个可恢复版本 | tombstone 后不可用于新 run | 记录 rebuild reason、embedding_version |
| embedding_vector | 跟随 document_version | 文档删除或分类升级时强制失效 | 记录 vector store deletion result |
| context_pack | 只保存 refs 和 hash，避免长期保存敏感全文 | 任一 ref tombstone 后失效 | 记录 pack_version、ref_status |
| citation | 保留 doc_id/page/span，不暴露未授权正文 | 权限撤回后只显示受限引用 | 记录 access check |
| memory_ref | 跟随 memory lifecycle | 删除/纠错后从恢复上下文移除 | 记录 correction event |

Rebase 规则：

- 如果旧 index 仍有效，resume 可使用旧 index/context refs。
- 如果旧 index 被 tombstone，但文档仍允许访问，必须用新 index 重新检索并记录 `rebase_reason`。
- 如果文档被删除或权限撤回，Run 进入 `paused` 或 `quarantined`，不能自动用旧 context 继续生成。
- 如果权限变化影响结果，必须重新做 retrieval policy check。
- 所有 rebase 都必须写 trace 和 audit。

## 5. Agentic RAG Loop

推荐结构：

```text
Plan retrieval need
-> Choose retriever
-> Rewrite/decompose query
-> Retrieve
-> Rerank/filter
-> Pack context
-> Check evidence support
-> Answer or repair
-> Write trace/eval signals
```

失败时：

```text
no evidence -> rewrite/decompose/HyDE
low precision -> rerank/filter
conflict -> source priority/effective date/conflict answer
unsafe evidence -> reject/quarantine
expensive route -> cache/cheap retriever/skip expensive rerank
```

## 6. 教学验收

学习者必须能演示：

- 同一问题在 index v1 和 v2 下答案为什么不同。
- checkpoint 恢复时如何使用旧 context refs。
- 权限变更后为什么必须重新 policy check。
- RAG 失败如何进入 CRAG/Self-RAG repair loop。
- 线上失败样本如何变成 regression case。
