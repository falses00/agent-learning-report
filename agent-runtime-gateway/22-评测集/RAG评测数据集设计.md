# RAG 评测数据集设计

生成日期：2026-06-30  
用途：定义 RAG 评测集如何设计、分层、版本化和进入发布门禁。当前阶段不要求你写评测代码，只要求你能设计出可审核的数据集。

## 1. 评测集的作用

RAG 评测集不是考试题库，而是工业级护栏：

```text
每一次文档、索引、embedding、reranker、prompt、policy 或 memory 变化，都要证明旧问题没有重新失败。
```

没有评测集时，优化通常会变成“这次看起来回答更好”。有评测集时，优化才能变成：

- 哪类问题改善了。
- 哪类问题退化了。
- 哪些安全样例必须阻塞上线。
- 哪个版本引入了回归。

## 2. 数据集分层

| 分层 | 目的 | 示例 |
|---|---|---|
| smoke | 快速确认链路可用 | 简单政策问答，必须命中单个文档 |
| hard_retrieval | 检验召回能力 | 同义词、短查询、跨语言、省略上下文 |
| rerank_noise | 检验排序和去噪 | top_k 有相似但错误片段 |
| multi_hop | 检验跨文档综合 | 需要两个以上文档才能回答 |
| table_or_pdf | 检验解析质量 | 表格列、PDF 标题、页码引用 |
| freshness | 检验版本和新鲜度 | 新政策覆盖旧政策 |
| citation | 检验证据支持 | 答案必须引用具体 chunk |
| security | 检验注入和投毒 | 文档内指令要求泄露秘密 |
| tenant_acl | 检验多租户隔离 | 不得召回其他租户 doc |
| memory_boundary | 检验记忆边界 | 会话记忆不得污染企业知识库 |
| cost_latency | 检验成本延迟 | 限制 top_k、rerank_top_n、cache |

## 3. JSONL 字段

每一行是一条评测样例。字段建议如下：

| 字段 | 必填 | 说明 |
|---|---|---|
| case_id | 是 | 稳定 ID，不能随意改 |
| category | 是 | smoke、security、tenant_acl 等 |
| question | 是 | 用户问题 |
| tenant_id | 是 | 所属租户 |
| workspace_id | 是 | 工作空间 |
| principal_role | 是 | 发起者角色 |
| allowed_sources | 是 | 允许检索的数据源 |
| knowledge_card_ids | 否 | 关联的 KnowledgeCard，用于证明答案引用的是已审核知识卡 |
| source_review_ids | 否 | 关联的 SourceReview，用于判断来源 license、freshness、质量是否可用 |
| data_classification_max | 是 | 允许的数据等级 |
| expected_doc_ids | 是 | 应该命中的文档 |
| must_not_retrieve | 是 | 禁止召回的文档或租户 |
| expected_answer_rules | 是 | 答案必须包含/禁止包含/是否允许拒答 |
| metrics | 是 | 本 case 关注哪些指标 |
| risk_tags | 是 | 风险标签 |
| failure_type | 是 | 这个 case 防止哪类失败 |
| release_blocker | 是 | 失败是否阻塞发布 |

## 4. 设计样例前先问的问题

你可以这样和 Codex 交互：

```text
请基于这个 RAG 失败，帮我设计一条评测样例。
不要写代码，先用表格说明：
问题属于哪一类；
期望召回哪些 doc；
必须禁止召回哪些 doc；
应该看哪些指标；
失败是否阻塞上线。
最后再转成 JSONL。
```

## 5. 验收标准

一个合格的 RAG 评测集至少满足：

- 覆盖正常路径和困难路径。
- 覆盖至少一个 prompt injection 样例。
- 覆盖至少一个跨租户禁止召回样例。
- 覆盖至少一个旧信息和新信息冲突样例。
- 每条 case 都能说明失败类型。
- 每条 case 都知道失败是否阻塞发布。
- 评测集版本能和索引、embedding、reranker、prompt 版本一起记录。
- freshness、citation、unsupported_answer 类 case 必须能关联 KnowledgeCard 或说明为什么不需要知识卡。
- 外部资料进入评测集前必须有 KnowledgeSource 和 SourceReview，不能把未知 license 内容直接变成评测事实。

## 6. 发布门禁

| 失败类型 | 是否阻塞发布 | 原因 |
|---|---|---|
| access_violation | 必须阻塞 | 安全和合规风险 |
| tenant_escape | 必须阻塞 | 跨租户数据泄漏 |
| prompt_injection | 必须阻塞 | 外部数据控制模型行为 |
| unsupported_answer | 通常阻塞 | 幻觉风险 |
| bad_citation | 通常阻塞 | 答案不可验证 |
| retrieval_miss | 视范围阻塞 | 关键业务问题必须阻塞 |
| cost_regression | 视阈值阻塞 | 影响 SLA 和预算 |
| latency_regression | 视阈值阻塞 | 影响体验和吞吐 |

## 7. 用户复述验收

你应该能这样解释：

```text
RAG 评测集不是为了追求一个总分，而是为了把每类失败固定下来。
当索引、embedding、reranker、prompt 或权限策略变化时，我能用这些 case 判断有没有回归。
安全、跨租户和注入失败不是普通低分，而是发布阻塞项。
```
