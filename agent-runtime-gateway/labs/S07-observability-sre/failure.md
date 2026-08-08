# S07 故障注入与排查

## 排查顺序

```text
用户影响
-> root span 与 terminal outcome
-> trace context / coverage
-> policy / tool / retrieval child spans
-> audit coverage / hash chain
-> SLI / SLO / burn rate
-> replay lineage
-> alert / incident / regression
```

## 故障矩阵

| 故障 | 症状 | 正确 blocker | 修复 |
|---|---|---|---|
| child span 被删除 | root duration 无法分解 | `TRACE_COVERAGE_GAP` | 补 instrumentation 和 coverage test |
| trace-id 损坏 | 跨组件无法关联 | `TRACE_CONTEXT_INVALID` | 入口生成内部 context，逐跳透传 |
| 审批 audit 缺失 | 高风险动作无责任证据 | `AUDIT_COVERAGE_GAP` | allow/deny/error/approval 同步审计 |
| audit event 被修改 | chain 验证失败 | `AUDIT_CHAIN_INVALID` | 保全原始证据，调查写入和导出路径 |
| prompt 写入 span | export 出现 canary | `SENSITIVE_TELEMETRY_DETECTED` | metadata-only、过滤、截断、轮换 secret |
| P95 = 5000ms | 端到端 SLO 失败 | `P95_LATENCY_SLO_BREACH` | 定位尾部 span、降级或回滚 |
| 一次关键运行失败 | 99% 预算快速燃烧 | `ERROR_BUDGET_FAST_BURN` | page、冻结发布、修复后重放 |
| replay 缺 policy version | 同一事故无法重建 | `REPLAY_PACKET_INCOMPLETE` | 补全版本谱系并重新封存证据 |

## 最小回归命令

```powershell
python -m pytest ..\21-测试\test_observability.py -q
python -m agent_course.cli observability-eval ..\22-评测集\s7-observability-adversarial.json
```

修复不能只让 blocker 消失，还必须证明对应 attack case 仍然存在并通过。
