# S4 实验：崩溃恢复与副作用对账

一句话定义：Durable Execution 把可恢复业务状态持久化，并在重放外部副作用前用稳定 `operation_id` 查询既有结果；无法确认结果时暂停对账，而不是盲目重试。

## 1. 先看责任边界

本实验围绕同一个 OpsPilot 退款流程实现：

```text
waiting_approval
  -> 原子保存 approval + operation intent + checkpoint
  -> dispatching
  -> provider 已成功 / 本地尚未 commit 时崩溃
  -> restart
  -> query provider by operation_id
  -> committed 或 needs_reconciliation
```

实现位于：

- `../../20-源码/agent_course/durability.py`
- `../../20-源码/agent_course/store.py`
- `../../20-源码/agent_course/runtime.py`
- `../../20-源码/agent_course/tools.py`
- `../../20-源码/agent_course/evals.py`
- `../../21-测试/test_durable.py`
- `../../22-评测集/s4-durable-baseline.json`

这是确定性的单进程/SQLite 教学基线。它证明 crash window、provider reconciliation、checkpoint 版本和 fail-closed 语义；不声称已经具备分布式调度、worker lease、真实支付 SLA、跨区域容灾、审批身份认证或全局 exactly-once。

## 2. 六个关键概念

| 概念 | 原理 | 缺少时的事故 | 本实验如何验收 |
|---|---|---|---|
| Checkpoint | 保存业务状态、待办动作、批准事实和副作用引用 | 进程重启后只能重头运行 | SQLite 中形成带版本、父节点和 state hash 的 checkpoint 链 |
| Stable operation ID | 同一业务意图在所有重试中使用同一身份 | 每次恢复都变成一笔新退款 | `run_id:refund` 同 payload 重放只保留一条 provider 记录 |
| Operation ledger | 区分 approved、dispatching、ambiguous、committed | 本地“没结果”被误判为“没执行” | crash 后 ledger 保留状态和 attempt，而不是只有成功结果 |
| Query-before-retry | 对已 dispatch 的写操作先查 provider | 外部成功、响应丢失后重复副作用 | provider 已有结果时补记本地，不再次执行 |
| Error taxonomy | recoverable 不等于可原样 retry；ambiguous 必须对账 | 所有异常都套同一个指数退避 | 查询不可用时进入 `needs_reconciliation`，`retryable=false` |
| Durable approval | 批准决定与 operation intent 一起持久化 | 重启后重复审批或绕过审批 | resume 只能继续已批准 operation；等待态可安全取消 |

数据库事务只能原子提交本地记录，不能回滚已经发生的外部退款。Durable framework 也只能恢复控制流；业务正确性仍依赖下游幂等合同、可查询状态和人工对账路径。

## 3. 先复现失败

阅读[失败注入](failure.md)，重点观察这个窗口：

```text
provider.execute(operation_id) -> success
                         [CRASH]
local operations.status -> still dispatching
```

运行可复现实验：

```powershell
cd "agent-runtime-gateway\20-源码"
python -m agent_course.cli durable-demo --work-dir "$env:TEMP\opspilot-s4" --reset
```

预期证据：

- `before_resume.run.status == "executing"`。
- `before_resume.operation.status == "dispatching"`。
- 恢复后的 audit 包含 `PROVIDER_RESULT_RECONCILED`。
- `after_resume.operation.status == "committed"`。
- crash 前后 `provider_execution_count` 都是 `1`。

## 4. 三类验证

```powershell
python -m pytest ..\21-测试\test_runtime.py ..\21-测试\test_durable.py -q
python -m agent_course.cli eval ..\22-评测集\s4-durable-baseline.json
```

| 类型 | 场景 | 必须看到 |
|---|---|---|
| 正常 | 批准后直接执行 | committed、一次副作用、结构化 audit |
| 失败 | provider 前 crash；provider 成功后 crash | 从 approved 或 dispatching checkpoint 恢复 |
| 对抗 | provider 查询不可用；同 key 换 payload；未知 checkpoint 版本 | 暂停对账、参数冲突、版本拒绝，不盲重试 |

S4 eval 当前包含 3 个 critical case、21 条断言；每个 case 使用独立临时目录，并在 crash 后关闭、重开 runtime 与 provider 两个 SQLite 文件。任一重复退款、ambiguous 自动 retry、checkpoint 不兼容仍继续执行，都必须阻塞发布。

## 5. 常见易错点与修复

| 易错点 | 为什么错 | 修复与回归 |
|---|---|---|
| “有 checkpoint 就是 exactly-once” | checkpoint 可能没记录外部成功 | provider 幂等键 + query-before-retry |
| 客户端 timeout 直接 retry | timeout 代表结果未知 | 先查 operation/provider，再决定 retry |
| 同 operation ID 接受不同参数 | 会把另一笔业务意图当作重放 | 保存参数 hash，不一致立即冲突 |
| 把 secret、连接和完整思维链存入 checkpoint | 泄漏且无法稳定反序列化 | 只存最小业务状态与外部引用 |
| 查询失败时把状态改回 approved | 抹掉已经 dispatch 的事实 | 保留 ambiguous 并暂停自动执行 |
| 让模型决定是否再退款 | 模型不是副作用账本或权限事实源 | 恢复策略只读取可信 runtime/provider 状态 |

## 6. 五道自测

1. 外部退款成功、本地 ledger 未提交时，为什么 `retryable=false` 但 `recoverable=true`？
2. crash 在 provider 调用前与调用后，恢复算法为什么不同？
3. operation ID 相同但 amount 不同，为什么必须失败而不是返回旧结果？
4. checkpoint 应保存哪些最小事实，哪些内容绝不能保存？
5. Temporal、LangGraph 或 Agents SDK 的持久化为什么不能替代业务 provider reconciliation？

答错时先指出误区属于状态、边界、可靠性还是权限，再重跑对应 `test_durable.py` case，并新增一个能让错误实现稳定失败的 regression。

## 7. 一页速记清单

```text
一句话：恢复控制流之前，先恢复副作用事实。
负责层：Runtime + operation ledger + provider adapter。
核心契约：run_id、checkpoint_id、operation_id、args_hash、status、provider_reference。
最危险失败：provider success -> response lost -> local commit missing。
恢复顺序：load checkpoint -> inspect ledger -> query provider -> commit/retry/pause。
自动 retry 条件：确认未执行，并使用同一幂等键。
必须暂停：provider outcome unknown、checkpoint version unknown、payload mismatch。
证据：checkpoint chain、operation attempts、provider count、audit、critical eval。
仍未证明：多 worker lease、真实 provider 合同、跨区域容灾、补偿 SLA。
```

## 8. 通过与预习门禁

- [ ] CLI 能稳定复现 provider 成功、本地未提交的 crash。
- [ ] provider 前后 crash 都有测试。
- [ ] provider 成功后的恢复不会增加副作用计数。
- [ ] 查询不可用时状态停在 `needs_reconciliation`。
- [ ] checkpoint 版本和 state hash 都被校验。
- [ ] 等待审批可取消；已 dispatch 或 ambiguous 状态不能伪装成安全取消。
- [ ] S4 eval `critical_failed=0`，证据按[清单](evidence/README.md)登记。

岗位映射：可靠 Agent Runtime、支付/工单副作用治理、HITL、幂等 API、故障注入、恢复策略、事故答辩。

下一阶段预习：区分工作上下文、checkpoint 和长期 Memory；准备一条错误事实、PII 和跨租户记忆候选。

## 9. 一手资料与未来走向

- [Temporal Error handling](https://docs.temporal.io/best-practices/error-handling)：Activity 会因失败重试，副作用必须具备幂等与错误分类。
- [LangGraph Functional API](https://docs.langchain.com/oss/python/langgraph/functional-api)：恢复会重放入口逻辑，副作用应放在 task 中并保持幂等。
- [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)：HITL 恢复会从节点开头重跑，interrupt 前副作用必须可重放。
- [OpenAI Agents SDK HITL](https://openai.github.io/openai-agents-python/human_in_the_loop/)：`RunState` 可序列化批准状态并恢复原顶层 run。
- [AWS EC2 idempotency](https://docs.aws.amazon.com/ec2/latest/devguide/ec2-api-idempotency.html)：同 client token、同参数安全重放；参数变化必须冲突。

未来的 durable agent 会更多采用标准化 run state、托管 checkpoint、可恢复 approval 和 workflow history，但下游 API 的幂等 TTL、query 能力、参数匹配和补偿语义仍然必须逐工具声明并评测。框架能减少调度工作，不能替业务承诺“全局 exactly-once”。
