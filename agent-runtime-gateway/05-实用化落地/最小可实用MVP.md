# 最小可实用 MVP

生成日期：2026-06-29  
目标：定义第一个能从教学 demo 走向内部试点的最小应用版本。

## 1. MVP 名称

**工单处理 Agent Runtime Gateway MVP**

## 2. 用户故事

```text
作为企业内部支持团队成员，
我希望 Agent 能读取工单和知识库，
给出分类、优先级、建议回复和建议动作，
并在需要调用工具时经过权限和审计，
这样我可以更快处理低风险重复工单。
```

## 3. 最小功能范围

| 模块 | MVP 功能 | 不包含 |
|---|---|---|
| Agent Manifest | 定义工单 Agent 的 owner、version、model policy、tools、eval set | 可视化编辑器 |
| Minimal Runtime | Run/Step/State、mock model 或可替换 model client | 分布式调度 |
| Request Gateway | 生成 request_id、thread_id、trace_id、principal | 复杂 API gateway 集群 |
| Tool Gateway | 只读工具、schema 校验、policy 判断、audit event | 自动执行高风险写操作 |
| Knowledge Tool | mock 知识库查询或本地只读知识库 | 真实企业敏感数据 |
| Memory v0 | session memory、有限长期偏好、写入门禁 | 自动无限长期记忆 |
| Eval v0 | 20-50 条 golden tasks，10-20 条 red team tasks | 大规模评测平台 |
| Observability v0 | structured logs、trace JSON、简单 replay | 完整 dashboard |
| Security v0 | tool allowlist、deny dangerous action、secret 不进 prompt | 完整沙箱 |

## 3.1 工业级最小骨架

MVP 可以功能少，但骨架必须真实：

| 骨架 | 必须有 |
|---|---|
| 长线任务 | `Run`、`Step`、`State`、`Checkpoint` |
| 工具治理 | `ToolCall`、schema validation、policy decision、audit event |
| 审计复盘 | `trace_id`、span、structured log、replay command |
| 可靠执行 | `operation_id`、retry、timeout、recoverable/terminal error |
| 测评审核 | smoke、golden、red team、trajectory eval |
| 发布门禁 | eval pass、trace coverage、audit coverage、rollback |

## 4. 最小数据对象

必须先实现或定义：

- `AgentManifest`
- `Run`
- `Step`
- `ToolCall`
- `PolicyDecisionInput`
- `PolicyDecision`
- `AuditEvent`
- `ErrorModel`
- `MemoryRecord`
- `EvalCase`
- `EvalResult`

## 5. 最小端到端链路

```text
User Ticket
-> Request Gateway
-> Agent Runtime
-> ToolCall candidate
-> Tool Gateway
-> Policy Decision
-> Read-only Knowledge Tool
-> Agent Response
-> Audit Event
-> Eval Result
```

## 6. MVP 验收标准

必须通过：

- 正常工单分类和建议回复。
- 只读知识库工具调用成功。
- 写操作工具调用被拒绝或进入审批。
- prompt injection 不得绕过工具策略。
- 缺字段/错类型 ToolCall 被 schema 拒绝。
- 每次 run 都能通过 trace_id 找到步骤。
- 每次工具调用都有 audit event。
- 评测集变更可复跑。
- 至少一个任务中断后能恢复或给出可解释失败。

## 7. MVP 不算生产可用的地方

这个 MVP 可以内部试点，但不能直接承诺生产可用，因为它还缺：

- 完整 IAM/OIDC 集成。
- 完整 sandbox。
- 完整多租户隔离。
- SLO、告警、扩缩容。
- 数据备份和恢复演练。
- 完整 UI console。
- 合规审计流程。

## 8. 内部试点条件

可以进入内部试点前，必须满足：

- 只接低风险只读数据。
- 不连接生产写工具。
- 所有工具调用可审计。
- 所有用户知道 Agent 建议需要人类复核。
- 出错时可以回放 trace。
- 评测报告连续通过。

## 9. 成功指标

| 指标 | 试点目标 |
|---|---:|
| 工单分类准确率 | >= 85% |
| 建议回复可用率 | >= 80% |
| ToolCall schema pass rate | >= 99% |
| 越权工具拦截率 | 100% critical cases |
| Trace 覆盖率 | 100% run |
| Audit event 覆盖率 | 100% tool call |
| 评测回归通过率 | >= 95% |
| 人工节省时间 | 试点后再量化 |

这些目标是试点目标，不是最终生产 SLO。
