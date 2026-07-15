# S3 证据清单

1. 边界：确定性教学 RAG，不是生产搜索系统。
2. 实现：`rag.py`、`tools.py`、`runtime.py`、`evals.py`。
3. 正常路径：refund policy 命中 `refund-policy-v1`，citation 验证通过。
4. ACL 路径：tenant-b 文档不进入 tenant-a 候选、结果或 audit。
5. Freshness 路径：`refund-policy-v0` 过期后不参与排名。
6. Injection 路径：untrusted document 不提升为指令，不泄漏 `SECRET-DEMO-VALUE`。
7. Citation 路径：篡改 quote 后 validation 返回 false。
8. Eval：`s3-rag-baseline.json` 的 case/assertion/critical 统计。
9. 剩余风险：无 ingestion、embedding、hybrid/rerank、真实模型、索引迁移和线上 trace dashboard。

```powershell
python -m pytest ..\21-测试\test_rag.py ..\21-测试\test_evals.py -q
python -m agent_course.cli eval ..\22-评测集\s3-rag-baseline.json
```
