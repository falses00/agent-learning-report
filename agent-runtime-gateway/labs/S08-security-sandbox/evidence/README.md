# S08 Evidence

质量门应保存：

- `test_security.py` 的 JUnit 结果。
- `s8-security-adversarial.json` 的 25-case/150-assertion 报告。
- `critical_failed=0` 与 `release_passed=true`。
- 每个阻断请求的 decision、reason codes、side-effect flag 和 metadata-only audit。
- 安全手册引用的一手资料和固定 commit 项目审计。

禁止保存真实 token、客户 URL、内网地址、生产目录和未脱敏 prompt。
