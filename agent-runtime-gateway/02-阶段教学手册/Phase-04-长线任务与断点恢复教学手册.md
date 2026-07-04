# Phase 04 - 长线任务与断点恢复教学手册

生成日期：2026-06-30  
学习模式：Design-only  
目标：让你理解长线 Agent 为什么必须支持 checkpoint、resume、retry、cancel、fork、human-in-the-loop 和幂等。

## 1. 本阶段解决的失控风险

长线任务最大的风险不是“答错一次”，而是：

- 做到一半进程崩溃。
- 用户中途补充或撤回需求。
- 高风险操作需要人工审批。
- 工具成功了但 Agent 以为失败，重复执行。
- 一个任务跑几十步后无法复盘。

Phase 4 的目标是让任务可暂停、可恢复、可重试、可取消、可审计。

## 2. 本阶段边界

本阶段学习：

```text
Checkpoint
Resume
Retry
Cancel
Fork
Human-in-the-loop
Idempotency
Quarantine
```

不做：

- 完整 workflow engine 实现。
- 真实数据库迁移。
- 多 Agent 协作。
- UI 审批控制台。

## 3. 课时拆分

| 课时 | 主题 | 你要理解 | Design-only 产物 |
|---|---|---|---|
| 4.1 | Checkpoint | 保存的是可恢复状态，不是聊天摘要 | checkpoint 内容表 |
| 4.2 | Resume | 从最近安全点继续，不重做副作用 | resume 时间线 |
| 4.3 | Retry 与幂等 | 重试不能重复提交写操作 | operation_id 设计卡 |
| 4.4 | HITL | 高风险步骤暂停等待人类决定 | approval 状态图 |
| 4.5 | Fork/Cancel/Quarantine | 分支、取消和隔离是不同语义 | 状态转换表 |
| 4.6 | Durable execution 对照 | checkpoint 与 Temporal/DBOS/Restate/Dapr 的边界 | 对照表 |

## 4. 课堂练习

### 练习 A：设计 checkpoint 内容

一个 checkpoint 至少应该说明：

- run_id。
- step_id。
- current_state。
- completed_operations。
- pending_approval。
- context_refs。
- tool_result_refs。
- memory_refs。
- error_state。
- next_allowed_actions。

### 练习 B：推演中断恢复

场景：

```text
Step 1 读取工单成功
Step 2 检索政策成功
Step 3 生成关闭账号操作计划
Step 4 等待人工审批
进程崩溃
```

你要回答：

- 恢复后从哪一步继续？
- 是否可以重复执行 Step 2？
- 是否可以直接执行 Step 4？
- approval_ticket 存在哪里？

### 练习 C：对比 durable execution

说明差异：

| 概念 | 解决什么 |
|---|---|
| Agent checkpoint | 保存 Agent 运行状态 |
| Durable workflow | 保存业务流程和可靠执行语义 |
| Idempotency key | 防止重复副作用 |
| Audit event | 证明发生过什么 |

## 5. 失败案例

| 失败案例 | 根因 | 正确设计 |
|---|---|---|
| retry 重复关闭客户账号 | 没有 operation_id | 幂等键 + completed_operations |
| 审批后上下文丢失 | approval 未进 checkpoint | approval_ticket 写入状态 |
| 用户取消后 Agent 继续调工具 | cancel 语义不清 | cancel 后禁止新工具调用 |
| 检索版本变化导致恢复后答案不同 | context/index refs 缺失 | checkpoint 记录版本引用 |

## 6. 架构评审问题

- Checkpoint 保存全部上下文还是引用？
- 哪些 step 可以 retry，哪些只能人工处理？
- operation_id 由谁生成，在哪里校验？
- resume 后是否允许模型重新规划？
- fork 与 retry 有什么区别？
- 什么失败应该 quarantine 而不是继续 retry？

## 7. Design-only 过关标准

你应该能复述：

```text
Phase 4 解决的是长线任务不可恢复和副作用不可控。
Checkpoint 保存可恢复状态，resume 从安全点继续，retry 必须受幂等约束，高风险步骤进入 HITL，无法安全继续的任务进入 quarantine。
保存聊天记录不等于 durable execution。
```

## 8. 后续 Implementation-later 门禁

后续工程阶段才需要：

- checkpoint 能保存并恢复。
- 重复 operation_id 不产生重复副作用。
- approval resume 能从暂停点继续。
- cancel 后不再调用工具。
- max step guard 生效。
- 失败任务能进入 quarantined 状态。

## 9. 进入 Phase 5 条件

Design-only 进入条件：

- 你能画出 checkpoint/resume 时间线。
- 你能解释 retry、resume、fork、cancel 的区别。
- 你能设计一个高风险审批场景。
- 你能说明下一阶段为什么要把外部工具标准化成 MCP/Tool Registry。
