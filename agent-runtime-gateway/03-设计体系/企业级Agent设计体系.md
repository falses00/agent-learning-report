# 企业级 Agent 设计体系

生成日期：2026-06-29  
用途：把本项目要教会你的设计能力拆成层次，避免只学零散框架。

## 1. 总体分层

```text
用户与业务入口
-> Agent Gateway
-> Agent Runtime
-> Orchestration
-> Model Gateway
-> Tool Gateway
-> Memory System
-> Evaluation System
-> Observability & Audit
-> Security Isolation
-> Governance Plane
```

每一层都有一个核心问题：

| 层 | 核心问题 | 不能只靠什么 |
|---|---|---|
| Agent Gateway | 谁能请求 Agent，请求如何进入系统 | 不能只靠 API route |
| Agent Runtime | Agent 如何运行、暂停、恢复 | 不能只靠聊天记录 |
| Orchestration | 单 Agent、多 Agent、人工如何协同 | 不能只靠角色扮演 prompt |
| Model Gateway | 模型如何路由、限流、降级、计费 | 不能把模型 API 直接散落在代码里 |
| Tool Gateway | 工具如何校验、授权、执行、审计 | 不能让模型直接调用工具 |
| Memory System | 什么能记、谁能看、何时忘 | 不能只做向量库 |
| RAG / Retrieval System | 知识如何被解析、检索、重排、引用、评测 | 不能只做 topK 向量召回 |
| Evaluation System | 如何证明质量没有退化 | 不能只看一次 demo 是否成功 |
| Observability & Audit | 失败如何复盘，成本如何归因 | 不能只看应用日志 |
| Security Isolation | 高风险动作如何隔离 | 不能把 Docker 当完整安全边界 |
| Governance Plane | 如何上线、审批、回滚、审计 | 不能靠人脑记流程 |

## 2. Agent Gateway 设计

Agent Gateway 是所有 Agent 请求的入口，不只是 HTTP API。

必须具备：

- 身份认证：识别 `principal`、tenant、workspace。
- 请求标准化：生成 `request_id`、`thread_id`、`trace_id`。
- 配额与预算：限制用户、Agent、模型、工具成本。
- 风险标记：根据场景、用户、工具、数据等级标记风险。
- 路由：把请求送到正确 Agent、Runtime 和模型策略。
- 审计入口：记录请求来源、主体、版本、策略上下文。

教学重点：Gateway 的价值不是“转发”，而是把不可信输入放进可治理边界。

## 3. Runtime 设计

Agent Runtime 负责让 Agent 可恢复、可审计、可重放。

核心对象：

- `Run`：一次任务执行。
- `Step`：任务中的一个动作。
- `State`：结构化状态，不等于 chat history。
- `Checkpoint`：可恢复快照。
- `Event`：模型调用、工具调用、策略决策、记忆读写、人工审批。

教学重点：长线任务准确率不仅来自模型，还来自状态可恢复、错误可分类、轨迹可复盘。

## 4. Tool Gateway 设计

工具调用必须经过四道门：

1. Schema 校验。
2. Policy 决策。
3. Credential Broker。
4. Result Filter + Audit。

关键能力：

- 工具注册：名称、版本、schema、owner、风险等级。
- 参数校验：未知字段、注入文本、跨租户 ID 必须处理。
- 权限分级：读、写、删除、执行、外发数据分级。
- dry-run：高风险操作先生成计划，不直接执行。
- 人工审批：高风险写操作进入审批。
- 幂等：`operation_id` 防止重复副作用。

教学重点：Tool Gateway 是 Agent 安全的主战场。

## 5. Memory System 设计

记忆系统分四层：

| 类型 | 作用 | 风险 |
|---|---|---|
| Short-term Memory | 当前任务上下文 | 上下文爆炸 |
| Episodic Memory | 某次任务发生过什么 | 记录敏感信息 |
| Semantic Memory | 抽取后的事实和偏好 | 错误事实污染 |
| Procedural Memory | 做事方法和流程 | 固化错误习惯 |

记忆写入必须有门禁：

- 来源是否可信。
- 是否包含敏感信息。
- 是否跨租户。
- 是否有过期时间。
- 是否可撤销。
- 是否能被评测。

教学重点：记忆系统不是“把所有东西存起来”，而是“只把该记、可证、可删、可控的东西留下”。

## 6. Evaluation System 设计

评估系统必须覆盖四类对象：

- 最终答案。
- 工具调用。
- Agent 轨迹。
- 安全与治理行为。

最低评测集：

- golden tasks：常规正确性。
- red team tasks：注入、越权、泄漏、危险动作。
- memory tasks：记忆写入、召回、遗忘、跨租户隔离。
- trajectory tasks：是否调用正确工具、是否重复、是否恢复。
- regression tasks：每次变更必须跑。

教学重点：评测不是最后才做，而是每阶段都做。

## 6.1 RAG / Retrieval System 设计

RAG 是知识进入 Agent 的受控通道，不是简单向量库查询。

核心链路：

```text
parse
-> chunk
-> index
-> rewrite/decompose query
-> retrieve
-> rerank/filter
-> pack context
-> cite
-> evaluate
```

关键设计问题：

- chunking：普通切块、语义切块、late chunking、层级切块如何选择。
- retrieval：dense、sparse、hybrid、GraphRAG、LightRAG、long-context fallback 何时使用。
- rerank：什么时候用 cross-encoder、ColBERT、multi-vector。
- safety：检索前 ACL、tenant namespace、prompt injection、poisoning。
- eval：context recall、precision、faithfulness、citation support、latency、cost。

教学重点：RAG 优化必须问题驱动。只有当 baseline 失败、指标证明改进、风险可控时，才引入更复杂方案。

## 7. Multi-Agent 设计

多 Agent 协同要靠协议，不靠“大家聊聊”。

必须定义：

- 角色：planner、executor、reviewer、verifier。
- 输入输出：每个 agent 接收什么、返回什么。
- handoff：谁把任务交给谁，交接哪些状态。
- 共享状态：哪些状态可写，哪些只读。
- 仲裁：冲突时由谁决定。
- 停止条件：最大轮数、重复状态、无进展、人工介入。
- 文件/资源锁：避免多个 agent 写同一资源。

教学重点：多 Agent 的核心不是“更多角色”，而是“更清楚的边界”。

## 8. 安全隔离设计

按风险选择隔离等级：

| 风险 | 示例 | 隔离建议 |
|---|---|---|
| 低 | 只读查询、格式转换 | 进程级限制 + policy |
| 中 | 读本地文件、调用内网 API | 容器 + 网络/文件白名单 |
| 高 | 执行代码、浏览器自动化、写数据库 | gVisor/E2B/microVM + 审批 |
| 极高 | 生产凭据、跨租户数据、外发数据 | 默认禁止，必须人工审批和审计 |

教学重点：沙箱不能替代权限，权限也不能替代沙箱。

## 9. 治理设计

企业上线 Agent 前必须回答：

- 哪个 Agent 版本上线？
- 使用哪个模型、prompt、工具、策略、评估集？
- 谁批准上线？
- 如何回滚？
- 如何证明没有越权？
- 如何导出审计？
- 如何复盘一次失败？

治理不是一个漂亮控制台，而是“发布、审批、评估、观测、审计、回滚”的闭环。
