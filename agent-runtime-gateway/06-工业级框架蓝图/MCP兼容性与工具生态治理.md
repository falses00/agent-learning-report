# MCP 兼容性与工具生态治理

生成日期：2026-06-30  
目标：把 MCP 当作工具协议层，而不是企业治理层。

## 1. 采用原则

- MCP 解决工具、资源、提示词的标准化接入。
- MCP 不替代身份、权限、审计、凭据、沙箱、评测。
- 公共 MCP server 不能直接进入企业 trusted registry。
- RC 版本不能当 stable 标准。

## 2. 兼容矩阵

| 维度 | MVP-practical | prod-lite | production |
|---|---|---|---|
| spec version | latest stable | latest stable + 兼容检查 | 明确版本策略 |
| transport | local/mock | stdio/local HTTP | stdio/HTTP with policy |
| tools | 支持基础 tools | tool registry + allowlist | health、quota、audit |
| resources | 可选 | 权限过滤 | 数据分类治理 |
| prompts | 可选 | 版本化 | release gate |
| auth | mock | 最小凭据代理 | IAM/Credential Broker |
| registry | private list | curated registry | private registry + review |

## 3. MCP Server 准入

必须检查：

- 来源。
- license。
- owner。
- tool schema。
- risk level。
- auth model。
- network access。
- data access。
- health check。
- disable path。

## 3.1 MCP Server 准入审核模板

```text
server_name：
server_owner：
source_url：
version：
license：
transport：
tools/resources/prompts 清单：
是否执行本地命令：
是否访问网络：
是否需要凭据：
凭据注入方式：
数据分类：
tenant/workspace 过滤方式：
日志字段：
health check：
timeout：
disable path：
rollback path：
对应评测用例：
审批人：
```

准入判断：

| 结果 | 条件 |
|---|---|
| allow | 来源可信、工具低风险、schema 清晰、无生产凭据、评测覆盖 |
| allow with guard | 需要凭据、内部数据或写操作，但有审批、审计、sandbox 或 dry-run |
| deny | 来源不明、可执行本地命令且无隔离、日志可能泄密、不能禁用 |
| quarantine | 已接入但出现异常、schema 变化、审计缺失或高危 redteam 失败 |

## 4. 降级策略

MCP server 不健康时：

- 熔断该 server。
- 标记 run 为 recoverable。
- 返回结构化错误。
- 不自动切到高风险替代工具。
- 记录 audit event。

## 5. 禁止行为

- 让模型直接选择任意公共 MCP server。
- 让 MCP server 直接拿生产凭据。
- 绕过 Tool Gateway 调 MCP tool。
- 把 MCP registry 当安全信任来源。
