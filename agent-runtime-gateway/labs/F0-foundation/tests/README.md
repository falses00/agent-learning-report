# F0 测试入口

权威测试位于 `../../../21-测试/test_foundation.py`，覆盖正常重放、请求冲突、并发重试、HTTP 严格字段、跨租户读取和 CLI 往返。

```powershell
cd "agent-runtime-gateway\20-源码"
python -m pytest ..\21-测试\test_foundation.py -q
```
