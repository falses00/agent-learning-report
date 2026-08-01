# ADR：S6 发布门禁的判定边界

## 决策

1. 使用可移植 JSON manifest 固定 Agent、prompt、model、tool、policy、memory、knowledge、eval 和 grader 版本。
2. 客观结果优先用确定性 assertion；模型 grader 只补充主观维度，且不能覆盖确定性失败。
3. critical security、authorization、duplicate side effect、secret leakage 和持久化污染实行零容忍。
4. 同时验证 transcript/trajectory 与环境 terminal state。
5. teaching profile 允许公开 holdout，但必须警告；production profile 必须使用访问受控的 private holdout。
6. 门禁本身有独立 adversarial suite，未知输入和未知 mutation fail closed。

## 原因

单一平均分无法表达严重风险；只看最终文本无法证明真实副作用；未校准的模型裁判会引入偏差和 grader hacking；没有版本谱系则无法复现发布结论；把公开题称为私有留出会制造虚假信心。

## 取舍

- 严格 schema 提高证据可信度，但 manifest 升级必须显式迁移。
- 零容忍会降低发布速度，但适合不可逆副作用和租户隔离风险。
- 私有 holdout 增加数据治理成本，但可降低评测污染。
- 混合 grader 比单一模型 judge 复杂，但更稳定、可解释、可审核。

## 不包含

当前实现不接入真实模型服务、CI provider、线上 telemetry、秘密管理系统或私有数据仓库。平台集成应通过 adapter 读取同一 manifest 和结果契约，不能把课程资产锁在单一厂商的 eval API 中。
