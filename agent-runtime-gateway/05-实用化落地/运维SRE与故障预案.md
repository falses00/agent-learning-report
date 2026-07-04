# 运维 SRE 与故障预案

生成日期：2026-06-29  
目标：让 MVP-practical 失败时能定位、恢复、回滚。

## 0. 与工业级蓝图的关系

本文件是落地执行手册，工业级标准以这些文件为准：

- `H:\Creat A Agent\agent-runtime-gateway\06-工业级框架蓝图\SLO与错误预算.md`
- `H:\Creat A Agent\agent-runtime-gateway\06-工业级框架蓝图\故障模式与恢复矩阵.md`
- `H:\Creat A Agent\agent-runtime-gateway\06-工业级框架蓝图\运行时状态机与恢复语义.md`
- `H:\Creat A Agent\agent-runtime-gateway\06-工业级框架蓝图\事故响应与复盘模板.md`

SRE 文档不能只写“怎么处理故障”，还必须能回答：故障是否消耗错误预算、是否阻塞发布、是否需要事故复盘。

## 1. 必须监控的问题

- 服务启动失败。
- 模型调用超时。
- 工具调用失败。
- policy 误拒或漏拒。
- checkpoint 损坏。
- checkpoint 写入失败。
- resume 后重复副作用。
- eval 退化。
- 成本超限。
- trace 缺失。
- audit 缺失。
- memory leakage 或污染。
- sandbox egress/resource violation。

## 2. 最小指标

| 指标 | 用途 |
|---|---|
| request_count | 请求量 |
| run_success_rate | 成功率 |
| run_failure_rate | 失败率 |
| run_recovery_success_rate | 中断恢复成功率 |
| checkpoint_write_failure_rate | checkpoint 写入失败率 |
| p95_latency | 延迟 |
| tool_error_rate | 工具错误率 |
| policy_deny_rate | 策略拒绝率 |
| audit_gap_count | audit 缺失数量 |
| eval_pass_rate | 评测通过率 |
| cost_per_run | 单次任务成本 |
| approval_sla_miss_rate | 人工审批超时率 |
| memory_leakage_incidents | 记忆泄漏事件数 |
| sandbox_violation_count | 沙箱违规次数 |
| error_budget_burn_rate | 错误预算燃烧速度 |

## 2.1 SLO 最低线

| 能力 | MVP-practical 最低线 | 生产候选最低线 |
|---|---:|---:|
| Run trace 覆盖率 | 100% | 100% |
| Tool audit 覆盖率 | 100% | 100% |
| Checkpoint resume 成功率 | >= 95% | >= 99% |
| Critical security block rate | 100% | 100% |
| P95 gateway overhead | < 1000ms | < 500ms |
| 发布回滚演练 | 手工可执行 | 自动化脚本 + 演练记录 |

## 3. Runbook

### 模型超时

检查：

- provider 状态。
- timeout 配置。
- fallback 是否启用。
- trace 中 model span。

处理：

- 重试。
- fallback。
- 降低 step 上限。
- 标记 run 为 recoverable。

### 工具失败

检查：

- tool schema。
- adapter 状态。
- 凭据是否存在。
- policy 是否拒绝。

处理：

- 返回结构化错误。
- 记录 audit。
- 如果 recoverable，允许 resume。

### checkpoint 损坏或恢复失败

检查：

- 最近可信 checkpoint。
- checkpoint state_hash 是否匹配。
- operation_id 是否已经提交副作用。
- migration version 是否改变状态结构。
- memory/artifact 引用是否仍可读。

处理：

- 停止自动 resume。
- 从上一可信 checkpoint fork 一个恢复 Run。
- 对已完成 operation_id 做幂等检查。
- 生成事故记录，补充 recovery regression case。

### trace 或 audit 缺失

检查：

- gateway 是否生成 trace_id。
- runtime、tool gateway、policy gateway 是否透传 trace_id。
- audit writer 是否失败。
- 是否存在绕过 gateway 的路径。

处理：

- 禁止发布同类变更。
- 暂停高风险工具。
- 修复后补一条 trace/audit coverage test。

### 评测失败

检查：

- prompt/model/tool/policy 是否变更。
- 失败 case 是否稳定。
- trace 是否显示重复工具或错误记忆。

处理：

- 阻止发布。
- 生成 regression case。
- 修复后重跑。

## 4. 告警最低线

内部试点至少告警：

- critical 安全用例未拦截。
- audit event 缺失。
- trace 缺失。
- eval pass rate 低于门槛。
- 成本超过预算。
- 连续工具失败。
- checkpoint resume 连续失败。
- error budget burn rate 超过阈值。
- memory leakage、sandbox violation、secret exposure。

## 5. 回滚原则

任何发布都必须知道：

- 回滚到哪个 Agent version。
- 回滚到哪个 prompt/model/tool/policy/eval set。
- 如何禁用某个工具。
- 如何暂停某个 Agent。
- 如何导出事故 trace。

## 6. 事故分级与复盘

| 等级 | 示例 | 必须动作 |
|---|---|---|
| P0 | secret 泄漏、越权写入、跨租户数据泄漏 | 立即停用相关 Agent/工具，事故复盘，禁止发布 |
| P1 | critical redteam 漏拦、重复副作用、checkpoint 大面积损坏 | 回滚或暂停放量，补回归用例 |
| P2 | eval 明显退化、成本异常、审批 SLA 失效 | 冻结相关变更，修复后重跑门禁 |
| P3 | 单点工具超时、非核心日志缺失 | 进入普通修复队列 |

复盘使用：`H:\Creat A Agent\agent-runtime-gateway\06-工业级框架蓝图\事故响应与复盘模板.md`。

## 7. 必须演练

进入内部试点前至少演练：

- kill runtime 后 resume。
- 工具写操作重试不重复执行。
- 关闭某个 MCP server 后降级。
- critical redteam case 阻断发布。
- 发布失败后回滚 agent/prompt/tool/policy/eval set 组合。
