# S3 失败注入

## 先用故障树定位

不要把所有失败都归因给 embedding。按 `source -> parse -> chunk -> index -> query -> retrieve -> rerank -> pack -> claim/citation -> operate` 收集信号，再运行：

```powershell
cd "agent-runtime-gateway\20-源码"
python -m agent_course.cli rag-diagnostic-eval ..\22-评测集\rag-diagnostic-baseline.json
```

安全优先级高于质量：跨租户候选、间接注入、无支持关键 claim 和陈旧关键证据必须返回 `block`。未知字段和未知断言也必须失败，防止评测配置静默放水。

## ACL 排序后执行

症状：tenant-b 文档先被向量或关键词检索命中，再在答案层删除。即使最终答案没有显示，未授权内容也已经进入候选、trace 或模型上下文。

修复：可信 tenant 和 allowed source 在打分前过滤；只记录过滤计数，不记录未授权文档 id 或正文。

回归：`test_rag_acl_runs_before_ranking_and_context_creation`。

## 过期文档仍参与排名

症状：旧版“无需审批”政策因词更相似而成为第一引用。

修复：按 `effective_from` / `expires_at` 先过滤，再评分；版本与引用一起返回。

回归：`test_rag_filters_stale_and_untrusted_documents`、`rag-stale-policy-refuses`。

## 低相关结果被强行回答

症状：legacy query 只与当前文档共享一个 `refund`，系统仍生成确定答案。

修复：建立可解释的最小相关性阈值，并用 hard-negative case 调整；阈值不足时拒答。

回归：`rag-no-evidence-refuses`。

## 引用只校验 id

症状：答案引用真实文档 id，但 quote 是模型编造的句子。

修复：校验 tenant、trust、有效期、version、chunk id 和 quote 是否确实存在于文档。

回归：`test_rag_rejects_tampered_citation`。
