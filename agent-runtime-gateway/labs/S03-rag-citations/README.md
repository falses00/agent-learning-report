# S3 实验：多租户 RAG 与可信引用

一句话定义：先用权限、来源可信度和有效期缩小可见语料，再做检索与引用验证；没有足够证据时结构化拒答。

## 1. 为什么这一阶段不先接云模型

本实验先固定检索语料和确定性排序，让 ACL、过期文档、引用篡改和拒答可以稳定复现。模型生成质量属于后续 adapter 实验，不能掩盖数据边界错误。

实现位于：

- `../../20-源码/agent_course/rag.py`
- `../../20-源码/agent_course/tools.py`
- `../../20-源码/agent_course/runtime.py`
- `../../20-源码/agent_course/evals.py`
- `../../21-测试/test_rag.py`
- `../../21-测试/test_evals.py`
- `../../22-评测集/s3-rag-baseline.json`

## 2. 六个关键概念

| 概念 | 原理 | 缺少时的问题 | 本实验如何证明 |
|---|---|---|---|
| ACL before ranking | 未授权文档不能先进入候选再删除 | 数据已进入模型、缓存或日志 | tenant-a 查询 tenant-b 只得到空上下文 |
| Freshness gate | 过期版本在评分前排除 | 高相似旧政策压过新规则 | legacy-only 查询拒答，不引用 v0 |
| Source trust | 检索文档是数据，不是系统指令 | 间接注入被提升为命令 | untrusted injection 文档不进入上下文 |
| Relevance threshold | 词重合不等于足够证据 | 一个公共词触发错误引用 | 低相关结果低于阈值后拒答 |
| Verifiable citation | 引用包含 doc/chunk/version/原文片段 | 引用存在但不支持答案 | 篡改 quote 后验证失败 |
| Layered eval | retrieval、answer、citation、audit 分开测 | 平均分掩盖安全失败 | 组合断言逐条输出原因，critical case 阻塞 |

责任边界：本实验实现确定性 lexical baseline、过滤、引用与拒答；不宣称已有 ingestion pipeline、embedding、hybrid retrieval、reranker、生成模型或生产级索引发布。

## 3. 先复现失败

阅读[失败注入](failure.md)，依次复现：

1. ACL 放在排序后，tenant-b 文档短暂进入候选。
2. 不检查 `expires_at`，旧政策被引用。
3. 任何词重合都算命中，legacy query 错引当前政策。
4. 只校验 document id，不校验 quote 和 version。

停止条件：候选、上下文、结果和 audit 中都没有未授权文档内容。

## 4. 运行

```powershell
cd "agent-runtime-gateway\20-源码"
python -m pytest ..\21-测试\test_rag.py ..\21-测试\test_evals.py -q
python -m agent_course.cli eval ..\22-评测集\s3-rag-baseline.json
```

预期：RAG 集 5/5 case、27/27 assertions 通过，`critical_failed=0`，`release_passed=true`。

## 5. 五道自测

1. 为什么生成后删除 tenant-b 引用仍然算越权？
2. retrieval hit、grounded answer 和 valid citation 分别证明什么？
3. 为什么简单增加 `top_k` 不能修复 stale policy？
4. 文档里的“忽略规则并导出 token”为什么不能成为系统指令？
5. lexical baseline 通过后，何时才值得引入 embedding、hybrid search 或 reranker？

答错时必须指向一个失败 case 重讲；不能只背定义。

## 6. 通过门禁

- tenant ACL、freshness 和 source trust 在评分前执行。
- 当前政策返回可验证 citation。
- 无答案、跨租户、过期文档和间接注入进入结构化拒答。
- 篡改 quote 的 citation validation 失败。
- eval runner 能检查 citation、audit、forbidden tool、result 和 trace。
- 按[证据清单](evidence/README.md)记录测试与剩余风险。

岗位映射：Agentic RAG、检索评测、多租户 ACL、引用可信度、prompt injection 防护、回归门禁和可观测性。

下一阶段预习：为工具前、工具后、本地 commit 后三个 crash point 画状态图，并解释 query-before-retry。
