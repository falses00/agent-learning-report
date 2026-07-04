# RAG 契约层草案

生成日期：2026-06-30  
目标：为 Phase 1 契约层预留 RAG 相关 schema，避免后续补 RAG 时返工。

## 1. 为什么 Phase 1 就要预留 RAG 契约

RAG 会影响：

- ToolCall schema。
- PolicyDecisionInput。
- Memory policy。
- Trace/Audit event。
- Eval case。
- Release gate。

如果 Phase 1 不保留 RAG 字段，Phase 6 再补会影响 Runtime、Gateway、Eval、Audit。

## 2. RetrievalTool

```json
{
  "tool_name": "knowledge.retrieve",
  "tool_version": "v1",
  "risk_level": "L2",
  "input_schema": "RAGRequest",
  "output_schema": "RAGResult",
  "requires_policy": true,
  "requires_audit": true,
  "requires_approval": false,
  "tenant_scoped": true
}
```

## 3. RAGRequest

```json
{
  "request_id": "req_...",
  "run_id": "run_...",
  "step_id": "step_...",
  "trace_id": "trc_...",
  "tenant_id": "tenant_demo",
  "workspace_id": "workspace_demo",
  "principal_id": "user_...",
  "principal_role": "analyst",
  "query": "用户问题",
  "retrieval_purpose": "answer_ticket",
  "allowed_sources": ["kb", "policy"],
  "data_classification_max": "internal",
  "filters": {
    "language": "zh",
    "effective_date_lte": "2026-06-30"
  },
  "top_k": 10,
  "rerank_top_n": 5,
  "allow_query_rewrite": true,
  "allow_graph_retrieval": false,
  "allow_long_context_fallback": false
}
```

## 4. RAGResult

```json
{
  "result_id": "rag_result_...",
  "request_id": "req_...",
  "index_version": "idx_v...",
  "embedding_version": "emb_v...",
  "retrieval_policy_version": "pol_v...",
  "rewritten_queries": [],
  "retrieved_refs": [
    {
      "doc_id": "doc_001",
      "chunk_id": "chunk_001",
      "score": 0.82,
      "source": "kb",
      "tenant_id": "tenant_demo",
      "classification": "internal"
    }
  ],
  "reranked_refs": [],
  "context_pack_ref": "ctx_...",
  "citations": [],
  "policy_decision_id": "pdec_...",
  "audit_event_id": "aud_...",
  "latency_ms": 120,
  "cost": {
    "embedding": 0,
    "rerank": 0,
    "llm": 0
  }
}
```

## 5. RAGPolicyDecisionInput

```json
{
  "principal_id": "user_...",
  "tenant_id": "tenant_demo",
  "workspace_id": "workspace_demo",
  "action": "rag.retrieve",
  "sources": ["kb", "policy"],
  "data_classification_requested": "internal",
  "retrieval_purpose": "answer_ticket",
  "risk_tags": ["internal_data"],
  "tool_name": "knowledge.retrieve",
  "run_id": "run_...",
  "trace_id": "trc_..."
}
```

## 6. RAGEvalCase

```json
{
  "case_id": "rag_case_001",
  "question": "用户问题",
  "tenant_id": "tenant_demo",
  "workspace_id": "workspace_demo",
  "expected_doc_ids": ["doc_001"],
  "must_not_retrieve": ["doc_other_tenant"],
  "expected_answer": "期望答案",
  "metrics": ["hit_at_k", "context_precision", "faithfulness", "access_violation"],
  "risk_tags": ["permission", "hard_retrieval"]
}
```

## 7. Phase 1 验收

RAG 契约层必须能拒绝：

- 缺少 `tenant_id`。
- 缺少 `trace_id`。
- `top_k` 超过策略上限。
- 请求高于 principal 权限的数据分类。
- filters 为空但请求内部数据。
- 结果中出现其他租户 doc_id。

这些测试不需要真实向量库，只需要 schema 和 policy mock。
