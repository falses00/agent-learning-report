# RAG 评测回归与观测手册

生成日期：2026-06-30  
目标：证明 RAG 优化真的有效，而不是只靠一次看起来不错的回答。

## 1. 分层指标

| 层 | 指标 | 说明 |
|---|---|---|
| Retrieval | hit@k、MRR、context recall | 是否找到了应该找的证据 |
| Ranking | nDCG、context precision | 证据排序是否靠前且噪声少 |
| Generation | answer accuracy、faithfulness | 答案是否正确且被证据支持 |
| Citation | citation support、source coverage | 引用是否真实支持答案 |
| Security | attack success rate、access violation | 是否被注入、投毒或越权绕过 |
| Cost | cost/query、token/query、cache hit | 是否在预算内 |
| Latency | p50/p95、rerank latency | 是否可上线 |
| Ops | trace coverage、eval regression backlog | 是否可复盘和持续改进 |

## 2. 数据集

至少维护五类：

- Golden QA：常规业务问题。
- Hard Retrieval：短查询、歧义、跨语言、专有名词。
- Multi-Hop：跨文档和实体关系问题。
- Security Red Team：prompt injection、tenant escape、poisoning。
- Regression：历史线上失败和人工纠错。

## 3. CI Gate

RAG 相关变更必须触发：

- chunking config diff。
- embedding model diff。
- retriever config diff。
- reranker diff。
- prompt/context packing diff。
- ACL/retrieval policy diff。
- index rebuild。

阻塞条件：

- critical 安全用例失败。
- access violation > 0。
- faithfulness 明显下降。
- context recall 下降超过阈值。
- citation support 低于阈值。
- 成本或延迟超过预算且没有审批。

## 4. Online Observability

每次 RAG 调用至少记录：

```text
trace_id
run_id
tenant_id
principal_id
query
query_rewrite
retriever_version
embedding_version
index_version
filters
top_k
retrieved_doc_ids
reranker_version
reranked_doc_ids
context_pack_id
answer_id
citations
latency
cost
policy_decision
```

没有这些字段，就无法判断一次失败来自哪里。

## 5. 失败样本回流

失败样本必须进入回归：

| 失败 | 回流到 |
|---|---|
| 找不到证据 | Hard Retrieval |
| 排名靠后 | Ranking Regression |
| 答案无证据 | Faithfulness Regression |
| 旧知识冲突 | Freshness/Conflict Set |
| 越权召回 | Security Red Team |
| 记忆污染 | Memory Eval |
| 成本或延迟异常 | Ops Regression |

## 6. 教学验收

学习者必须能解释：

- 为什么 recall 提升但 precision 下降可能不可上线。
- 为什么 reranker 让答案更准但 p95 延迟超标也可能失败。
- 为什么 LLM-as-judge 不能裁决权限和安全。
- 为什么每次线上事故都必须变成 regression case。
