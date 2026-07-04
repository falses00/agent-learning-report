# Phase 02 - 最小运行时教学手册

生成日期：2026-06-30  
学习模式：Design-only  
目标：让你不写代码，也能理解 Agent loop 为什么必须被建模成 Run、Step、Event、State 和 Checkpoint，而不是一段聊天记录。

## 1. 本阶段解决的失控风险

如果没有最小运行时，Agent 会变成一段无法复盘的对话：

- 模型做了几步不知道。
- 工具失败后状态丢失。
- 重试时可能重复执行副作用。
- 中断后只能重新开始。
- 最终答案错了，但不知道是哪一步错。

Phase 2 的目标不是让 Agent 很聪明，而是让 Agent 的每一步都有结构。

## 2. 本阶段边界

本阶段只学习运行时最小语义：

```text
Task
-> Run
-> Step
-> Event
-> State
-> Checkpoint
-> Error
```

不提前做：

- 真实模型网关。
- 真实工具网关。
- MCP 接入。
- 长期记忆。
- 多 Agent。
- UI Console。

## 3. 课时拆分

| 课时 | 主题 | 你要理解 | Design-only 产物 |
|---|---|---|---|
| 2.1 | Run 与 Task | 用户目标和一次执行实例不是一回事 | Task/Run 责任卡 |
| 2.2 | Step 与 Event | Agent 运行要拆成可审计步骤 | Step/Event 流程图 |
| 2.3 | State 与 Checkpoint | 状态必须显式保存，不能靠聊天记录 | Checkpoint 设计卡 |
| 2.4 | ErrorModel | 失败必须可分类、可恢复、可审计 | 错误分类表 |
| 2.5 | Loop Guard | 防止无进展循环和无限工具调用 | 停止条件表 |

## 4. 课堂练习

### 练习 A：画最小运行链路

把一次“帮我处理工单”的请求画成：

```text
Task
-> Run created
-> Step 1 classify_ticket
-> Event model_call
-> Step 2 retrieve_policy
-> Event tool_call_requested
-> Step 3 draft_reply
-> Checkpoint saved
-> Run completed
```

你不需要写代码，只需要说明每个节点为什么存在。

### 练习 B：设计坏运行

设计 5 个失败：

| 失败 | 应该怎么记录 |
|---|---|
| 模型输出非法结构 | `invalid_model_output` |
| 工具超时 | `tool_timeout` |
| 同一步重复调用同一工具 | `loop_guard_triggered` |
| checkpoint 写入失败 | `checkpoint_failed` |
| step 超过最大步数 | `max_step_exceeded` |

### 练习 C：区分聊天记录和运行状态

回答：

- 聊天记录能否证明某个工具已经执行？
- 聊天记录能否防止重复副作用？
- 聊天记录能否作为审计证据？
- checkpoint 里至少要保存什么？

## 5. 失败案例

| 失败案例 | 为什么严重 | 正确设计 |
|---|---|---|
| Agent 卡在“继续分析”循环 | 成本失控，任务不结束 | max step、loop guard、no-progress detection |
| 工具失败后模型继续编造结果 | 用户拿到假结果 | structured error + retry/escalate |
| 进程重启后任务消失 | 长线任务不成立 | checkpoint + resume |
| 重试导致重复提交工单 | 副作用重复 | operation_id + idempotency |

## 6. 架构评审问题

- Run 和 Task 的区别是什么？
- Step 是否可以被单独重试？
- Event 是调试日志，还是审计事实？
- Checkpoint 保存的是最终答案，还是可恢复状态？
- 什么情况下应该 stop、retry、escalate、quarantine？
- 如果模型一直给出无效输出，最多修复几轮？

## 7. Design-only 过关标准

你应该能复述：

```text
Phase 2 解决的是 Agent 行为不可复盘、不可恢复的问题。
Run 是一次执行实例，Step 是可审计可重试的动作，Event 是发生过的事实，Checkpoint 是恢复依据。
聊天记录不能替代状态，因为它不能保证幂等、恢复、审计和失败分类。
```

## 8. 后续 Implementation-later 门禁

后续工程阶段才需要：

- 定义 Run/Step/Event/State 数据结构。
- 跑一个正常 run。
- 跑一个失败 run。
- 证明 trace_id 全链路传递。
- 证明 loop guard 生效。
- 证明工具失败转成 ErrorModel。

## 9. 进入 Phase 3 条件

Design-only 进入条件：

- 你能画出最小运行链路。
- 你能解释为什么状态不是聊天记录。
- 你能设计至少 3 个运行时失败样例。
- 你能说明下一阶段为什么要引入 Gateway 和 Tool Governance。
