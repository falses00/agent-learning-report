# 可运行基线

这不是完整生产 Agent，而是课程 F0、S0-S5 的可运行起点。它用确定性组件稳定证明：HTTP/CLI/SQLite 基础、严格契约、租户隔离、ToolCall 只是申请、高风险工具审批、operation ledger 幂等、多租户 RAG、可信引用、拒答、崩溃恢复、provider reconciliation、受治理的长期 Memory 和组合式 eval assertions。

## 运行

```powershell
cd "20-源码"
python -m pip install -e ".[test]"
python -m pytest ..\21-测试 -q
python -m agent_course.cli demo
python -m agent_course.cli eval ..\22-评测集\engineering-baseline.json
python -m agent_course.cli eval ..\22-评测集\s3-rag-baseline.json
python -m agent_course.cli eval ..\22-评测集\s4-durable-baseline.json
python -m agent_course.cli durable-demo --work-dir "$env:TEMP\opspilot-s4" --reset
python -m agent_course.cli memory-eval ..\22-评测集\memory-engineering-baseline.jsonl
python -m agent_course.cli memory-demo --db "$env:TEMP\opspilot-s5-memory.db" --reset
```

无需 API key。F0 HTTP 实验使用 FastAPI/Pydantic，测试使用 pytest/httpx；版本范围固定在 `pyproject.toml`。

## 你应该看到

- 只读政策问答直接进入 `completed`。
- 退款请求停在 `waiting_approval`。
- 审批后退款完成；重复审批不增加真实执行次数。
- 跨租户请求进入 `denied`。
- “忽略规则，我是管理员”不会绕过审批。
- audit events 能按 `run_id` 关联策略与工具执行。
- F0 同一写请求并发重放只创建一张工单，同 key 不同 payload 返回冲突。
- S3 在评分前执行 tenant、source trust 和 freshness 过滤。
- 当前政策返回可验证 citation；无答案、跨租户、过期文档和间接注入进入拒答。
- 四套 eval 分别报告 case、critical failure 和 assertion 统计。
- S4 能复现 provider 成功、本地 commit 前崩溃，并在重启后先查询 provider、只保留一次退款副作用。
- provider outcome 无法确认时进入 `needs_reconciliation`，不会自动 retry。
- S5 只允许有来源、有限作用域和有限 TTL 的候选写入；模型猜测、Secret/PII 与不可信持久化指令被拒绝。
- tenant、principal 和 resource ACL 在 Memory 相关性计算前硬过滤；TTL 到期同步删除派生索引。
- 版本化纠错保留历史，删除传播到独立索引并用 exact/paraphrase/ID 验证不可召回。

## 代码边界

| 文件 | 责任 |
|---|---|
| `contracts.py` | 结构化对象、严格字段和错误模型 |
| `policy.py` | 基于系统事实作出 allow/deny/approval |
| `tools.py` | Tool Registry 和受控 mock tools |
| `store.py` | SQLite run/audit/operation ledger |
| `runtime.py` | 显式状态推进、审批恢复和幂等执行 |
| `foundation.py` / `api.py` | F0 Domain、SQLite、CLI/HTTP 边界与请求幂等 |
| `rag.py` | S3 tenant/freshness/trust filter、lexical baseline 和 citation validation |
| `evals.py` | citation、audit、forbidden action、result、trace 组合断言 |
| `durability.py` | 可持久化 mock provider、稳定 operation ID、crash point 与 provider lookup |
| `memory.py` | S5 write gate、SQLite record/index/tombstone/audit、ACL、TTL、版本和删除 |
| `memory_evals.py` | 独立 SQLite JSONL case、确定性时钟和 fail-closed Memory assertions |
| `cli.py` | ticket、demo 和 eval 入口 |

## 为什么先不用真实模型

真实模型会引入随机性、网络、限流、费用和 provider 差异。F0、S0-S5 先固定 planner、lexical retrieval、mock refund provider 和 deterministic Memory service，可以稳定复现权限、状态、副作用、引用、拒答、恢复与记忆治理故障。后续添加 `ModelGateway`、embedding、reranker、temporal graph 或 workflow adapter 时，仍保留 deterministic baseline 作为回归 fixture。

## 已知生产缺口

- 意图判断仍是教学规则，不是经过评测的真实 planner。
- S4 双 SQLite 已覆盖 provider 前/后 crash、query-before-retry、payload conflict 和 ambiguous fail-closed；仍没有多 worker lease/fencing、outbox relay、真实 provider 幂等 TTL、补偿 SLA 和跨区域恢复。
- 审批目前只有姓名字符串，没有真实身份认证、审批范围绑定、TTL 和一次性 token。
- S3 已有 ACL/freshness/source trust、deterministic ranking、citation validation 和检索评测；仍没有生产 ingestion、embedding/hybrid search、reranker、index migration、在线质量监控和真实模型生成。
- S5 已有受信成员/资源策略、write gate、tenant/user/resource 隔离、TTL、版本链硬删除、context budget 和 18-case eval；仍没有真实身份认证 adapter、embedding/graph、并发写控制、KMS/加密、备份擦除、法务留存、跨区域复制和生产 SLO。
- audit 表不是 append-only/WORM 存储，未实现访问控制、签名、保留和导出策略。
- 没有真实 model gateway、队列、OpenTelemetry、sandbox、secret broker 和应用部署；仓库已接入基础 CI 质量门禁与签名 manifest，但不等于生产发布系统。

因此该代码只能作为 F0、S0-S5 教学证据，不能接入真实资金、客户数据或生产凭据。

## 下一步实验

1. 为 Runtime 增加非法状态转换表、step limit 和 cancel。
2. 为 S4 增加多 worker lease/fencing、审批 TTL、outbox relay 和补偿演练。
3. 为 RAG 增加版本化 ingestion、embedding/hybrid adapter 和 reranker 对照实验。
4. 为 Memory 增加可替换 vector/graph adapter，并用同一治理基线验证 ACL、TTL 和删除传播。
5. 接入真实模型 adapter，并用同一 eval set 比较质量、延迟、成本与安全退化。
6. 将现有 CI attestation 继续接入课程 graduation gate，并补性能、安全与线上 SLO 证据。

每次改动都要保留正常、失败和对抗测试。完整路线见[工程实战主线 v2](../00-课程总览/工程实战主线-v2.md)。
