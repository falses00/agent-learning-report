# ADR：F0 使用 Domain Service + SQLite + FastAPI

- 状态：Accepted for teaching baseline
- 日期：2026-07-15

## 决策

业务规则放在 `TicketService` 与 `TicketRepository`；FastAPI 只负责 HTTP 契约和状态码；SQLite 用于可重放的本地事务实验。

## 备选方案

- 路由函数直接写 SQL：文件更少，但无法分离 HTTP、领域和持久化失败。
- 一开始使用 PostgreSQL/Redis：更接近生产，但增加安装和环境噪声，掩盖 F0 核心概念。
- 手写 `http.server`：依赖更少，但不符合后续 Pydantic 严格契约主线。

## 代价与撤销条件

SQLite + 进程内锁不能证明多进程或分布式 exactly-once。进入生产部署前，必须迁移到支持目标并发模型的数据库，并重新运行并发、故障恢复与 migration 测试。
