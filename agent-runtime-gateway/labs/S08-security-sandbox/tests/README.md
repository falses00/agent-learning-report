# S08 Test Map

| 类别 | 重点测试 |
|---|---|
| 正常 | scoped read、allowlisted HTTPS、approved write |
| 审批 | 高风险写等待审批且副作用为 false |
| 注入 | untrusted instruction -> quarantine |
| Secret | raw token / 非 broker ref -> block |
| Filesystem | traversal、双重编码、symlink escape |
| Network | scheme、host、metadata、DNS rebinding、redirect、DNS evidence |
| Sandbox | unavailable -> fail closed |
| MCP | server admission、version、capability diff |
| Contract | unknown tool、scope、policy outage、unknown request field |

新增安全事故必须先写失败 case，再修复策略，并保留 regression owner。
