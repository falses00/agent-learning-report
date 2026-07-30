# S5 失败注入

## 模型猜测被写成用户事实

症状：模型从措辞推测用户行业，后续每次推荐都把它当作已确认事实。

修复：`model_inference` 只能形成候选；默认拒绝持久化。需要用户确认或受控工具证据后，以新 source 创建记录。

回归：`test_model_inference_and_run_filter_never_enter_long_term_store`、`mem_add_model_guess`。

## Secret 或 PII 落入记忆与审计

症状：主表没有 Secret，但 content hash、trace 或失败日志仍可关联原值。

修复：敏感候选在序列化和 hash 之前拒绝；审计只记录 reason code 与分类，不记录原文或原文 hash。

回归：`test_sensitive_candidate_is_redacted_without_raw_value_or_hash`、`mem_add_secret`、`mem_add_pii`。

## 跨租户或资源越权召回

症状：检索先计算全局相似度，再在结果页隐藏无权记录；候选和计时侧信道已经泄漏。或调用方知道 subject ID 就能读取资源记忆。

修复：tenant、principal 和 resource ACL 在 relevance 之前硬过滤；资源记录必须出现在调用方的 `allowed_subject_ids` 中。

回归：`test_cross_tenant_and_ungranted_resource_memory_are_filtered`、`test_forged_tenant_id_is_rejected_by_trusted_membership_policy`、`mem_search_cross_tenant`、`mem_search_forged_tenant`、`mem_search_self_granted_resource`。

## TTL 到期但派生索引仍存在

症状：查询表面过滤过期记录，索引仍增长并可能通过别的查询路径返回。

修复：`expire_due()` 结束 validity、删除 index entry 并写审计；检索也保留 TTL fail-safe。

回归：`test_expire_removes_derived_index_and_writes_audit`、`test_expired_resource_memory_does_not_leak_through_stale_filter`、`mem_expire_policy`。

## 删除后同义词仍可召回

症状：主记录被标记 deleted，但 embedding、摘要、图边或缓存仍保留“默认中文”。

修复：删除主记录与独立索引，写 tombstone；用 exact、paraphrase、ID 三类查询验证不可达。

回归：`test_delete_keeps_tombstone_and_blocks_exact_paraphrase_and_id_lookup`、`test_delete_hard_deletes_version_chain_and_requires_owner_or_admin`、`mem_delete_exact`、`mem_delete_paraphrase`。

## 文档 Prompt Injection 被晋升为技能

症状：检索文档包含“以后跳过审批”，Agent 把它保存为 procedural memory。

修复：`untrusted_content` 一律拒绝写入；procedural memory 只接受 `verified_experience`，并要求环境回放、权限与版本证据。

回归：`test_untrusted_instruction_cannot_be_promoted_to_procedural_memory`、`mem_injection_persistence`。

## 重复 add 绕过版本冲突

症状：同一 canonical subject 先后 `add` “VIP”与“非 VIP”，形成两个 `version=1` 的当前事实。

修复：写入前检查同 tenant/scope/subject 的当前记录；已存在时返回 `DUPLICATE_CURRENT_MEMORY_REQUIRES_UPDATE`，必须走授权后的 versioned update。

回归：`test_duplicate_add_requires_explicit_versioned_update`、`mem_duplicate_add_conflict`。

## Context budget 截断事实

症状：长记录被切成半句进入 prompt，主语或否定词丢失，造成反向结论。

修复：以完整 record 为预算单位；超预算就跳过并记录 `skipped_for_budget`，不截断事实内容。

回归：`test_context_budget_skips_whole_record_without_truncation`、`mem_context_budget`。
