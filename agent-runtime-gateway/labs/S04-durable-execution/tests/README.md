# S4 测试与评测入口

- Runtime 回归：`../../../21-测试/test_runtime.py`
- Durable failure tests：`../../../21-测试/test_durable.py`
- Eval runner：`../../../21-测试/test_evals.py`
- Critical eval：`../../../22-评测集/s4-durable-baseline.json`

至少保留 provider 前 crash、provider 成功后 crash、provider outcome unknown、payload mismatch、checkpoint version 和 cancel-before-execution 六类路径。

```powershell
python -m pytest ..\21-测试\test_runtime.py ..\21-测试\test_durable.py -q
python -m agent_course.cli eval ..\22-评测集\s4-durable-baseline.json
```
