# SLO 与错误预算

生成日期：2026-06-30
更新日期：2026-08-08
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

## 8. S7 可执行基线

课程 S7 使用 `s7-observability-manifest.json` 声明 SLI、阈值、采样和 regression owner，再由真实 Runtime case 生成观测报告。当前门禁至少计算：

- `run_success_rate`：实际终态符合 case 预期的运行比例。
- `p95_latency_ms`：端到端 latency 教学夹具的最近秩分位数。
- `cost_per_success_usd`：总成本除以成功运行数，失败成本不能从分子删除。
- `trace_coverage`：实际 span 数除以应有 root 与 audit-derived span 数。
- `audit_coverage`：期望责任动作在 hash-chained export 中出现的比例。
- `replay_packet_coverage`：版本谱系完整的 replay packet 比例。
- `sensitive_exposures`：导出证据中的 secret/PII pattern 数量。
- `error_budget_burn_rate`：当前错误率除以 `1 - SLO target`。

教学 baseline 使用确定性 latency/token/cost，不是生产 SLO。生产接入必须记录数据源、查询表达式、长短窗口、缺数据行为和告警路由。

## 9. Multi-window burn-rate 起点

参考 Google SRE 的方法，用长窗口确认持续影响、短窗口确认当前仍在燃烧：

| 类型 | 动作 | 课程起点 |
|---|---|---:|
| 快速燃烧 | page、冻结发布、保全 trace/audit | burn rate >= 14.4 |
| 慢速燃烧 | ticket、owner、截止时间 | burn rate >= 3 |
| 单次可恢复错误 | 保留 exemplar，观察窗口 SLI | 不单独 page |

这些数值是教学起点，不是通用生产阈值。真实阈值必须由 SLO window、流量、用户影响和响应能力共同决定。

## 10. 采样管道 SLO

Tail sampling 可根据完整 trace 的错误、延迟和属性保留稀有证据，但是有状态组件。生产接入时至少监测：

- 待决策 trace 数和内存占用。
- 超时、容量溢出和被迫降级次数。
- 错误、高延迟、高风险和新版本 trace 的实际保留率。
- 采样决策延迟、导出失败和每成功任务观测成本。

参考 [OpenTelemetry Sampling](https://opentelemetry.io/docs/concepts/sampling/)。外部 `sampled` flag 不能覆盖内部风险和数据分类策略。
