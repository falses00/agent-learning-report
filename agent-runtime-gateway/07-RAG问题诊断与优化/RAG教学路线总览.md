# RAG 教学路线总览

生成日期：2026-06-30  
目标：让学习者知道面对不同 RAG 问题时，如何诊断、选型、实验、评测和上线，而不是只会搭一个向量库 demo。

## 1. 核心判断

工业级 RAG 不是一个组件，而是一条链路：

```text
Data Ingestion
-> Parsing / Chunking
-> Indexing
-> Query Understanding
-> Retrieval
-> Reranking / Filtering
-> Context Packing
-> Generation
-> Citation / Verification
-> Evaluation
-> Observability
-> Security / Governance
```

在 Agent Runtime Gateway 中，RAG 还必须接入：

- Agent Gateway：身份、租户、请求追踪。
- Tool Gateway：检索工具注册、schema、审计。
- Policy Gateway：ACL、数据等级、多租户过滤。
- Memory Gate：长期记忆写入、召回、删除。
- Eval Gate：检索、答案、轨迹、安全回归。
- Observability：trace、span、cost、latency、drift。

## 2. 课程主线

| 阶段 | 名称 | 解决的问题 | 实验产物 | 验收指标 |
|---|---|---|---|---|
| RAG-00 | 失败模式导入 | 为什么 naive RAG 不可靠 | 一组失败问题 | 失败可复现 |
| RAG-01 | Baseline PDF/KB RAG | 端到端最小链路 | PDF/Markdown 知识库问答 | answer accuracy、citation support |
| RAG-02 | Parsing 与 Chunking | 切块丢上下文、表格乱、长文断裂 | normal/semantic/late chunking 对比 | context recall、chunk hit rate |
| RAG-03 | Query Rewrite | 短查询、多轮省略、跨语言 | HyDE、multi-query、decomposition | hit@k、MRR |
| RAG-04 | Hybrid + Rerank | 召回不足和噪声太多 | BM25 + vector + reranker | context precision、nDCG |
| RAG-05 | Graph / Hierarchy | 多跳、全局主题、知识冲突 | RAPTOR、GraphRAG、LightRAG | multi-hop F1、path validity |
| RAG-06 | Adaptive / Corrective | 检索失败如何自修复 | Self-RAG、CRAG | recovery success、unsupported answer rate |
| RAG-07 | Memory + RAG | 长线 Agent 如何记忆和召回 | memory write/read gate | memory precision、leakage rate |
| RAG-08 | Eval + Observability | 怎么证明优化有效 | Ragas/Promptfoo/Phoenix-style report | regression pass rate |
| RAG-09 | Security + Multi-Tenant | 注入、投毒、越权召回 | RAG red team、ACL tests | attack success rate、access violation |
| RAG-10 | Cost / Latency | 成本高、延迟高、缓存误命中 | semantic cache、routing、topN 控制 | cost/query、p95 latency |
| RAG-11 | Industrial Integration | 接入 Agent Runtime Gateway | RAG tool + trace + policy + eval gate | trace/audit coverage |

配套文档：

| 文档 | 用途 |
|---|---|
| `RAG逐课教学手册.md` | 把每个课时拆成失败、实验、指标、上线判断和复述验收 |
| `RAG闭环实验报告模板.md` | 每次优化都按问题、假设、变量、指标、结论记录 |
| `RAG小项目三段式训练法.md` | 把 GitHub 小项目转成设计模式，不要求背代码 |
| `RAG失败样例与评测集设计.md` | 把失败样例沉淀成 regression case |
| `../22-评测集/RAG评测数据集设计.md` | 设计 RAG 评测集分层和发布阻塞规则 |
| `../02-阶段教学手册/第1阶段-RAG契约层补充手册.md` | 在 Phase 1 就理解 RAG 契约责任 |
| `../06-工业级框架蓝图/RAG跨层契约与版本治理.md` | 把 RAG 纳入版本、评测、审计和发布治理 |

## 3. 先学问题，再学工具

学习顺序必须是：

```text
先复现失败
-> 定位失败在哪一层
-> 选择最小优化
-> 做对照实验
-> 用指标证明
-> 写入回归集
-> 决定是否上线
```

不能反过来因为某个项目热门，就强行把 GraphRAG、ColBERT、CRAG 都塞进系统。

## 4. 大项目与小项目的搭配

| 类型 | 用途 | 示例 |
|---|---|---|
| 大项目 | 建立抽象和工程基线 | LlamaIndex、LangChain、GraphRAG、Ragas、Phoenix |
| 小项目 | 学单点优化技巧 | late-chunking、semantic-chunkers、HyDE、CRAG、RAPTOR、ModelCache |
| 论文实现 | 理解方法边界 | Self-RAG、CRAG、RAPTOR、HyDE |
| Benchmark | 验证改动是否真的好 | EnterpriseRAG-Bench、Ragas、Promptfoo |

大项目教“系统怎么看”，小项目教“问题怎么解”。

## 5. 和主课程阶段的关系

| 主课程阶段 | RAG 插入点 |
|---|---|
| Phase 1 契约层 | 定义 RetrievalTool、RAGRequest、RAGResult、Citation schema |
| Phase 3 Gateway | RAG 工具必须经 Tool Gateway 和 Policy Gateway |
| Phase 5 MCP | RAG 可暴露为 MCP tool/resource，但权限仍在 Gateway |
| Phase 6 Memory | 区分 Knowledge RAG、Session Memory、Long-term Memory |
| Phase 7 Eval | 增加 retrieval eval、faithfulness、red team |
| Phase 8 Observability | 为 retrieval、rerank、context pack、answer 记录 span |
| Phase 9 Security | 加入 prompt injection、poisoning、tenant escape |
| Phase 11 Release | RAG index、embedding、reranker、eval set 版本一起发布 |

## 6. 学完后的能力

你应该能做到：

- 看到 RAG 失败时，判断是 parsing、chunking、retrieval、rerank、context packing、generation、权限还是数据新鲜度问题。
- 面对问题选择最小优化，而不是盲目上复杂框架。
- 设计 baseline 与优化版对照实验。
- 用 recall、precision、faithfulness、citation、latency、cost、security 指标判断是否值得上线。
- 把失败案例写入 regression set。
