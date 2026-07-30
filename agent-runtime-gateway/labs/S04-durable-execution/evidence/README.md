# S4 证据清单

1. 边界：确定性双 SQLite 教学基线，不是生产 workflow/payment 系统。
2. 实现：`durability.py`、`store.py`、`runtime.py`、`tools.py`、`evals.py`。
3. 正常路径：批准、执行、本地 committed，一次 provider side effect。
4. Crash-before 路径：approved checkpoint 恢复后执行一次。
5. Crash-after 路径：dispatching checkpoint 先查询 provider，再补记本地结果。
6. Ambiguous 路径：查询不可用时 `needs_reconciliation`、`retryable=false`，副作用计数不增加。
7. Idempotency 路径：同 operation ID 不同 payload 被拒绝。
8. Checkpoint 路径：schema version、parent、reason、state hash 可复核。
9. Eval：`s4-durable-baseline.json` 的 case/assertion/critical 统计。
10. 剩余风险：无多 worker lease、outbox relay、真实 provider 合同、审批 TTL/身份认证、补偿 SLA 和跨区域容灾。

```powershell
python -m agent_course.cli durable-demo --work-dir "$env:TEMP\opspilot-s4" --reset
python -m pytest ..\21-测试\test_runtime.py ..\21-测试\test_durable.py -q
python -m agent_course.cli eval ..\22-评测集\s4-durable-baseline.json
```
