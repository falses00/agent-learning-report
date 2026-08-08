# ADR: S08 使用确定性控制平面作为课程基线

## 决策

先实现不执行真实副作用的严格安全判定器，再接入容器、gVisor、microVM、proxy 和 credential broker adapter。

## 原因

- 可稳定复现 25 类 allow/approval/block/quarantine 行为。
- 将模型行为与授权、网络、文件、凭据和供应链错误分开定位。
- CI 无需云账号、生产 secret 或高权限 runner。
- 未来 backend 替换时仍保留同一策略与攻击回归契约。

## 放弃方案

- 只做 prompt injection classifier：不能证明副作用边界。
- 在 CI 直接运行攻击容器：平台差异大，也容易把容器存在误当成策略正确。
- 把审批作为统一安全开关：审批不能修复 scope、SSRF、secret 或 sandbox 失败。

## 撤销条件

当课程具备可重复、无特权、跨平台的真实 sandbox/network/KMS 测试环境时，将 adapter 结果加入同一 S8 gate；不得删除确定性 baseline。
