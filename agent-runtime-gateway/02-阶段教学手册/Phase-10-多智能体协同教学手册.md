# Phase 10 - 多智能体协同教学手册

生成日期：2026-07-01  
学习模式：Design-only  
目标：让你理解多 Agent 的价值不是“多写几个角色”，而是把复杂任务拆成有责任边界、结构化 handoff、共享状态、资源锁、冲突仲裁、循环终止和协同评测的工作流。

## 1. 本阶段解决的失控风险

如果多 Agent 只是自由聊天：

- Planner、Executor、Reviewer 责任不清。
- Agent 之间传递的是自然语言片段，状态丢失。
- 两个 Agent 同时修改同一资源。
- Reviewer 没有证据就宣布通过。
- 互相反驳但没有仲裁和停止条件。
- 一个 Agent 绕过 Tool Gateway 调工具。
- 多 Agent 让成本和延迟失控。

Phase 10 的目标是让协同可控、可审计、可评测，而不是把复杂性包装成“团队感”。

## 2. 本阶段边界

本阶段学习：

```text
Role Contract
Graph Workflow
Handoff Schema
Shared State
Resource Lock
Reviewer Evidence
Verifier Gate
Arbiter
Loop Guard
Collaboration Eval
```

不做：

- 真实多 Agent 框架接入。
- 真实并发调度实现。
- 自动让多个 Agent 写同一文件。
- 用角色扮演代替结构化状态。

## 3. 先建立一个判断

多 Agent 只有在下面条件成立时才有价值：

```text
任务确实可分解；
每个角色有独立责任；
handoff 是结构化的；
共享状态可版本化；
冲突有仲裁；
结果能被评测。
```

否则单 Agent 加工具和 reviewer/verifier gate 往往更简单、更可靠、更便宜。

## 4. 课时拆分

| 课时 | 主题 | 你要理解 | Design-only 产物 |
|---|---|---|---|
| 10.1 | 是否需要多 Agent | 多 Agent 不是默认答案 | 协同必要性判断表 |
| 10.2 | 角色契约 | 每个 Agent 有职责、权限和禁止项 | role contract |
| 10.3 | Handoff Schema | 交接必须结构化 | handoff schema 卡 |
| 10.4 | Shared State | 共享事实、待决策、风险和版本 | shared state 表 |
| 10.5 | Resource Lock | 防止并发写冲突 | resource lock 矩阵 |
| 10.6 | Arbiter/Loop Guard | 冲突和循环必须终止 | stop condition 表 |
| 10.7 | Collaboration Eval | 评测协同质量而非聊天流畅 | 协同评测矩阵 |

## 5. 课堂练习

### 练习 A：判断是否需要多 Agent

| 场景 | 是否需要多 Agent | 原因 |
|---|---|---|
| 简单问答 | 不需要 | 单 Agent + RAG 足够 |
| 高风险工具发布审核 | 需要 Reviewer/Verifier | 需要独立审查和证据 |
| 长线工单处理 | 可需要 | Planner/Executor/HITL/Verifier 分工明确 |
| 单文件小改动 | 通常不需要 | 多 Agent 成本高且容易冲突 |
| 多来源研究和方案对比 | 适合 researcher + reviewer | 可并行读资料，但主线程合并证据 |

### 练习 B：设计 handoff schema

handoff 至少要包含：

| 字段 | 目的 |
|---|---|
| handoff_id/run_id/trace_id | 可追踪 |
| from_agent/to_agent | 责任边界 |
| reason | 为什么交接 |
| accepted_facts | 已确认事实 |
| rejected_facts | 已拒绝事实 |
| open_questions | 未决问题 |
| state_ref | 共享状态版本 |
| tool_permissions | 接收方允许的工具 |
| risk_flags | 风险提示 |
| success_criteria | 完成标准 |
| stop_conditions | 停止条件 |

### 练习 C：处理冲突

场景：

```text
Reviewer 认为计划风险太高，Executor 认为可以继续执行。
```

你要说明：

- 谁有最终仲裁权？
- 是否需要 human approval？
- 当前 state_version 是否冻结？
- 是否允许 Executor 继续调用工具？
- 冲突是否进入 audit？
- 这个冲突是否需要新增评测 case？

## 6. 失败案例

| 失败案例 | 根因 | 正确设计 |
|---|---|---|
| 多个 Agent 同时改同一文件 | 无资源锁 | 单写多读 + lock TTL |
| Reviewer 只说“看起来不错” | 无证据要求 | reviewer 必须引用 trace/eval/diff |
| Handoff 丢失权限上下文 | 只传自然语言 | handoff schema + state_ref |
| Agent 互相循环修改计划 | 无 loop guard | max_handoffs + no_progress_counter |
| Executor 绕过 Tool Gateway | 角色权限错误 | 所有工具仍经 Tool Gateway |
| 多 Agent 成本失控 | 无预算和停止条件 | per-role budget + max turns |

## 7. 架构评审问题

- 为什么这里需要多 Agent，而不是单 Agent 加 gate？
- 每个角色的职责和禁止项是什么？
- handoff 是否能被机器和人同时审计？
- 共享状态如何版本化和回滚？
- 资源锁如何避免死锁？
- Reviewer 和 Verifier 的证据标准是什么？
- 循环、冲突、无进展如何终止？
- 协同质量如何进入 regression eval？

## 8. Design-only 过关标准

你应该能复述：

```text
Phase 10 解决的是复杂任务协同失控。
多 Agent 不是角色越多越强，而是责任边界、结构化 handoff、共享状态、资源锁、仲裁、loop guard 和协同评测的组合。
所有 Agent 仍然必须服从 Runtime、Tool Gateway、Policy、Memory Gate、Audit 和 Eval。
```

## 9. 后续 Implementation-later 门禁

后续工程阶段才需要：

- handoff schema 校验通过率 100%。
- role boundary violation 为 0 critical。
- resource lock 能阻止并发写。
- no-progress/loop guard 能终止循环。
- Reviewer/Verifier 输出必须带证据引用。
- 多 Agent eval 覆盖冲突、死锁、越权、重复工作。

## 10. 参考锚点

- [多 Agent 协同契约](../06-工业级框架蓝图/多Agent协同契约.md)
- [运行时状态机与恢复语义](../06-工业级框架蓝图/运行时状态机与恢复语义.md)
- [测评审核体系](../04-测评审核体系/测评审核体系.md)
- [资料核验记录-2026-07-01](../10-GitHub项目调研/资料核验记录-2026-07-01.md)
- [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/overview/)
- [Google ADK](https://adk.dev/)

## 11. 进入 Phase 11 条件

Design-only 进入条件：

- 你能判断一个任务是否真的需要多 Agent。
- 你能设计 role contract 和 handoff schema。
- 你能说明共享状态和资源锁如何防冲突。
- 你能设计 loop guard 和 arbiter 规则。
- 你能说明下一阶段为什么发布治理必须锁定 prompt、model、tool、policy、memory、eval、sandbox 和 runtime 的组合版本。
