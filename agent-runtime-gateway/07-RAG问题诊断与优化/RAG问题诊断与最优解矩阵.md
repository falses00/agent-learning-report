# RAG 问题诊断与最优解矩阵

生成日期：2026-06-30  
用途：遇到 RAG 问题时，按问题定位、方案组合、风险和指标进行优化。

## 1. 诊断顺序

```text
问题是否来自数据？
-> 是否来自解析/切块？
-> 是否来自查询理解？
-> 是否来自召回？
-> 是否来自排序和过滤？
-> 是否来自上下文打包？
-> 是否来自生成和引用？
-> 是否来自权限、安全、时效或成本？
```

先定位，再优化。不要一上来就换 embedding 或上 GraphRAG。

## 2. 问题矩阵

| 问题 | 典型症状 | 优先方案组合 | 风险 | 验证指标 |
|---|---|---|---|---|
| 召回不足 | 答案说不知道，但知识库有 | hybrid search + multi-query + HyDE + topK 扩展 | 噪声上升、成本升高 | context recall、hit@k、MRR |
| 噪声太多 | 检索很多无关片段 | reranker/cross-encoder + MMR + metadata filter | 误杀边缘证据 | context precision、nDCG、answer F1 |
| 幻觉 | 无证据回答或编造引用 | citation-required prompt + Self-RAG/CRAG + faithfulness eval | 模型伪造引用 | faithfulness、citation support rate |
| 时效性差 | 使用旧政策、旧价格、旧流程 | freshness metadata + recency scoring + incremental indexing | 新旧冲突 | freshness hit rate、staleness incidents |
| 长文档失真 | 长 PDF/合同/手册细节找不到 | hierarchical chunking + RAPTOR + long-context fallback | 摘要丢细节 | long-doc QA accuracy、token cost |
| 表格错误 | 表格单元格、列名、单位答错 | table parser + SQL/DSL tool + raw-cell citation | 表格语义误读 | exact match、cell citation accuracy |
| 多跳问题失败 | 需要跨文档综合时答偏 | GraphRAG/LightRAG + query decomposition + path evidence | 图抽取错误 | multi-hop F1、path validity |
| 权限隔离失败 | 召回别的租户或用户资料 | pre-retrieval ACL + tenant namespace + post-check | 召回率下降、运维复杂 | access violation rate、policy tests |
| 记忆污染 | 错事实长期影响答案 | memory write gate + provenance + decay/retraction | 过度拒绝写入 | memory precision、deletion compliance |
| 成本高 | 每问都多路检索、多模型 rerank | semantic cache + cheap first-stage + route-to-expensive | 缓存陈旧、误命中 | cost/query、cache hit rate、quality delta |
| 延迟高 | p95 不可接受 | two-stage retrieval + async fanout + rerank topN only | 排名质量下降 | p50/p95 latency、nDCG@k |
| 跨语言差 | 中文问英文资料、英文问中文资料 | multilingual embeddings + query translation + HyDE | 翻译偏差 | per-language recall、answer quality |
| 多租户复杂 | 每个客户知识库不同 | per-tenant index/namespace + row-level ACL + audit trace | 索引成本高 | isolation tests、tenant p95 latency |
| 知识冲突 | 不同文档说法不一致 | source priority + effective date + conflict answer mode | 输出保守 | conflict detection、resolution accuracy |
| 评测困难 | 优化后不知道是否更好 | golden + synthetic adversarial + Ragas/DeepEval/Promptfoo CI | judge 偏差 | regression pass rate、human agreement |
| Prompt injection | 文档内容诱导泄密或越权 | context sanitization + tool boundary + RAG red team | 误报/绕过 | attack success rate、blocked unsafe calls |
| 数据投毒 | 知识库被植入恶意内容 | ingestion scanner + source trust + quarantine | 误拦正常文档 | poisoning detection、quarantine precision |
| PDF 解析差 | 表格、图片、页眉页脚污染 | doc parser + layout-aware chunk + multimodal retrieval | 解析成本高 | parse accuracy、page citation |
| 代码知识库差 | 函数/类型/调用链找不到 | symbol-aware chunking + code graph + hybrid search | 索引复杂 | symbol hit rate、answer compile/test pass |
| 长线任务上下文爆炸 | Agent 多轮后上下文越来越乱 | context packer + memory refs + checkpoint summary | 摘要丢因果 | task success、context token budget |

## 3. 决策树

```text
如果知识库里没有答案：
  先解决数据覆盖和更新，不调 RAG。

如果知识库有答案但搜不到：
  先做 query rewrite / hybrid / topK / embedding 对照。

如果搜到了但排序差：
  加 reranker、MMR、metadata filter。

如果需要跨文档推理：
  先 query decomposition，再考虑 GraphRAG/LightRAG。

如果文档很长：
  先 hierarchical chunking / RAPTOR，再考虑 long-context fallback。

如果答案没有证据：
  加 citation-required、faithfulness eval、Self-RAG/CRAG。

如果涉及权限：
  retrieval 前必须 ACL filter，生成后再做 post-check。

如果成本/延迟超标：
  做 route、cache、topN、异步、cheap-first-stage。
```

## 4. 每次优化必须做消融

每次只改一个变量：

- chunk size。
- overlap。
- embedding model。
- sparse/dense 权重。
- reranker。
- query rewrite。
- topK/topN。
- context packing。
- citation prompt。
- ACL filter。

记录：

```text
优化目标：
baseline 配置：
新配置：
数据集版本：
指标变化：
成本变化：
延迟变化：
失败样本：
是否进入 regression：
是否上线：
```
