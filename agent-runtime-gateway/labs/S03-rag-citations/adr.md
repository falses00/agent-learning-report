# ADR：S3 先采用确定性 lexical baseline

- 状态：Accepted for teaching baseline
- 日期：2026-07-15

## 决策

先使用版本化内存语料、ACL/freshness/trust 前置过滤、确定性 lexical ranking 和引用验证。将 embedding、hybrid search、reranker 与生成模型留作后续对照实验。

## 原因

- 权限和引用错误可稳定复现，不受模型与服务波动影响。
- 学习者能分别观察过滤、ranking、citation 和 refusal。
- 新检索方法必须用同一 S3 eval set 证明收益，不能只凭主观 demo。

## 代价与撤销条件

lexical baseline 对同义词、长文档、表格和多跳问题能力有限。当版本化 corpus 与 hard query 集准备好后，可加入 embedding/hybrid adapter；只有 recall、citation support、P95 和成本综合改善且 critical case 不退化时才替换 baseline。
