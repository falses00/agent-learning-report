# Phase 11 - 治理控制台与发布教学手册

生成日期：2026-07-01  
学习模式：Design-only  
目标：让你理解工业级 Agent 的最终交付不是一个 demo，而是一套可发布、可审批、可回滚、可审计、可冻结、可试点、可持续评测的治理体系。

## 1. 本阶段解决的失控风险

如果没有治理发布：

- 改了 prompt 却不知道影响哪些能力。
- 换了模型后工具选择悄悄退化。
- 新增工具没有安全评审就上线。
- 记忆策略变更导致隐私泄漏。
- 评测集被降低门槛但没人审批。
- 线上事故无法回滚到明确版本组合。
- demo 可以跑，但无法进入内部试点或真实业务。

Phase 11 的目标是让每一次变更都有证据包、审批、门禁、放量、回滚和事故复盘。

## 2. 本阶段边界

本阶段学习：

```text
Release Packet
Version Bundle
Change Type
Release Gate
Approval
Rollout
Rollback
Kill Switch
Risk Register
Production Readiness Review
```

不做：

- 真实治理控制台 UI。
- 真实 CI/CD 和灰度系统。
- 真实生产发布。
- 真实权限后台。

## 3. 先建立一个判断

Agent 发布不是只发布代码：

```text
prompt、model、tool、policy、memory、RAG index、eval set、sandbox、runtime 任一变化，都会改变 Agent 行为。
```

所以发布包必须锁定组合版本，而不是只记录服务版本号。

## 4. 课时拆分

| 课时 | 主题 | 你要理解 | Design-only 产物 |
|---|---|---|---|
| 11.1 | Version Bundle | Agent 行为由多个版本共同决定 | 版本组合表 |
| 11.2 | Change Type | 不同变更有不同门禁 | 变更类型矩阵 |
| 11.3 | Release Packet | 发布必须有证据包 | release packet 模板 |
| 11.4 | Approval | 高风险变更需要审批链 | 审批矩阵 |
| 11.5 | Rollout/Rollback | 发布要能灰度和回滚 | 放量与回滚流程 |
| 11.6 | Kill Switch | 事故要能快速停用 | 停止开关设计卡 |
| 11.7 | Production Readiness | 是否可进入真实试点 | 生产就绪审核清单 |

## 5. 课堂练习

### 练习 A：设计版本组合表

一次发布至少锁定：

| 版本项 | 为什么必须锁定 |
|---|---|
| agent_manifest_version | 定义 Agent 能力边界 |
| prompt_version | 影响行为和工具选择 |
| model_route_version | 影响能力、成本和安全 |
| tool_registry_version | 影响可调用工具 |
| policy_version | 影响 allow/deny/approval |
| memory_policy_version | 影响写入、召回、删除 |
| rag_index_version | 影响知识来源 |
| eval_set_version | 影响通过标准 |
| sandbox_profile_version | 影响隔离强度 |
| runtime_gateway_version | 影响状态机和治理链路 |

### 练习 B：判断发布等级

| 变更 | 发布等级 | 门禁 |
|---|---|---|
| 修正文档链接 | docs-only | link check |
| 改 prompt | beta 前至少 golden/redteam/trajectory |
| 新增只读工具 | contract + policy + audit |
| 新增写工具 | approval + dry-run + idempotency + redteam |
| 改 memory 策略 | memory eval + privacy leakage |
| 改 sandbox profile | escape/egress/resource probe |
| 更换模型 | golden + latency/cost + safety |

### 练习 C：写 release packet

你要能写出：

```text
发布名称：
发布等级：
变更摘要：
版本组合：
通过的评测：
红队结果：
trace/audit 覆盖：
SLO 和成本影响：
剩余风险：
审批人：
回滚版本：
回滚步骤：
停止开关：
是否允许进入试点：
```

## 6. 失败案例

| 失败案例 | 根因 | 正确设计 |
|---|---|---|
| prompt 小改导致工具误选 | prompt 未进发布门禁 | prompt 变更触发 tool/trajectory eval |
| 评测集删掉难题后通过率变高 | eval set 无审批 | eval diff + approval |
| 事故后不知道回滚到哪 | 没有版本组合 | release packet 记录全部版本 |
| 新增工具后越权写 | tool gate 缺失 | 工具准入 + policy + redteam |
| 生产试点无停止开关 | 治理缺口 | kill switch + disable path |
| 高风险残留口头接受 | 风险未登记 | risk register + owner + deadline |

## 7. 架构评审问题

- 这次发布改变了哪些行为相关版本？
- 哪些评测必须重新运行？
- 哪些失败会阻塞发布？
- 谁有权批准高风险变更？
- 是否能按租户、工具、Agent 或版本停用？
- 回滚会影响哪些记忆、checkpoint 和外部副作用？
- 事故后如何冻结发布并生成 regression case？
- 这个 release packet 是否足够让新人复盘？

## 8. Design-only 过关标准

你应该能复述：

```text
Phase 11 解决的是 demo 到真实试点之间的治理断层。
Agent 发布必须锁定 prompt、model、tool、policy、memory、RAG、eval、sandbox、runtime 的组合版本。
能发布不等于能生产，必须有证据包、审批、放量、回滚、停止开关、SLO、事故响应和生产就绪审核。
```

## 9. 后续 Implementation-later 门禁

后续工程阶段才需要：

- release packet 可自动生成。
- 发布门禁可阻塞失败变更。
- kill switch 能按 Agent/tool/tenant/version 生效。
- canary/shadow/rollback 流程演练通过。
- production readiness review 全部 critical 项通过。
- 风险登记有 owner、deadline、temporary control。

## 10. 参考锚点

- [工业级发布门禁矩阵](../06-工业级框架蓝图/工业级发布门禁矩阵.md)
- [生产就绪审核清单](../06-工业级框架蓝图/生产就绪审核清单.md)
- [事故响应与复盘模板](../06-工业级框架蓝图/事故响应与复盘模板.md)
- [SLO 与错误预算](../06-工业级框架蓝图/SLO与错误预算.md)
- [资料核验记录-2026-07-01](../10-GitHub项目调研/资料核验记录-2026-07-01.md)

## 11. 课程前置完成判断

Design-only 前置课程可以开始的条件：

- 你能顺序解释 Phase 0-11 各自解决的失控风险。
- 你能说出每个阶段的设计产物和过关问题。
- 你能区分当前 Design-only 证据和后续 Implementation-later 工程证据。
- 你能说明为什么这个项目现在是“可教学、可设计、可评审”，但还不是“已实现、可生产运行”的代码框架。
- 你能接受每次进入真实依赖或代码实现前，都要重新核验官方文档、GitHub release、license、安全边界和评测结果。
