# 工业级 Agent 框架总纲

生成日期：2026-06-29  
定位：本项目不是普通 Agent demo，也不是只教 prompt 的课程，而是以工业级 Agent Framework 为目标的教学与工程项目。

## 1. 工业级定义

本项目中的“工业级”必须同时满足：

- **长线运行**：任务可以跨多步、跨中断、跨人工审批继续执行。
- **可恢复**：失败、超时、进程重启、工具错误后可以恢复或安全终止。
- **可审计**：每次模型调用、工具调用、策略决策、记忆读写都有证据。
- **可评测**：最终答案、工具调用、轨迹、记忆、安全、多 Agent 都能被评估。
- **可治理**：Agent、模型、工具、策略、评测集、发布都可版本化和回滚。
- **可隔离**：高风险工具不能裸跑，凭据不能进入 prompt。
- **可演进**：从 mock 到试点再到生产，不推倒重来。

如果缺少其中任意一项，只能称为 demo 或 prototype，不能称为工业级框架。

## 2. 不可妥协能力

| 能力 | 工业级要求 | 不能接受 |
|---|---|---|
| 契约层 | 所有核心输入输出有 schema 和 bad-case tests | `dict[str, Any]` 直接穿透 |
| Runtime | Run/Step/State/Event 显式建模 | 只存 chat history |
| Checkpoint | 支持保存、恢复、重试、取消 | 任务失败后只能重跑 |
| Tool Gateway | 工具调用先校验、授权、审计 | 模型直接执行工具 |
| Policy | 策略基于事实和版本 | 只靠 prompt 承诺 |
| Memory | 写入门禁、召回权限、遗忘、评测 | 所有对话都塞向量库 |
| Eval | golden/red team/trajectory/memory/security 回归 | 只人工看一次回答 |
| Observability | trace/span/audit/replay/cost | 只有普通日志 |
| Sandbox | 高风险工具有隔离等级 | 任意代码直接本机执行 |
| Governance | release gate、rollback、approval | 上线靠手工记忆 |

## 3. 框架核心分层

```text
Application Layer
-> Agent Gateway
-> Agent Runtime
-> Orchestration Layer
-> Model Gateway
-> Tool Gateway
-> Memory Layer
-> Evaluation Layer
-> Observability & Audit Layer
-> Security Isolation Layer
-> Governance Control Plane
```

每层必须有清晰边界，不允许互相偷职责：

- Runtime 不负责权限。
- Tool Gateway 不负责推理。
- Memory 不负责事实真伪最终裁决。
- Eval 不替代安全策略。
- Sandbox 不替代审计。
- Governance 不替代测试。

## 4. 工业级最小闭环

最小闭环不是“模型回答一句话”，而是：

```text
Request
-> Identity/Context
-> AgentManifest
-> Run
-> Step
-> ModelCall
-> ToolCall Candidate
-> Schema Validation
-> Policy Decision
-> Tool Execution
-> Audit Event
-> Trace Span
-> Checkpoint
-> Eval Result
-> Response
```

任何一步缺失，都必须在阶段报告里标成风险。

## 5. MVP-practical 与工业级关系

MVP-practical 不是完整工业级生产系统，但必须采用工业级骨架：

- 单租户，但保留 tenant/workspace 字段。
- mock/file adapter，但保留真实 adapter 接口。
- 本地 trace，但保留 OpenTelemetry 语义。
- 简单 eval，但覆盖 golden/red team/trajectory。
- 简单 policy，但必须可版本化和测试。

这样后续升级不会推倒重来。

## 6. 框架成功标准

一个阶段完成后，不只问“能不能跑”，还要问：

```text
能否恢复？
能否审计？
能否评测？
能否隔离？
能否回滚？
能否解释失败？
能否被下阶段复用？
```

全部能回答，才算工业级方向正确。
