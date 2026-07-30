# S5 测试与评测入口

- Memory store / service：`../../../21-测试/test_memory.py`
- 通用 eval 集成：`../../../21-测试/test_evals.py`
- JSONL runner：`../../../20-源码/agent_course/memory_evals.py`
- Critical eval：`../../../22-评测集/memory-engineering-baseline.jsonl`

至少保留明确偏好、模型猜测、Secret/PII、tenant/resource ACL、TTL、版本冲突、删除 exact/paraphrase/ID、持久化注入、数据库重开、context budget 和未知断言 fail-closed 路径。

```powershell
cd "agent-runtime-gateway\20-源码"
python -m pytest ..\21-测试\test_memory.py ..\21-测试\test_evals.py -q
python -m agent_course.cli memory-eval ..\22-评测集\memory-engineering-baseline.jsonl
python -m agent_course.cli memory-demo --db "$env:TEMP\opspilot-s5-memory.db" --reset
```
