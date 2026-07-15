# F0 工程基础实验：可安全重试的工单服务

一句话定义：用严格 HTTP 契约、SQLite 事务和请求指纹，把一个写请求变成可测试、可隔离、可安全重放的后端服务。

## 1. 本阶段交付

你要交付同一个 OpsPilot 工单服务的三种入口：

- Domain：`TicketService`，不依赖 Web 框架。
- HTTP：FastAPI `POST /tickets`、`GET /tickets`、`GET /tickets/{id}`。
- CLI：`python -m agent_course.cli ticket ...`。

实现位于：

- `../../20-源码/agent_course/foundation.py`
- `../../20-源码/agent_course/api.py`
- `../../20-源码/agent_course/cli.py`
- `../../21-测试/test_foundation.py`

## 2. 四个关键概念

| 概念 | 白话解释 | 缺少时的事故 | 验收证据 |
|---|---|---|---|
| 请求指纹 | 幂等键还要绑定原始请求内容 | 同一 key 被不同写请求复用，返回错误旧结果 | 同 key 同 payload 重放；同 key 不同 payload 返回 409 |
| 事务边界 | 查旧记录和插入新记录必须在同一受控区间 | 并发重试创建两张工单 | 8 路并发只出现一个 ticket id |
| 租户作用域 | 每次读写都带可信 tenant 条件 | tenant-b 读到 tenant-a 工单 | 跨租户 GET 返回 404，列表为空 |
| 框架隔离 | FastAPI 只做输入输出，业务规则留在 service | 业务逻辑被路由、ORM 和框架异常绑死 | Domain 测试无需启动 HTTP server |

责任边界：本实验负责 API/CLI/SQLite/pytest 基础、租户过滤和顺序/线程级幂等；不负责容器打包、分布式锁、跨进程 exactly-once、真实身份认证或生产数据库高可用。Docker 镜像、staging 和回滚属于尚待接入的发布实验，不能用本阶段证据冒充。

## 3. 先复现失败

阅读[失败注入](failure.md)，先尝试这两个坏设计：

1. 仅按 `Idempotency-Key` 返回旧结果，不校验请求内容。
2. 先查询、事务外再插入，并发运行 8 次。

停止条件：你能解释为什么“HTTP 超时”只代表客户端不知道结果，而不是服务端一定失败。

## 4. 运行实验

在 `agent-runtime-gateway/20-源码` 中运行：

```powershell
python -m pip install -e ".[test]"
python -m pytest ..\21-测试\test_foundation.py -q
```

启动 HTTP 服务：

```powershell
$env:OPSPILOT_DB_PATH = "$env:TEMP\opspilot-f0.db"
python -m uvicorn agent_course.api:create_app --factory --port 8010
```

另开终端调用：

```powershell
$headers = @{ "X-Tenant-ID"="tenant-a"; "Idempotency-Key"="request-demo-01" }
$body = @{ title="VPN access is failing" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8010/tickets -Headers $headers -ContentType application/json -Body $body
```

CLI 路径：

```powershell
$db = "$env:TEMP\opspilot-f0-cli.db"
python -m agent_course.cli ticket --db $db create --tenant tenant-a --title "Printer offline" --idempotency-key request-cli-01
python -m agent_course.cli ticket --db $db list --tenant tenant-a
```

## 5. 五道自测

1. 为什么只保存幂等键还不够？
2. 为什么同一 key 不同 payload 应返回冲突，而不是旧结果？
3. `BEGIN IMMEDIATE` 在这个实验中保护了什么？它不能保护什么？
4. 为什么跨租户读取返回 404 通常比 403 更合适？
5. 如果外部支付成功但 SQLite commit 前崩溃，本实验为什么仍无法保证 exactly-once？

答错时回到对应失败测试，先解释误区，再修改测试让错误实现稳定失败。

## 6. 通过门禁

- `test_foundation.py` 全部通过。
- 同一请求重放只生成一个 ticket id。
- 同 key 不同 payload 返回 409。
- 额外字段被 Pydantic `extra="forbid"` 拒绝。
- 跨租户读取不暴露资源是否存在。
- 按[证据清单](evidence/README.md)记录命令、结果与剩余风险。

岗位映射：Python 后端、FastAPI/Pydantic、SQL 事务、并发、API 契约、幂等与多租户隔离。

下一阶段预习：阅读严格 `RunRequest` 与 `ToolCall`，准备缺字段、未知字段和伪造 tenant 三类坏输入。
