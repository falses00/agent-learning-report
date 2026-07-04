# SLO 与错误预算

生成日期：2026-06-30  
目标：把“能长期运行”变成可度量、可告警、可冻结发布的指标。

## 1. SLO 分层

| 层级 | 适用阶段 | 目标 |
|---|---|---|
| local-dev | Phase 1-3 | 能本地稳定复现 |
| demo | Phase 3-4 | 能演示端到端链路 |
| prod-lite | Phase 4-9 | 能内部低风险试点 |
| production | Phase 10-11 后 | 能承接真实业务流量 |

## 2. 核心 SLO

| 指标 | demo | prod-lite | production |
|---|---:|---:|---:|
| run_success_rate | >= 90% | >= 95% | >= 99% |
| trace_coverage | 100% | 100% | 100% |
| audit_coverage_tool_policy_memory | 100% | 100% | 100% |
| checkpoint_resume_success | >= 95% | >= 99% | >= 99.5% |
| critical_security_block_rate | 100% | 100% | 100% |
| duplicate_side_effect_rate | 0 critical | 0 critical | 0 critical |
| p95_run_latency | 由场景定义 | 由场景定义 | 由业务 SLO 定义 |
| eval_gate_pass_rate | >= 95% | >= 98% | >= 99% |

## 3. Agent 运行环境 SLO

| 指标 | prod-lite 目标 | 说明 |
|---|---:|---|
| worker_heartbeat_freshness | >= 99% | worker 存活和调度健康 |
| queue_lag_p95 | 场景定义 | 长线任务不能无限堆积 |
| sandbox_start_success_rate | >= 98% | 高风险工具执行环境可用性 |
| sandbox_policy_violation_count | 0 critical | 网络/文件/进程越权 |
| tool_timeout_rate | <= 2% | 工具超时可恢复 |
| approval_sla_met_rate | >= 95% | HITL 不成为黑洞 |
| trace_missing_rate | 0 | 任一缺失都阻塞发布 |
| audit_writer_error_rate | 0 critical | 审计失败不能静默 |
| eval_regression_backlog_age | <= 7 days | 失败样本及时回流 |

## 4. 错误预算

错误预算不是允许安全事故发生。以下事件预算永远为 0：

- secret 泄漏。
- critical 越权写操作执行。
- 跨租户记忆泄漏。
- audit event 缺失。
- 重复副作用。

可使用错误预算的事件：

- 模型超时。
- 可恢复工具失败。
- 非 critical 答案质量退化。
- fallback 触发。
- false refusal。

## 5. 发布冻结规则

出现以下情况，冻结发布：

- critical security case 失败。
- trace coverage 低于 100%。
- audit coverage 低于 100%。
- checkpoint resume 测试失败。
- golden eval 连续两次下降超过阈值。
- red team 新增失败未修复。
- 事故复盘未生成 regression case。

## 6. 告警等级

| 等级 | 示例 | 处理 |
|---|---|---|
| P0 | secret 泄漏、越权写执行、跨租户泄漏 | 立即停用相关 Agent/工具 |
| P1 | audit 缺失、resume 大面积失败、评测门禁失效 | 冻结发布，修复后复测 |
| P2 | 模型超时升高、成本超预算、false refusal 升高 | 降级、限流、调参 |
| P3 | 文档/指标缺口 | 排入改进计划 |

## 7. 错误预算复盘

每次消耗错误预算都要记录：

```text
事件：
影响：
触发指标：
根因：
检测方式：
恢复动作：
是否加入 regression：
是否修改门禁：
```
