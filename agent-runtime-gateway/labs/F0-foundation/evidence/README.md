# F0 证据清单

只记录脱敏摘要、仓库路径和可重放命令，不粘贴 token、PII 或真实客户数据。

1. 边界：本实验负责和不负责什么。
2. 实现：commit、`foundation.py`、`api.py`、`test_foundation.py`。
3. 正常路径：首次 POST 返回 201；同请求重放返回 200 和 `Idempotency-Replayed: true`。
4. 失败路径：同 key 不同请求返回 409；额外字段返回 422；跨租户读取返回 404。
5. 并发路径：8 路并发只生成一个 ticket id。
6. 命令：`python -m pytest ..\21-测试\test_foundation.py -q`。
7. 剩余风险：SQLite、进程内锁、无真实认证、无外部副作用 reconciliation。

工程认证必须由测试或 CI 重新生成这些结果；浏览器中的本地记录仍只是 self-reported。
