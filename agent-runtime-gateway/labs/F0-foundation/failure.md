# F0 失败注入

## 失败 1：幂等键没有绑定请求

坏实现：只按 `(tenant_id, idempotency_key)` 查询并返回旧记录。

复现：先用 key `request-1` 创建“VPN 故障”，再用同一 key 创建“删除账号”。若第二次返回第一张工单且没有报错，客户端会把不同业务请求错误合并。

修复：对规范化请求生成 SHA-256 指纹；key 已存在但指纹不同，返回 `IDEMPOTENCY_CONFLICT` / HTTP 409。

回归：`test_foundation_idempotency_key_is_bound_to_request`。

## 失败 2：查询与插入不在事务内

坏实现：先 `SELECT`，释放连接，再 `INSERT`。

复现：8 个线程同时使用同一 key 创建工单。

修复：唯一约束作为最终防线；查询与插入放入 `BEGIN IMMEDIATE` 事务，并对同一 repository 的线程访问加锁。

回归：`test_foundation_concurrent_retries_create_one_ticket`。

## 失败 3：读取只按 ticket id

坏实现：`SELECT * FROM tickets WHERE ticket_id = ?`。

复现：tenant-b 使用 tenant-a 的 ticket id 请求详情。

修复：资源查询必须同时绑定可信 tenant；对不可访问资源返回统一 404，避免存在性侧信道。

回归：`test_foundation_http_contract_and_tenant_isolation`。
