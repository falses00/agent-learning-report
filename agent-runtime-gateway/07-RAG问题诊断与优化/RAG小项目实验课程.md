# RAG 小项目实验课程

生成日期：2026-06-30  
目标：用小而尖项目训练具体优化能力，而不是只学大框架 API。

## 1. 实验总规则

每个实验都必须包含：

- baseline。
- 优化方案。
- 失败样例。
- 指标。
- trace。
- 结论：采用、放弃、待复核。

小项目只用于学习和复现实验，不默认作为生产依赖。

## 2. 实验路线

| 实验 | 项目参考 | 学什么 | 成功标准 |
|---|---|---|---|
| RAG-Lab-01 PDF baseline | pdfGPT、ragbase | 朴素 PDF/Markdown RAG | 能复现 3 个成功和 3 个失败问题 |
| RAG-Lab-02 Chunking | semantic-chunkers、late-chunking、rag-when-how-chunk | chunk size、semantic boundary、late chunking | context recall 提升且噪声可控 |
| RAG-Lab-03 Query Rewrite | HyDE、AutoHyDE、EasyRAG | HyDE、multi-query、query decomposition | hit@k/MRR 提升 |
| RAG-Lab-04 Hybrid + Rerank | RAG-Retrieval、ColBERT、byaldi | dense + sparse + reranker | precision/nDCG 提升 |
| RAG-Lab-05 Graph / Hierarchy | nano-graphrag、RAPTOR、LightRAG | 多跳、层级摘要、实体关系 | multi-hop QA 改善 |
| RAG-Lab-06 Corrective RAG | Self-RAG、CRAG、CRAG-Ollama-Chat | 检索评估、纠错、拒答 | unsupported answer rate 下降 |
| RAG-Lab-07 Eval Regression | AutoRAG、Giskard、EnterpriseRAG-Bench | 自动评测、回归集、配置搜索 | 每次优化有报告 |
| RAG-Lab-08 Security | Rebuff、garak、Veritensor | prompt injection、poisoning、PII | attack success rate 下降 |
| RAG-Lab-09 Cache + Gateway | ModelCache、semantic-cache、mimir | 成本、延迟、缓存误命中 | cost/query 降低且质量不退化 |
| RAG-Lab-10 Memory + RAG | memory-lancedb-pro、SimpleMem、ReMe、memsearch | 长期记忆、召回、遗忘 | memory leakage 为 0 critical |
| RAG-Lab-11 MCP Knowledge Tool | knowledge-rag | RAG 作为 MCP/tool 接入 Gateway | trace/audit/policy 全覆盖 |
| RAG-Lab-12 Multimodal/PDF Table | byaldi、NexusRAG、pdf-to-markdown | 图像页、表格、版面解析 | page/cell citation 准确 |
| RAG-Lab-13 Code RAG | CodeRAG、codegraph-rust | 代码符号、调用关系、图检索 | 回答能对应文件/符号/测试 |

## 3. 每个实验的教学说明模板

```text
这个实验解决什么问题：
为什么 baseline 会失败：
参考小项目：
我们采用什么：
我们不采用什么：
如何复现：
如何评测：
成本/延迟变化：
安全风险：
能否进入主架构：
```

## 4. 课程落地顺序

推荐顺序：

```text
PDF baseline
-> chunking
-> query rewrite
-> hybrid + rerank
-> eval regression
-> graph/hierarchy
-> corrective RAG
-> security
-> memory + RAG
-> cache/gateway
-> multimodal/table/code
```

原因：先让学习者感受到 naive RAG 的失败，再逐步增加复杂度。GraphRAG、CRAG、ColBERT、semantic cache 都必须在 baseline 和指标存在后再上。
