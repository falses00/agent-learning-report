# RAG 失败样例与评测集设计

生成日期：2026-06-30  
目标：先设计失败样例，再谈优化。没有失败样例，就没有可靠教学。

## 1. 数据集分层

| 数据集 | 用途 | 最少样本 |
|---|---|---:|
| `rag_smoke` | 快速确认链路可用 | 10 |
| `rag_golden` | 常规业务正确性 | 50 |
| `rag_hard_retrieval` | 召回困难、短查询、同义词、跨语言 | 30 |
| `rag_multihop` | 多跳、跨文档、实体关系 | 30 |
| `rag_long_document` | 长 PDF、手册、合同、政策 | 20 |
| `rag_table_structured` | 表格、清单、字段、单位 | 20 |
| `rag_security_redteam` | 注入、投毒、越权、敏感信息 | 30 |
| `rag_regression` | 历史失败样本 | 持续增长 |

## 2. 样本字段

```json
{
  "case_id": "rag_case_001",
  "dataset": "rag_hard_retrieval",
  "question": "用户问题",
  "tenant_id": "tenant_demo",
  "workspace_id": "workspace_demo",
  "principal_role": "analyst",
  "expected_answer": "期望答案",
  "expected_doc_ids": ["doc_001"],
  "expected_citations": [
    {
      "doc_id": "doc_001",
      "page": 3,
      "span": "..."
    }
  ],
  "must_not_retrieve": ["doc_other_tenant"],
  "risk_tags": ["short_query", "permission"],
  "evaluation": {
    "retrieval": true,
    "faithfulness": true,
    "security": true
  }
}
```

## 3. 失败类型

| 失败类型 | 示例 | 进入哪个集合 |
|---|---|---|
| 没召回 | 文档里有答案，但 topK 没命中 | `rag_hard_retrieval` |
| 召回噪声 | topK 里大多无关 | `rag_hard_retrieval` |
| 引用不支持 | 答案引用的段落不能证明结论 | `rag_golden` |
| 多跳断裂 | 单篇文档答不完整 | `rag_multihop` |
| 长文丢细节 | 长手册中的例外条款找不到 | `rag_long_document` |
| 表格误读 | 金额、单位、列名错 | `rag_table_structured` |
| 旧知识覆盖新知识 | 旧政策被当成当前政策 | `rag_regression` |
| 跨租户召回 | A 用户召回 B 租户文档 | `rag_security_redteam` |
| 注入成功 | 文档指令诱导模型泄密或越权 | `rag_security_redteam` |
| 缓存误命中 | 相似问题返回旧答案 | `rag_regression` |

## 4. 教学样例包

第一版教学样例建议只用 mock 数据：

- `tickets.json`：10 条工单。
- `kb_articles.md`：20 篇脱敏知识库文章。
- `policy_versions.md`：包含旧版和新版流程。
- `tables.csv`：包含 SLA、优先级、费用、状态字段。
- `malicious_docs.md`：包含 prompt injection 和污染样例。

不要一开始接真实企业知识库。

## 5. 验收指标

| 指标 | 最低线 |
|---|---:|
| smoke pass | 100% |
| hard retrieval hit@5 | >= 80% 初始，优化后持续提升 |
| context precision | 不因 topK 增大明显恶化 |
| citation support | >= 95% |
| access violation | 0 |
| critical attack success | 0 |
| p95 latency | 场景定义 |
| cost/query | 场景定义 |

## 6. 回归规则

任何线上或实验失败都必须判断是否进入：

- `rag_regression`。
- `rag_security_redteam`。
- `rag_hard_retrieval`。
- `rag_long_document`。

未进入回归的失败，不算真正修复。
