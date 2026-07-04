# Phase 03 - Agent 网关与工具治理教学手册

生成日期：2026-06-30  
学习模式：Design-only  
目标：让你理解 Agent Gateway、Model Gateway、Tool Gateway、Policy Gateway 和 Audit 的分工，知道为什么 prompt 不能决定权限。

## 1. 本阶段解决的失控风险

如果没有网关治理：

- 用户请求没有身份、租户、trace。
- 模型可以直接调用高风险工具。
- prompt injection 可以改变工具参数。
- 工具凭据可能进入模型上下文。
- 越权写操作没有审批和审计。

Phase 3 的目标是让所有外部能力都经过受控入口。

## 2. 本阶段边界

本阶段学习五个边界：

```text
Request Gateway
-> Runtime
-> Model Gateway
-> Tool Gateway
-> Policy Gateway
-> Audit Event
```

不做：

- 长线恢复细节。
- MCP 真实接入。
- 长期记忆。
- 沙箱执行。
- 多 Agent。

## 3. 课时拆分

| 课时 | 主题 | 你要理解 | Design-only 产物 |
|---|---|---|---|
| 3.1 | Request Gateway | 每个请求必须绑定身份和 trace | 请求入口责任卡 |
| 3.2 | Model Gateway | 模型选择、预算、fallback 不能散落各处 | 模型路由决策表 |
| 3.3 | Tool Gateway | 所有工具调用必须 schema 校验 | 工具调用流程图 |
| 3.4 | Policy Gateway | 权限是结构化判断，不是 prompt 规则 | PolicyDecisionInput 设计卡 |
| 3.5 | Audit Event | 每次允许/拒绝都能复盘 | 审计字段表 |

## 4. 课堂练习

### 练习 A：设计一次受控工具调用

场景：工单 Agent 想读取知识库政策。

你要设计：

| 字段 | 示例 |
|---|---|
| principal | `user_123` |
| tenant_id | `tenant_demo` |
| tool_name | `knowledge.retrieve` |
| action | `read` |
| risk_level | `L1` |
| policy_decision | allow |
| audit_event | created |

### 练习 B：设计一次拒绝

场景：用户要求“帮我直接关闭客户账号”。

你要说明：

- 这是读操作还是写操作？
- 风险等级是什么？
- 是否需要 dry-run？
- 是否需要 human approval？
- audit event 记录什么？

### 练习 C：发现坏设计

判断下面设计为什么错：

```text
系统 prompt 写着：你不能执行高风险工具。
所以 Tool Gateway 不做权限校验。
```

正确回答：prompt 可以约束模型行为，但不能作为企业权限边界。

## 5. 失败案例

| 失败案例 | 根因 | 正确设计 |
|---|---|---|
| 用户通过 prompt injection 调用删除工具 | Tool Gateway 缺 schema 和 allowlist | 工具调用必须经过 schema、policy、risk gate |
| Agent 把 API key 放进 prompt | 凭据边界错误 | credential proxy，不把 secret 给模型 |
| 只读用户执行写操作 | 权限在 prompt 而非 policy | RBAC/ABAC + approval |
| 失败后没有审计记录 | audit 不是强制事件 | allow/deny/error 都写 audit |

## 6. 架构评审问题

- Gateway 是普通 API 反代吗？
- Tool Gateway 和 MCP server 的边界是什么？
- Policy 判断需要哪些事实？
- 拒绝工具调用是否也要写 audit？
- 工具结果返回模型前是否需要过滤？
- operation_id 为什么必须存在？

## 7. Design-only 过关标准

你应该能复述：

```text
Phase 3 解决的是 Agent 工具调用失控。
Request Gateway 管入口，Model Gateway 管模型和预算，Tool Gateway 管工具 schema 和执行代理，Policy Gateway 管权限，Audit 负责不可抵赖记录。
Prompt 不是权限系统，模型不能直接决定谁能做什么。
```

## 8. 后续 Implementation-later 门禁

后续工程阶段才需要：

- Request Gateway 生成 request_id/thread_id/trace_id。
- Tool Gateway 校验工具参数。
- Policy 拒绝越权写操作。
- Audit Event 记录主体、工具、参数摘要、策略结果和执行结果。
- 证明 Tool Gateway 不可绕过。

## 9. 进入 Phase 4 条件

Design-only 进入条件：

- 你能画出请求到工具调用的治理链路。
- 你能说明 prompt 为什么不能决定权限。
- 你能设计一个 allow、一个 deny、一个 approval 场景。
- 你能说明下一阶段为什么要处理 checkpoint、resume 和幂等。
