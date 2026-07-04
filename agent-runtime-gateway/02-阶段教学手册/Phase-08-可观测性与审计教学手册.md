# Phase 08 - 可观测性与审计教学手册

生成日期：2026-07-01  
学习模式：Design-only  
目标：让你理解 Agent 的失败必须能定位到具体层级：输入、模型、工具、策略、记忆、RAG、沙箱、checkpoint、handoff、发布版本，而不是只看最终回答。

## 1. 本阶段解决的失控风险

如果没有可观测性和审计：

- 失败后不知道是模型错、工具错、RAG 错、记忆错还是权限错。
- 长线任务恢复后行为变化但无法复现。
- 高风险工具调用没有不可抵赖记录。
- 成本暴涨但不知道是哪类请求造成。
- 线上事故无法回流成 regression case。
- 发布后退化无法定位到 prompt、model、tool、policy、memory 或 index 版本。

Phase 8 的目标是让每一次 Agent 行为可追踪、可复盘、可评测、可审计、可回滚。

## 2. 本阶段边界

本阶段学习：

```text
Trace
Span
Metric
Log
Audit Event
Replay Packet
SLO
Error Budget
Incident Intake
Regression Intake
```

不做：

- 真实 observability 后端部署。
- 真实 OpenTelemetry SDK 接入。
- 线上告警系统配置。
- 商业监控平台选型。

## 3. 先建立一个判断

Trace 和 audit 不是一回事：

```text
trace 用来调试和定位失败。
audit 用来证明谁在什么权限下做了什么决定和动作。
```

trace 可以包含调试细节，但 audit 必须稳定、精简、不可抵赖，且避免泄漏 secret 和敏感原文。

## 4. 课时拆分

| 课时 | 主题 | 你要理解 | Design-only 产物 |
|---|---|---|---|
| 8.1 | Trace 分层 | 每个运行层都要有 span | trace/span 字段表 |
| 8.2 | Audit Event | allow/deny/error/approval 都要审计 | audit event schema 卡 |
| 8.3 | Replay Packet | 复现失败需要版本和引用 | replay packet 模板 |
| 8.4 | Metrics/SLO | 长线可靠性必须量化 | SLO 指标表 |
| 8.5 | Error Budget | 哪些事故预算永远为 0 | 错误预算规则 |
| 8.6 | Incident Intake | 事故如何进入回归集 | 事故到 regression 流程 |
| 8.7 | Observability Backends | Langfuse/Phoenix/OpenTelemetry 的位置 | 后端候选评估卡 |

## 5. 课堂练习

### 练习 A：设计一次工具调用 trace

一次工具调用至少要能串起：

| 字段 | 目的 |
|---|---|
| trace_id | 串联整次运行 |
| run_id | 对应 Agent run |
| step_id | 对应具体步骤 |
| principal/tenant_id | 证明身份和租户 |
| tool_name/tool_version | 定位工具行为 |
| policy_version | 定位策略判断 |
| input_hash/output_ref | 避免记录敏感原文 |
| risk_level | 解释为什么需要审批或沙箱 |
| latency_ms/cost | 成本和性能 |
| verdict | success、denied、failed、quarantined |

### 练习 B：区分 trace 和 audit

判断哪些字段适合 trace，哪些适合 audit：

| 字段 | 放哪里 | 原因 |
|---|---|---|
| 完整模型 prompt | trace 也要谨慎 | 可能含敏感信息 |
| policy_decision | audit 必须有 | 权限决定需要不可抵赖 |
| secret 明文 | 都不能放 | 泄漏风险 |
| tool output hash | trace/audit 都可 | 可复盘但不泄露 |
| approval_ticket | audit 必须有 | 高风险操作证明 |
| token cost | metric/trace | 成本归因 |

### 练习 C：把一次事故变成 replay packet

场景：

```text
发布后 Agent 对同一个退款问题给出不同答案。
```

你要收集：

- prompt_version。
- model_route_version。
- tool_registry_version。
- policy_version。
- memory_snapshot。
- index_version。
- eval_set_version。
- trace_id/run_id。
- 输入摘要和权限上下文。
- 期望答案和失败 verdict。

## 6. 失败案例

| 失败案例 | 根因 | 正确设计 |
|---|---|---|
| 事故后只剩聊天记录 | 缺 trace/span | 每层写 span，保留版本引用 |
| 审计里有 API key | audit 未脱敏 | secret scanner + redaction |
| 工具被拒绝但没有记录 | deny 未写 audit | allow/deny/error 都要 audit |
| RAG 失败无法定位 | retrieval/rerank/context 无 span | RAG 分层 trace |
| 成本暴涨找不到来源 | 无 token/tool metrics | 按 run、tool、tenant、phase 聚合 |
| 修复事故后再次复发 | 未回流 regression | incident -> regression intake |

## 7. 架构评审问题

- 失败时能否定位到具体层：model/tool/policy/RAG/memory/runtime？
- audit event 是否覆盖 allow、deny、approval、error？
- trace 是否保存版本引用，而不是只保存自然语言摘要？
- 是否能从事故生成 regression case？
- secret 是否可能进入 prompt、trace、audit、eval report？
- SLO 是否区分质量、可靠性、安全、成本和延迟？
- replay packet 是否足够复现同一失败？

## 8. Design-only 过关标准

你应该能复述：

```text
Phase 8 解决的是失败不可定位、事故不可复盘、发布不可回滚。
Trace 用来调试链路，audit 用来证明权限和动作，metric 用来管理 SLO 和错误预算。
一个工业级 Agent 不能只保存聊天记录，必须保存可复现的版本引用、状态引用和审计事件。
```

## 9. 后续 Implementation-later 门禁

后续工程阶段才需要：

- trace coverage 达到 100%。
- policy/tool/memory/retrieval 的 allow、deny、error 都有 audit。
- replay packet 能复现至少一个失败样例。
- SLO 和 error budget 有自动报告。
- 事故能生成 regression case。
- secret scanner 能检查 prompt/log/trace/audit/eval report。

## 10. 参考锚点

- [SLO 与错误预算](../06-工业级框架蓝图/SLO与错误预算.md)
- [事故响应与复盘模板](../06-工业级框架蓝图/事故响应与复盘模板.md)
- [测评审核升级蓝图](../06-工业级框架蓝图/测评审核升级蓝图.md)
- [资料核验记录-2026-07-01](../10-GitHub项目调研/资料核验记录-2026-07-01.md)
- [Langfuse](https://langfuse.com/docs)
- [Phoenix](https://arize.com/docs/phoenix)

## 11. 进入 Phase 9 条件

Design-only 进入条件：

- 你能设计 trace/span 字段表。
- 你能区分 trace、audit、metric、log。
- 你能写出一次事故的 replay packet。
- 你能说明哪些错误预算永远为 0。
- 你能说明下一阶段为什么高风险工具必须进入沙箱和隔离环境。
