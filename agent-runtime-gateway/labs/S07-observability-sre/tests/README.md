# S07 测试说明

`test_observability.py` 覆盖：

- 6-case baseline、36 条断言与三类覆盖率。
- W3C trace context 和 metadata-only export。
- secret canary 不进入证据。
- 缺 span、audit 篡改和 replay lineage 缺失。
- P95、cost/success 与 error budget blocker。
- evidence hash 缺失、未知 manifest 字段和路径逃逸。
- 外部 sampled flag 不覆盖内部策略。
- 14-case adversarial suite 完整通过。

运行：

```powershell
cd "agent-runtime-gateway\20-源码"
python -m pytest ..\21-测试\test_observability.py -q
```
