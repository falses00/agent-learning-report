# S5 证据清单

1. 边界：确定性单进程 SQLite 教学基线，不是生产 memory service。
2. 契约：candidate、record、decision、source、scope、sensitivity、type、TTL、version、tombstone。
3. 写入：明确偏好允许；模型推断、Secret/PII、untrusted instruction 拒绝。
4. 隔离：受信 membership/admin/resource grants 在相关性计算前硬过滤；伪造 tenant 与自授 subject 被回归覆盖。
5. 时间：TTL 到期结束 validity 并删除派生索引。
6. 纠错：新版本 supersede 旧版本，当前查询与历史解释都成立。
7. 删除：subject 的 raw version chain 被硬删除，目标 exact、paraphrase、ID 不可召回，最小 tombstone 与 audit 保留。
8. 预算：完整记录进入 context；超预算整条跳过，不截断事实。
9. 持久化：关闭并重开文件 SQLite 后记录与治理语义不变。
10. Eval：18 个独立 case、全部 assertions、`critical_failed=0`。
11. Failure path：未知字段与未知 assertion fail closed；重复 demo 不覆盖数据库。
12. 剩余风险：无真实身份认证 adapter、embedding/graph、大规模并发、KMS/加密、备份擦除、法务留存、跨区域复制与生产 SLO。

```powershell
cd "agent-runtime-gateway\20-源码"
python -m pytest ..\21-测试\test_memory.py -q
python -m agent_course.cli memory-eval ..\22-评测集\memory-engineering-baseline.jsonl
python -m agent_course.cli memory-demo --db "$env:TEMP\opspilot-s5-memory.db" --reset
```
