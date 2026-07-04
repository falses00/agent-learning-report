# 多 Agent 协同契约

生成日期：2026-06-30  
目标：让多 Agent 协同可控、可审计、可评测，而不是多个角色自由聊天。

## 1. 基本原则

多 Agent 的价值不是“更多角色”，而是把复杂任务拆成可验证的责任边界。

本项目只允许契约化协同：

- 每个 Agent 有明确角色、输入、输出和权限。
- Agent 之间通过结构化 handoff 传递状态。
- 共享状态必须版本化和审计。
- 工具调用仍只能通过 Tool Gateway。
- 失败、冲突、循环必须能被检测和终止。

## 2. 标准角色

| 角色 | 职责 | 禁止 |
|---|---|---|
| Router | 判断任务类型、选择流程 | 不直接调用高风险工具 |
| Planner | 拆解任务、生成计划和验收点 | 不伪造验证结果 |
| Executor | 按计划执行低风险步骤 | 不绕过 Tool Gateway |
| Reviewer | 审查计划、输出、风险和缺口 | 不改写事实来源 |
| Verifier | 运行测试、评测、恢复演练 | 不只做语言评价 |
| Arbiter | 处理冲突、终止循环、升级人工 | 不替代审计记录 |

## 3. Handoff 数据结构

```json
{
  "handoff_id": "hof_...",
  "run_id": "run_...",
  "from_agent": "planner",
  "to_agent": "executor",
  "reason": "execute approved low-risk plan",
  "task": {},
  "state_ref": "state_v...",
  "accepted_facts": [],
  "open_questions": [],
  "tool_permissions": [],
  "risk_flags": [],
  "success_criteria": [],
  "stop_conditions": [],
  "trace_id": "trc_...",
  "created_at": "ISO-8601"
}
```

Handoff 不能只是一段自然语言。自然语言说明可以存在，但必须附着在结构化字段之后。

## 4. 共享状态

共享状态至少包含：

- task goal。
- accepted facts。
- rejected facts。
- pending decisions。
- tool results。
- memory refs。
- artifact refs。
- risk flags。
- owner locks。
- evaluation status。

所有共享状态更新必须有：

- actor。
- reason。
- diff。
- state_version。
- trace_id。

## 5. 资源锁

多 Agent 同时处理资源时必须有锁：

| 资源 | 锁策略 |
|---|---|
| 文件 | 单写多读，写锁有 TTL |
| 工单 | 一个 executor 持有写锁，reviewer 只读 |
| 记忆记录 | 写入需 memory write gate，更新需版本比较 |
| 工具凭据 | 不进入 Agent 间 handoff，只由 Credential Broker 注入 |
| 外部系统操作 | operation_id + approval ticket |

## 6. 循环与冲突防护

必须设置：

- max_agent_turns。
- max_handoffs。
- max_reviewer_rejections。
- no_progress_counter。
- repeated_state_hash guard。
- resource_wait_timeout。
- human_escalation_threshold。

触发后进入 `paused`、`quarantined` 或 `waiting_approval`，不能无限协商。

## 7. 协同评测

| 指标 | 目标 |
|---|---:|
| handoff_schema_pass_rate | 100% |
| role_boundary_violation_rate | 0 critical |
| duplicate_work_rate | 可观测并持续下降 |
| conflict_resolution_success | >= 95% |
| deadlock_guard_effective | 100% known cases |
| verifier_evidence_rate | 100% high-risk changes |

## 8. 教学练习

学习者必须能演示：

1. Planner 生成计划，Executor 执行，Reviewer 找到风险，Verifier 运行验证。
2. Executor 尝试越权工具调用，被 Tool Gateway 拒绝并进入 audit。
3. 两个 Agent 争用同一资源，锁和仲裁机制生效。
4. 多轮无进展后触发 stop condition，而不是无限循环。

通过标准：每一步都能在 trace 中看到 handoff、state diff、policy decision 和最终 verdict。
