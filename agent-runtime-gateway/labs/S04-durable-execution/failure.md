# S4 失败注入

## Provider 成功、本地 commit 前崩溃

症状：退款已产生 provider reference，本地 operation 仍是 `dispatching`。错误实现把“本地无 result”当作“外部未执行”，恢复后再次退款。

修复：保留稳定 operation ID；恢复时先查询 provider。找到结果就补记本地 ledger，不再执行。

回归：`test_crash_after_provider_success_reconciles_without_duplicate_side_effect`、`provider-success-before-local-commit`。

## Provider 调用前崩溃

症状：批准已经持久化，但 worker 在 dispatch 前退出。

修复：operation 仍是 `approved` 且 attempts 为 0，因此恢复可以使用同一 key 执行一次。

回归：`test_crash_before_provider_call_resumes_from_approved_checkpoint`。

## Provider 查询不可用

症状：已有一次 dispatch，但无法确认 provider 是否完成。

错误修复：把状态改回 approved 并自动 retry。

正确修复：operation 进入 `ambiguous`，run 进入 `needs_reconciliation`，错误标记 `recoverable=true`、`retryable=false`；查询恢复或人工确认后才能继续。

回归：`test_unknown_provider_outcome_pauses_until_reconciliation_is_possible`、`unknown-provider-outcome-fails-closed`。

## 同 key 不同 payload

症状：调用方错误复用 operation ID，把 100 元退款改成 200 元。

修复：provider 和本地 ledger 都绑定 canonical args hash；参数变化返回冲突。

回归：`test_provider_rejects_same_operation_id_with_different_payload`。

## 未知 checkpoint 版本

症状：新代码按旧 schema 猜测 pending action，可能重复执行。

修复：checkpoint 明确带 schema version 和 state hash；未知版本拒绝 resume，先迁移或人工处理。

回归：`test_resume_rejects_unknown_checkpoint_schema`。
