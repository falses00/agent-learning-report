# RAG 索引

更新日期：2026-08-20
用途：说明 RAG 专项怎么学习、何时挂接主线、哪些文件先读。

## 1. RAG 在主线里的位置

RAG 不是独立于 Agent Runtime/Gateway 的另一个项目。它挂接主线：

| 主线阶段 | RAG 插入点 |
|---|---|
| Phase 1 | RAGRequest、RAGResult、Citation、RAGEvalCase 契约 |
| Phase 3 | RAG 工具必须经过 Tool Gateway 和 Policy |
| Phase 5 | RAG 可以作为 MCP tool/resource 暴露 |
| Phase 6 | 区分知识库、会话记忆、长期记忆 |
| Phase 7 | retrieval、citation、faithfulness、安全评测 |
| Phase 8 | retrieval span、rerank span、context pack span |
| Phase 9 | prompt injection、poisoning、tenant escape |
| Phase 11 | index、embedding、reranker、eval set、KnowledgeCard 版本治理 |

## 2. 先读顺序

1. [RAG 教学路线总览](RAG教学路线总览.md)：先看真实工程主线、七个阶段和停止规则。
2. [RAG × Vibe Coding 工程学习路径（2026）](RAG与Vibe-Coding工程学习路径-2026.md)：按任务契约、调查、实现、验证、审查和维护完成作品。
3. [S3 可执行实验](../labs/S03-rag-citations/README.md)：运行 ACL、freshness、citation、refusal 和诊断门禁。
4. [RAG 全链路提升与工业最佳实践（2026）](RAG全链路提升与工业最佳实践-2026.md)：按需查十层链路、25 条路径、源码与来源。
5. [RAG评测数据集设计](../22-评测集/RAG评测数据集设计.md)：扩展真实 failure slice 和发布 blocker。
6. [RAG跨层契约与版本治理](../06-工业级框架蓝图/RAG跨层契约与版本治理.md)：把索引、模型、策略和 eval 一起发布。

## 3. 按问题查当前资料

| 问题 | 先看 |
|---|---|
| 不知道 RAG 怎么开始 | [RAG教学路线总览](RAG教学路线总览.md) |
| 想把 Vibe Coding 用到真实 RAG 交付 | [RAG × Vibe Coding 工程学习路径](RAG与Vibe-Coding工程学习路径-2026.md) |
| 想看全链路提升、源码与最佳实践 | [RAG全链路提升与工业最佳实践（2026）](RAG全链路提升与工业最佳实践-2026.md) |
| 想按故障信号选择第一动作 | [S3 可执行诊断实验](../labs/S03-rag-citations/README.md) |
| 召回差、噪声多、引用错 | [RAG 全链路提升与工业最佳实践](RAG全链路提升与工业最佳实践-2026.md)的十层诊断与 25 条路径 |
| 想做评测集 | [RAG评测数据集设计](../22-评测集/RAG评测数据集设计.md)与 [S3 可执行诊断实验](../labs/S03-rag-citations/README.md) |
| 想讲安全和多租户 | [S3 可执行诊断实验](../labs/S03-rag-citations/README.md)与主课程 S8 Security |
| 想接入长线 Agent | [RAG跨层契约与版本治理](../06-工业级框架蓝图/RAG跨层契约与版本治理.md) |
| 想知道外部 RAG 资料能不能进入课程 | [LLM-Wiki 知识层调研](../10-GitHub项目调研/LLM-Wiki知识层调研-2026-07-02.md)、[LLM-Wiki 知识层与可维护扩展方案](../08-学习可视化前端设计/09-LLM-Wiki知识层与可维护扩展方案.md) |
| 想更新、降级或淘汰资料 | [项目维护规范](../../MAINTENANCE.md) |

## 4. 已退出主线的参考档案

以下 2026-06-30 文档保留部分模板或历史审计价值，但不再维护为当前学习路线，也不进入前端课程导航：

| 档案 | 保留价值 | 当前替代 |
|---|---|---|
| `RAG逐课教学手册.md`、`RAG问题诊断与最优解矩阵.md` | 旧问题清单和课堂拆分 | `RAG教学路线总览.md` + 页面诊断实验 |
| `RAG小项目三段式训练法.md`、`RAG小项目实验课程.md` | 小项目观察模板 | `RAG与Vibe-Coding工程学习路径-2026.md` |
| `RAG实验执行模板.md`、`RAG闭环实验报告模板.md` | 实验记录字段 | 新手册的 Plan/Contract/Verify/Review 流程 |
| `RAG失败样例与评测集设计.md`、`RAG评测回归与观测手册.md` | 历史 case 分类 | `22-评测集/RAG评测数据集设计.md` + 可运行 eval |
| `RAG安全多租户与数据治理.md`、`RAG长线Agent集成手册.md` | 专题背景 | S3/S8 可执行门禁 + 跨层版本治理 |

若档案内容与当前主线冲突，以当前主线、可执行实验和维护规范为准。

## 5. 学习原则

- 不从向量库 demo 开始。
- 不因为某项目热门就直接引入。
- 每个优化都必须有失败样例、指标、上线判断。
- 安全、跨租户、引用、版本治理失败必须优先于效果指标。
- 外部 RAG 技术资料先进入 KnowledgeSource / SourceReview / KnowledgeCard / KnowledgeVersion / ImportQueue，再进入课程或评测样例。

## 6. 资料生命周期

| 状态 | 用法 |
|---|---|
| 当前采用 | 可进入主线，但仍要在 OpsPilot 数据和预算上复现 |
| 持续观察 | 新论文、快速变化框架和自动评测工具，只进入候选实验 |
| 历史基础 | 用于理解 RAG、HyDE、Self-RAG 等方法演进，不代表当前默认 |
| 已退出主线 | 记录淘汰原因与替代项，不再作为推荐入口 |

本轮已把 `langchain-classic` 的 `ParentDocumentRetriever` 从当前主来源移出，替换为框架无关 parent-child 契约和当前 `RecursiveRetriever` 源码；旧的“按方法名逐级升级”路线也已退出主线。
