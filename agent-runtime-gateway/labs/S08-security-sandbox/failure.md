# S08 故障复现

## 代表性故障

旧设计只在 prompt 中要求“不要外发”。攻击文档把外部内容伪装成系统任务，Agent 同时拥有网络和客户数据访问时，文本检测失败就可能直接产生外传。

## 根因

```text
untrusted source
-> model 被说服
-> network/tool sink 无独立策略
-> secret/data exfiltration
```

## 修复

1. 标记 source trust，携带动作指令的外部内容进入 quarantine。
2. 工具必须登记风险、scope、网络、文件、凭据、审批和 sandbox 要求。
3. URL 同时检查 scheme、host、DNS、redirect 和实际出口。
4. 写操作需要 approval 与 operation id，但 approval 不覆盖其他 blocker。
5. 未知输入与控制面故障 fail closed。

## 生产剩余风险

- 应用层 URL 校验不能替代网络 proxy/firewall。
- 路径字符串校验不能解决真实 symlink/TOCTOU，需要受限 mount 和安全文件 API。
- 课程 secret scanner 只覆盖 canary pattern，不是完整 DLP。
- 教学 policy 未接真实 IAM、KMS、MCP runtime 或 sandbox backend。
