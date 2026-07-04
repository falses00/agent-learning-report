# Phase 07 - 测评审核与红队教学手册

生成日期：2026-07-01  
学习模式：Design-only  
目标：让你理解工业级 Agent 的准确率不是靠感觉判断，而是靠 contract eval、tool eval、RAG eval、memory eval、trajectory eval、security red team、long-run eval、cost/latency gate 和发布阻塞规则共同证明。

## 1. 本阶段解决的失控风险

如果没有测评审核体系：

- demo 看起来能跑，但真实任务一变就失败。
- 只测最终答案，不测工具选择、轨迹、记忆、权限和恢复。
- 新模型或新 prompt 上线后悄悄退化。
- 安全红队样例没有进入回归集。
- 线上事故复盘后没有沉淀成评测样例。
- 成本、延迟、失败率没有成为发布门禁。

Phase 7 的目标是让每一次能力提升都有证据，每一次失败都能变成回归样例。

## 2. 本阶段边界

本阶段学习：

```text
Eval Taxonomy
Golden Set
Adversarial Set
Regression Set
Trajectory Eval
Tool Eval
RAG Eval
Memory Eval
Security Red Team
Release Gate
```

不做：

- 真实 CI/CD 配置。
- 真实 eval runner 编写。
- 把某一个 eval 平台当唯一标准。
- 用主观打分替代结构化 case。

## 3. 先建立一个判断

你需要把评测拆成两类：

```text
能力是否达标
风险是否被拦住
```

Ragas、DeepEval、Promptfoo、Inspect AI、Langfuse、Phoenix 等工具可以帮助执行或观测，但课程重点不是记工具名，而是设计评测分类、样例、指标、阈值和阻塞规则。

## 4. 课时拆分

| 课时 | 主题 | 你要理解 | Design-only 产物 |
|---|---|---|---|
| 7.1 | Eval Taxonomy | 不同能力要用不同评测 | 评测分类矩阵 |
| 7.2 | Golden/Regression | 正常能力和历史失败都要固定 | golden/regression case 表 |
| 7.3 | Tool Eval | 评测工具选择、参数、拒绝和审批 | tool eval 样例 |
| 7.4 | RAG Eval | 评测召回、引用、权限、新鲜度 | RAG eval 样例 |
| 7.5 | Memory Eval | 评测召回、污染、过期、泄漏 | memory eval 样例 |
| 7.6 | Trajectory Eval | 评测中间步骤，不只最终答案 | trajectory rubric |
| 7.7 | Red Team | 注入、越权、泄漏、沙箱逃逸 | 红队样例表 |
| 7.8 | Release Gate | 失败如何阻塞发布 | 发布门禁规则 |

## 5. 评测分类矩阵

| 评测层 | 评测什么 | 典型阻塞条件 |
|---|---|---|
| contract eval | 输入输出 schema、字段缺失、坏输入 | schema 不兼容、坏输入崩溃 |
| tool eval | 工具选择、参数、allow/deny/approval | 越权工具被执行 |
| RAG eval | recall、rerank、citation、freshness、permission | 无引用回答、跨租户召回 |
| memory eval | recall、precision、pollution、TTL、delete | 记忆污染、删除后仍召回 |
| trajectory eval | planning、step、retry、checkpoint、handoff | 绕过网关、重复副作用 |
| long-run eval | resume、cancel、fork、idempotency | 崩溃后丢任务或重复写操作 |
| security eval | injection、exfiltration、SSRF、secret leakage | 泄密、越权、沙箱逃逸 |
| cost/latency eval | token、工具次数、延迟、失败率 | 成本或延迟超过预算 |

## 6. 课堂练习

### 练习 A：把一个需求拆成评测 case

需求：

```text
工单 Agent 能读取知识库，判断退款政策，并生成处理建议。
```

你要至少设计：

| case 类型 | 样例 |
|---|---|
| golden | 正常问题能引用正确政策 |
| hard | 用户描述模糊，需要 query rewrite |
| permission | 用户无权限读取某租户政策 |
| tool | 应该调用 retrieval tool，不应调用写工具 |
| memory | 不把一次性工单信息写长期记忆 |
| injection | 用户要求忽略政策直接退款 |
| regression | 过去失败过的同义词召回问题 |

### 练习 B：设计发布阻塞规则

把评测结果映射成发布决策：

| 失败 | 是否阻塞 | 原因 |
|---|---|---|
| schema 不兼容 | 阻塞 | 下游无法稳定消费 |
| 跨租户召回 | 阻塞 | 隐私和权限失效 |
| RAG 引用缺失 | 高风险场景阻塞 | 无法证明答案来源 |
| 记忆污染 | 阻塞 | 会长期影响后续任务 |
| 成本上升 8% | 看预算 | 若超过错误预算则阻塞 |
| 单个非关键措辞偏差 | 不一定阻塞 | 进入 backlog 或观察 |

### 练习 C：把事故变成回归样例

场景：

```text
线上发现 Agent 在恢复任务后重复提交了一次关闭账号操作。
```

你要写出：

- 事故属于哪一类评测缺口？
- 新增 regression case 的输入是什么？
- 期望轨迹是什么？
- 哪些字段必须出现在 trace/audit？
- 下次发布的阻塞条件是什么？

## 7. 失败案例

| 失败案例 | 根因 | 正确设计 |
|---|---|---|
| 只看最终答案准确率 | 忽略工具和轨迹 | 分层 eval taxonomy |
| 每次手工试几个问题 | 无固定数据集 | golden + regression set |
| 红队失败修完就忘 | 未回流评测集 | 每个事故变 regression case |
| 新模型上线后工具误选 | 无 tool eval | 工具选择和参数单独评测 |
| 记忆删除后仍召回 | 无 memory eval | deletion/tombstone case |
| 成本暴涨但答案没变 | 无 cost gate | 成本和延迟进入门禁 |

## 8. 架构评审问题

- 这个 case 测的是答案、工具、RAG、记忆、轨迹、安全还是成本？
- 失败后应该阻塞发布、降级、回滚还是进入 backlog？
- 每个线上事故是否都变成 regression case？
- 评测数据是否带版本、owner、适用场景和风险等级？
- 评测是否覆盖 allow、deny、approval、error？
- 新模型、新 prompt、新工具、新索引、新记忆策略是否都触发相应评测？
- 评测报告是否能追到 trace、audit、policy、memory 和 retrieval 版本？

## 9. Design-only 过关标准

你应该能复述：

```text
Phase 7 解决的是“我觉得能用”没有证据的问题。
工业级 Agent 要分层评测：契约、工具、RAG、记忆、轨迹、长线恢复、安全、成本和延迟。
评测不是一次性跑分，而是发布门禁、事故回流、回归阻塞和持续审计。
```

## 10. 后续 Implementation-later 门禁

后续工程阶段才需要：

- 每个 Phase 有 golden、adversarial、regression case。
- eval runner 能输出版本化报告。
- 发布前必须跑 contract/tool/RAG/memory/security/trajectory 的关键集。
- 失败 case 自动进入 regression backlog。
- 评测结果能关联 trace_id、run_id、tool_version、policy_version、memory_snapshot、index_version。
- 阻塞规则可被 CI 或发布流程执行。

## 11. 参考锚点

- [测评审核体系](../04-测评审核体系/测评审核体系.md)
- [测评审核门禁矩阵](../06-工业级框架蓝图/测评审核门禁矩阵.md)
- [测评审核升级蓝图](../06-工业级框架蓝图/测评审核升级蓝图.md)
- [RAG 评测数据集设计](../22-评测集/RAG评测数据集设计.md)
- [Ragas](https://docs.ragas.io/)
- [DeepEval](https://docs.confident-ai.com/)
- [Promptfoo](https://www.promptfoo.dev/docs/intro/)
- [Inspect AI](https://inspect.aisi.org.uk/)

## 12. 进入 Phase 8 条件

Design-only 进入条件：

- 你能把一个需求拆成至少 7 类评测 case。
- 你能说明哪些失败必须阻塞发布。
- 你能把一次事故转成 regression case。
- 你能解释为什么只测最终答案不够。
- 你能说明下一阶段为什么需要 trace、span、metrics、replay 和 audit 来定位失败原因。
