# ADR：S4 使用双 SQLite 模拟外部副作用与本地账本

- 状态：Accepted for teaching baseline
- 日期：2026-07-31

## 决策

使用两个独立 SQLite 数据库：Runtime store 保存 run、checkpoint、audit 和 operation ledger；Mock Refund Provider 保存外部退款结果。Runtime 不能跨库事务提交，故障注入放在 provider 成功与本地 commit 之间。

恢复策略是：未 dispatch 的 approved operation 可执行；已 dispatch 的 operation 必须先按稳定 operation ID 查询 provider；查询结果未知时进入 `needs_reconciliation`，禁止自动 retry。

## 原因

- 双存储真实暴露本地事务无法覆盖外部 API 的边界。
- 不需要云凭据，学习者能稳定重放 crash window。
- provider 记录可独立证明副作用次数，不依赖 Runtime 的内存计数。
- 同一 eval set 可以在未来替换为 Temporal、LangGraph 或真实 provider adapter。

## 未选择

- 单表“调用工具后立即写 result”：无法复现 dual-write ambiguity。
- 只用 retry decorator：会隐藏副作用是否已经发生。
- 声称 exactly-once：本基线只证明同一 provider 幂等合同下的一次业务效果。

## 代价与撤销条件

SQLite 不提供分布式 worker lease、跨区域复制和真实 provider SLA。引入并发 worker、消息 broker 或真实支付 API 时，应增加 lease/fencing、outbox relay、provider idempotency TTL、poll/backoff、补偿与告警；只有新实现通过同一 crash/eval 门禁后才能替换教学 baseline。
