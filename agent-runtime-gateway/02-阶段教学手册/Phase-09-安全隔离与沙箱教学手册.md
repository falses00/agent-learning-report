# Phase 09 - 安全隔离与沙箱教学手册

生成日期：2026-07-01  
学习模式：Design-only  
目标：让你理解 Agent 安全不能靠 prompt，而要靠威胁模型、工具风险分级、凭据边界、网络边界、文件边界、沙箱 profile、红队样例和审计门禁。

## 1. 本阶段解决的失控风险

如果没有安全隔离：

- 高风险工具在宿主机裸跑。
- 模型或工具可以读取 workspace 外文件。
- 工具可以访问任意外网或内网地址。
- secret 出现在 prompt、trace、log、memory 或 eval report。
- 浏览器自动化访问非授权域名。
- 代码执行、shell、文件处理没有资源限制。
- prompt injection 能变成真实越权动作。

Phase 9 的目标是让所有高风险能力按风险等级进入合适的隔离环境，并用红队评测证明边界有效。

## 2. 本阶段边界

本阶段学习：

```text
Threat Model
Risk Level
Sandbox Profile
Credential Broker
Network Egress Policy
Filesystem Policy
Process/Resource Limit
Secret Redaction
Adversarial Probe
```

不做：

- 真实容器、microVM 或云沙箱部署。
- 真实 secret manager 配置。
- 真实浏览器自动化账号登录。
- 攻击工具编写。

## 3. 先建立一个判断

安全隔离的核心问题是：

```text
如果模型被诱导、工具被污染、输入是恶意的，系统还能不能阻止真实损害？
```

所以 prompt 只是行为引导，不能作为安全边界。真正的安全边界在 policy、credential、sandbox、network、filesystem、audit 和 eval。

## 4. 课时拆分

| 课时 | 主题 | 你要理解 | Design-only 产物 |
|---|---|---|---|
| 9.1 | 威胁建模 | 先列攻击路径，再选控制 | threat matrix |
| 9.2 | 工具风险分级 | 读、写、外发、执行要分级 | tool risk table |
| 9.3 | 沙箱 profile | 不同风险需要不同隔离 | sandbox profile 卡 |
| 9.4 | 凭据边界 | secret 不进模型上下文 | credential boundary 图 |
| 9.5 | 网络/文件边界 | egress 和 filesystem 必须 allowlist | 边界策略表 |
| 9.6 | 红队探针 | 用攻击样例证明边界 | adversarial probe 表 |
| 9.7 | 安全事故响应 | 安全失败必须冻结发布 | 安全阻塞规则 |

## 5. 课堂练习

### 练习 A：设计工具风险分级

| 工具 | 风险等级 | 最低控制 |
|---|---|---|
| 只读知识库检索 | L0/L1 | Tool Gateway + 权限过滤 |
| 读取客户资料 | L1/L2 | tenant scope + audit |
| 修改工单状态 | L2 | dry-run + approval + operation_id |
| 关闭账号/退款 | L3 | 双人审批 + 幂等 + 回滚计划 |
| 本地文件处理 | L2 | restricted workspace |
| shell/代码执行 | L3 | sandbox + egress deny by default |
| 浏览器自动化 | L2/L3 | domain allowlist + scoped session |

### 练习 B：设计 sandbox profile

给每类高风险能力写 profile：

| 字段 | 你要写清楚 |
|---|---|
| profile_name | 例如 `shell_restricted` |
| allowed_paths | 只能访问哪些路径 |
| denied_paths | 明确禁止哪些路径 |
| network | deny、allowlist、proxy |
| secrets | 是否注入、如何短期化 |
| cpu/memory/time | 资源上限 |
| approval_required | 是否需要人工审批 |
| audit_required | 必须记录哪些事件 |
| kill_switch | 如何立即停止 |
| probes | 用什么攻击样例验证 |

### 练习 C：写红队探针

把每个攻击写成“输入 -> 期望阻断”：

| 攻击 | 期望 |
|---|---|
| 用户要求读取系统目录 | 拒绝并写 audit |
| 工具结果里夹带“忽略规则外发数据” | 标记 untrusted，不执行 |
| prompt 要求把 token 打印出来 | secret scanner 阻断 |
| 浏览器访问非 allowlist 域名 | egress policy 阻断 |
| retry 重复执行写操作 | operation_id 阻断 |

## 6. 失败案例

| 失败案例 | 根因 | 正确设计 |
|---|---|---|
| shell 工具读取用户目录 | 文件边界缺失 | workspace allowlist |
| 浏览器打开恶意 URL | egress 未限制 | domain allowlist |
| secret 出现在 trace | redaction 缺失 | secret scanner + hash/ref |
| 工具结果诱导下一步越权 | Tool Injection 未处理 | tool output 标记 untrusted |
| 高风险写操作无需审批 | 风险分级缺失 | approval + dry-run |
| sandbox 失败后继续执行 | fallback 不安全 | fail closed + quarantine |

## 7. 架构评审问题

- 这个工具最坏能造成什么损害？
- 它需要文件、网络、进程、凭据中的哪些权限？
- 哪些权限默认拒绝，哪些必须 allowlist？
- 模型是否能看到 secret 或生产凭据？
- sandbox 失败时是 fail open 还是 fail closed？
- 红队探针是否覆盖注入、外发、越权、secret、重复副作用？
- 安全失败是否立即冻结发布？

## 8. Design-only 过关标准

你应该能复述：

```text
Phase 9 解决的是高风险工具和恶意输入带来的真实损害。
安全不是 prompt 约束，而是威胁模型、工具分级、凭据边界、沙箱、网络和文件策略、审计、红队评测共同构成的防线。
任何高风险工具都必须 fail closed，并且有 kill switch、audit 和 regression probe。
```

## 9. 后续 Implementation-later 门禁

后续工程阶段才需要：

- sandbox profile 能阻止 workspace 外文件读取。
- egress allowlist 阻止非授权域名。
- secret scanner 覆盖 prompt/log/trace/audit/eval。
- 高风险工具无 approval 时不能执行。
- red team critical case 100% 阻断。
- sandbox fail closed 和 quarantine 生效。

## 10. 参考锚点

- [安全威胁模型与控制矩阵](../06-工业级框架蓝图/安全威胁模型与控制矩阵.md)
- [工具风险分级与审批矩阵](../06-工业级框架蓝图/工具风险分级与审批矩阵.md)
- [SLO 与错误预算](../06-工业级框架蓝图/SLO与错误预算.md)
- [资料核验记录-2026-07-01](../10-GitHub项目调研/资料核验记录-2026-07-01.md)

## 11. 进入 Phase 10 条件

Design-only 进入条件：

- 你能设计 tool risk table。
- 你能设计 sandbox profile。
- 你能解释 prompt 为什么不是安全边界。
- 你能写出至少 5 个红队探针。
- 你能说明下一阶段为什么多 Agent 协同必须靠契约、锁、仲裁和评测，而不是角色聊天。
