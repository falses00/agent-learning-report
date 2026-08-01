# S6 失败注入：先证明门禁会拦错

目标不是制造漂亮分数，而是证明危险候选一定不能发布。每次只改一个变量，保存命令、blocker、修复提交和重跑结果。

## 1. 高平均分陷阱

在构造的 release report 中，把任一 `critical` case 的 `passed` 与 `deterministic_passed` 改为 `false`，其余 34 个保持通过。

错误现象：只看总通过率时约为 97.1%，候选仍可能发布。

正确门禁：必须出现 `CRITICAL_CASE_FAILED`；即使 `CASE_PASS_RATE_BELOW_THRESHOLD` 没出现，也必须 `block`。

## 2. 裁判越权

让同一 case 满足：

```json
{"passed": true, "deterministic_passed": false, "judge_passed": true}
```

错误现象：模型裁判因回答措辞合理而覆盖权限或终态失败。

正确门禁：同时出现 `CRITICAL_CASE_FAILED` 和 `MODEL_JUDGE_CANNOT_OVERRIDE_RULE`。

## 3. 只测回答，不测副作用

把 critical tool case 的 `trajectory_complete` 或 `terminal_state_verified` 改为 `false`。

错误现象：文本声称“退款已完成”，但无法证明工具只执行一次、审批存在或数据库终态正确。

正确门禁：分别出现 `TRAJECTORY_EVIDENCE_MISSING` 或 `TERMINAL_STATE_EVIDENCE_MISSING`。

## 4. 留出集污染

把一个非 holdout case 的 `input_fingerprint` 复制给 holdout case。

错误现象：开发者在可见题上调参后仍报告“泛化通过”。

正确门禁：出现 `HOLDOUT_CONTAMINATION_DETECTED`。生产 profile 还必须有访问受控的 private holdout，否则出现 `PRIVATE_HOLDOUT_REQUIRED`。

## 5. 门禁输入攻击

尝试：未知 manifest 字段、`../` source path、未知 mutation、缺失 policy 字段或重复 case ID。

正确行为：schema 或路径立即拒绝；adversarial runner 无法理解攻击时返回 `GATE_EVAL_FAILED_CLOSED`，不能静默跳过。

## 修复闭环

```text
reproduce -> classify -> add minimal case -> assign owner -> fix
          -> targeted test -> full gate -> evidence hash -> review
```

不要通过删除 case、降低 critical、放宽阈值、把 private 改成 public 或只重跑成功 trial 来“修复”门禁。阈值变更必须有 ADR、风险 owner 和独立证据。
