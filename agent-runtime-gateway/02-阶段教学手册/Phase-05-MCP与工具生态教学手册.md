# Phase 05 - MCP 与工具生态教学手册

生成日期：2026-07-01  
学习模式：Design-only  
目标：让你理解 MCP 是工具接入协议，不是企业权限系统；你要能设计 MCP server 准入、工具注册、凭据代理、风险分级、禁用路径和回归评测。

## 1. 本阶段解决的失控风险

如果把 MCP 或任意工具市场当成可信边界，会出现：

- Agent 可以接入来源不明的 server。
- MCP server 直接拿生产凭据。
- 工具 schema 描述不清，模型误用工具。
- prompt injection 诱导工具访问内部 URL 或外部恶意 URL。
- 工具出错后无法禁用、回滚、追踪影响范围。
- 工具结果未经脱敏就进入模型上下文、trace 或 audit。

Phase 5 的目标是建立工具生态的治理入口：任何工具都必须先经过注册、准入、策略、凭据、观测和评测。

## 2. 本阶段边界

本阶段学习：

```text
MCP Client
MCP Server
Tool Registry
Tool Gateway
Credential Proxy
Server Admission
Tool Risk Level
Disable Path
Tool Eval
```

不做：

- 真实 MCP server 编写。
- 真实 OAuth/OIDC 集成。
- 生产凭据配置。
- 云端工具市场接入。
- 多 Agent 调度。

## 3. 先建立一个判断

你需要牢牢记住：

```text
MCP 解决工具、资源、提示词的标准化接入。
MCP 不替代身份、权限、审计、凭据隔离、沙箱和评测。
```

所以企业级 Agent 不能让模型自由挑选公共 MCP server，也不能让 MCP server 绕过 Tool Gateway。

## 4. 课时拆分

| 课时 | 主题 | 你要理解 | Design-only 产物 |
|---|---|---|---|
| 5.1 | MCP 的位置 | MCP 是协议层，不是治理层 | MCP 边界图 |
| 5.2 | Tool Registry | 工具必须被登记、分级、版本化 | 工具注册卡 |
| 5.3 | Server Admission | server 先准入再使用 | MCP server 准入卡 |
| 5.4 | Credential Proxy | 凭据不能进入模型上下文 | 凭据代理责任卡 |
| 5.5 | MCP Security | confused deputy、token passthrough、SSRF、session hijacking | 攻击路径表 |
| 5.6 | Disable Path | server 出问题必须可熔断 | 禁用与回滚流程 |
| 5.7 | Tool Eval | 工具选择和参数必须可回归评测 | 工具评测样例表 |

## 5. 课堂练习

### 练习 A：设计 MCP server 准入卡

给每个 server 填一张卡：

| 字段 | 你要写清楚 |
|---|---|
| server_name | server 名称和来源 |
| owner | 内部责任人 |
| source | 官方、自建、第三方、个人项目 |
| license | 是否允许商用和内部分发 |
| auth_model | 是否需要 OAuth、API key、服务账号 |
| tool_list | 暴露哪些工具 |
| risk_level | L0 只读、L1 内部读、L2 写操作、L3 高风险 |
| network_access | 是否可访问内网、外网、文件系统 |
| credential_boundary | 凭据在哪里注入、是否进入模型上下文 |
| audit_fields | 需要记录哪些审计字段 |
| eval_cases | 至少覆盖正常、越权、注入、失败 |
| disable_path | 谁可以禁用、多久生效、怎么回滚 |

### 练习 B：判断一个 server 是否能上线

场景：

```text
一个第三方 MCP server 可以读取 GitHub issue 和创建 issue。
它需要用户 token。
它没有企业审计字段。
它的工具 schema 只有自然语言描述。
```

你要判断：

- 哪些能力可以先允许？
- 哪些能力必须禁用？
- token 是否能传给模型？
- 是否需要只读模式？
- 是否需要私有 fork 或自建 wrapper？
- 上线前至少要补哪些评测 case？

### 练习 C：识别 MCP 安全攻击路径

把下面四种风险写成“攻击路径 -> 控制措施”：

| 风险 | 你要能说出的控制 |
|---|---|
| confused deputy | server 不能替用户越权行动，必须绑定 principal 和 scope |
| token passthrough | token 不进 prompt，不进 trace 明文，由 credential proxy 注入 |
| SSRF | server 网络访问要 allowlist，禁止任意内网探测 |
| session hijacking | session 绑定用户、租户、设备或审批上下文 |

## 6. 失败案例

| 失败案例 | 根因 | 正确设计 |
|---|---|---|
| Agent 自动接入热门 MCP server | 把热度当信任 | 私有 curated registry + 准入审核 |
| server 拿到生产 API key | 凭据边界错误 | credential proxy + 最小权限 token |
| prompt injection 让工具访问 metadata URL | 网络边界缺失 | network allowlist + SSRF 评测 |
| server 返回敏感日志给模型 | 工具结果未过滤 | output filter + audit redaction |
| 工具升级后参数含义变化 | 缺版本治理 | tool_version + regression eval |
| server 出错但无法禁用 | 无 disable path | registry 状态机：candidate/active/disabled/quarantined |

## 7. 架构评审问题

- MCP server 从哪里来，谁负责维护？
- 它是否可以绕过 Tool Gateway？
- 工具 schema 是否足以让模型稳定使用？
- 凭据是否进入 prompt、trace、audit 或 eval report？
- server 能访问哪些网络、文件和外部 API？
- 工具结果返回模型前是否脱敏、截断、标注来源？
- server 升级是否需要重新跑 eval？
- 一旦发现泄漏或误操作，禁用路径多久生效？

## 8. Design-only 过关标准

你应该能复述：

```text
Phase 5 解决的是外部工具生态失控。
MCP 是标准接入协议，但企业可用性来自 Tool Registry、Tool Gateway、Policy、Credential Proxy、Audit、Eval 和 Disable Path。
任何 MCP server 都不能因为流行、star 多或看起来方便就直接成为可信工具。
```

## 9. 后续 Implementation-later 门禁

后续工程阶段才需要：

- MCP server registry 有 active/disabled/quarantined 状态。
- server health check 和 disable path 生效。
- 工具调用经过 schema、policy、risk gate。
- 凭据只在执行端注入，不进入模型上下文。
- SSRF、越权、token 泄漏和工具误选有回归样例。
- 工具版本变更会触发对应 eval。

## 10. 参考锚点

- [MCP 兼容性与工具生态治理](../06-工业级框架蓝图/MCP兼容性与工具生态治理.md)
- [工具风险分级与审批矩阵](../06-工业级框架蓝图/工具风险分级与审批矩阵.md)
- [证据索引](../10-GitHub项目调研/00-证据索引.md)
- [MCP Security Best Practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)
- [Amazon Bedrock AgentCore Gateway](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html)

## 11. 进入 Phase 6 条件

Design-only 进入条件：

- 你能解释 MCP 解决什么、不解决什么。
- 你能设计一张 MCP server 准入卡。
- 你能说明凭据为什么不能交给模型。
- 你能设计一个 server 禁用与回滚流程。
- 你能说明下一阶段为什么要把“记忆”当作受治理的数据系统，而不是简单向量库。
