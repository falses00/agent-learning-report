# ADR：S5 使用 canonical SQLite record 与独立派生索引

- 状态：Accepted for teaching baseline
- 日期：2026-07-31

## 决策

使用 SQLite 保存 `memory_records`、`memory_index`、`memory_tombstones` 和 `memory_audit`。应用边界必须传入受信 `MemoryAccessPolicy`，由服务端成员关系、tenant admin 和 resource grants 构造。所有写入先经过确定性 `MemoryService`；检索先做 tenant/principal/resource、TTL 和 deleted 硬过滤，再做简单相关性和 context budget。模型推断、Secret/PII、untrusted content 和未验证 procedural memory 默认拒绝。

## 原因

- 主记录与派生索引分表，能真实测试“删主表但忘记删索引”的事故。
- 文件 SQLite 能验证关闭、重开后状态仍在，不依赖内存 fixture。
- 确定性时钟和检索让安全边界可重复回归，不受模型和外部服务波动影响。
- 同一 JSONL eval 可以在未来替换 vector/graph adapter，而不改变治理断言。

## 未选择

- 把全部聊天记录写入单一向量库：无法清楚表达来源、版本、TTL 和资源授权。
- 只在 prompt 中要求模型“不要记敏感内容”：不是可信执行边界。
- 引入真实云向量库或图数据库：会把课程重点转移到凭据、网络和厂商差异。
- 把 SQLite 基线宣传为生产 memory platform：当前没有分布式一致性、加密、备份擦除和合规留存。

## 代价与替换门禁

当前 lexical baseline 不能证明真实认证、语义召回、多跳关系或大规模性能。引入 auth/vector/graph/product adapter 时，必须保留 canonical record ID、provenance、受信 ACL hard filter、validity、tombstone 和 audit 契约；并通过同一 18 条基线，再增加索引迁移、删除传播、并发更新、备份与恢复、延迟/成本和真实数据分布评测，才能替换教学 baseline。
