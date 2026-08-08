# S07 证据清单

每次验收至少保存：

- `pytest` 或 JUnit 报告。
- S7 baseline JSON，包含 metrics、warnings、evidence hash 和 decision hash。
- S7 adversarial JSON，包含 14 个 case 和 46 条断言。
- 一个合法 W3C traceparent 与父子 span 摘要。
- 一个通过验证的 audit chain head。
- 一个 replay packet 的版本字段清单。
- 一个 P0/P1 incident 与 regression owner。
- secret canary 不在 export 中的扫描结果。

不要保存真实 secret、客户 prompt、完整工具输出或个人身份明文。课程本地报告是预检证据，只有 CI artifact attestation 才能证明构建来源。
