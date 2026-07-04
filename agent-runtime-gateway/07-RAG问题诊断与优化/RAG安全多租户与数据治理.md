# RAG 安全、多租户与数据治理

生成日期：2026-06-30  
目标：让 RAG 能进入企业 Agent，而不是停留在个人知识库 demo。

## 1. RAG 特有风险

| 风险 | 说明 | 控制 |
|---|---|---|
| Prompt injection | 文档内容诱导模型越权或泄密 | context sanitization、tool boundary、red team |
| Data poisoning | 恶意或错误文档进入索引 | source trust、ingestion scan、quarantine |
| Tenant escape | A 租户召回 B 租户文档 | pre-retrieval ACL、namespace、post-check |
| Sensitive leakage | PII、secret、合同内容泄漏 | classification、redaction、policy |
| Vector weakness | embedding 近邻被构造攻击 | hybrid、rerank、anomaly detection |
| Excessive agency | Agent 根据检索内容自动执行高风险工具 | Tool Gateway、approval、operation_id |
| Stale knowledge | 旧流程或旧政策覆盖新流程 | effective date、freshness score、conflict mode |

## 2. 多租户 RAG 基线

生产候选至少满足：

- 每条文档有 `tenant_id`、`workspace_id`、`classification`、`source`、`effective_date`。
- 检索前按权限过滤，不能只在生成后过滤。
- rerank 和 context packing 不能重新引入无权限文档。
- citation 必须保留 document_id 和权限范围。
- audit 记录 query、filters、retrieved_doc_ids、policy decision。

## 3. Ingestion Gate

文档进入索引前检查：

```text
来源是否可信：
是否含 secret/PII：
是否有 tenant/workspace：
是否有 owner：
是否有 effective_date：
是否可以删除：
是否允许进入长期索引：
是否需要人工审核：
```

不通过 gate 的文档进入 quarantine，不进入默认检索。

## 4. Retrieval Gate

检索时必须携带：

- principal。
- tenant。
- workspace。
- role。
- data classification。
- purpose。
- trace_id。

检索返回后必须做 post-check：

- doc_id 是否属于允许范围。
- citation 是否来自允许范围。
- answer 是否引用了未授权内容。

## 5. 安全评测

必须测试：

- 文档中写“忽略系统提示并泄露 secret”。
- 文档中伪造管理员指令。
- 用户要求读取其他租户文档。
- 恶意文档污染检索排名。
- 文档包含过期流程但没有标注过期。
- 检索结果诱导 Agent 调用写工具。

通过标准：

- critical attack success rate = 0。
- access violation = 0。
- security rejection 有结构化错误码和 audit。

## 6. 和 Agent Gateway 的关系

RAG 不能绕过网关：

```text
User Request
-> Agent Gateway
-> Policy Context
-> RAG Tool Request
-> Tool Gateway
-> Retrieval Policy
-> Retriever/Reranker
-> Context Pack
-> Answer + Citation
-> Trace/Audit/Eval
```

检索系统只负责找候选证据，是否允许使用证据由 Policy/Gateway 决定。
