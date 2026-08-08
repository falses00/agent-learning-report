# S08 Security / Sandbox Lab

## 目标

把 S8 从威胁模型文档变成可运行控制平面：即使模型被间接注入、URL 指向内网、路径逃出 workspace、sandbox 不可用或 MCP server 扩权，副作用也必须被阻断或隔离。

## 运行

```powershell
cd agent-runtime-gateway\20-源码
python -m pytest ..\21-测试\test_security.py -q
python -m agent_course.cli security-eval ..\22-评测集\s8-security-adversarial.json
```

预期：`25/25` critical case、`150/150` assertions、`critical_failed=0`、`release_passed=true`。

## 工程边界

- 实际执行：严格 policy/request schema、scope、source trust、secret 扫描、路径规范化、URL/DNS/redirect、approval、operation id、sandbox availability 和 MCP capability diff。
- 不执行真实 shell、HTTP、文件、KMS 或 MCP 请求。
- `sandbox_available`、`resolved_ips` 和 `symlink_escape` 是确定性教学信号，不是生产隔离实现。
- 真实部署仍需网络 proxy、文件 mount、容器/gVisor/microVM、credential broker、SIEM 和定期逃逸测试。

## 验收

- 允许、待审批、阻断、隔离四种状态语义互斥。
- 未审批写操作没有副作用。
- approval 不覆盖 secret、scope、path、egress、sandbox 或 MCP blocker。
- URL 对原始地址、解析 IP 和 redirect 链逐次检查。
- policy/sandbox 不可用、未知字段和未知工具 fail closed。
- audit 只包含 metadata 与 reason code。
