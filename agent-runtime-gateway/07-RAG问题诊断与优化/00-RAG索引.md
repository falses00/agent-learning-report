# RAG 索引

生成日期：2026-06-30  
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

1. [RAG教学路线总览](RAG教学路线总览.md)
2. [RAG逐课教学手册](RAG逐课教学手册.md)
3. [RAG问题诊断与最优解矩阵](RAG问题诊断与最优解矩阵.md)
4. [RAG评测数据集设计](../22-评测集/RAG评测数据集设计.md)
5. [RAG跨层契约与版本治理](../06-工业级框架蓝图/RAG跨层契约与版本治理.md)
6. [LLM-Wiki 知识层与可维护扩展方案](../08-学习可视化前端设计/09-LLM-Wiki知识层与可维护扩展方案.md)

## 3. 按问题查文件

| 问题 | 先看 |
|---|---|
| 不知道 RAG 怎么开始 | [RAG教学路线总览](RAG教学路线总览.md) |
| 想一课一课学 | [RAG逐课教学手册](RAG逐课教学手册.md) |
| 召回差、噪声多、引用错 | [RAG问题诊断与最优解矩阵](RAG问题诊断与最优解矩阵.md) |
| 想训练小项目能力 | [RAG小项目三段式训练法](RAG小项目三段式训练法.md)、[RAG小项目实验课程](RAG小项目实验课程.md) |
| 想设计实验报告 | [RAG实验执行模板](RAG实验执行模板.md)、[RAG闭环实验报告模板](RAG闭环实验报告模板.md) |
| 想做评测集 | [RAG失败样例与评测集设计](RAG失败样例与评测集设计.md)、[RAG评测回归与观测手册](RAG评测回归与观测手册.md) |
| 想讲安全和多租户 | [RAG安全多租户与数据治理](RAG安全多租户与数据治理.md) |
| 想接入长线 Agent | [RAG长线Agent集成手册](RAG长线Agent集成手册.md) |
| 想知道外部 RAG 资料能不能进入课程 | [LLM-Wiki 知识层调研](../10-GitHub项目调研/LLM-Wiki知识层调研-2026-07-02.md)、[LLM-Wiki 知识层与可维护扩展方案](../08-学习可视化前端设计/09-LLM-Wiki知识层与可维护扩展方案.md) |

## 4. 学习原则

- 不从向量库 demo 开始。
- 不因为某项目热门就直接引入。
- 每个优化都必须有失败样例、指标、上线判断。
- 安全、跨租户、引用、版本治理失败必须优先于效果指标。
- 外部 RAG 技术资料先进入 KnowledgeSource / SourceReview / KnowledgeCard / KnowledgeVersion / ImportQueue，再进入课程或评测样例。
