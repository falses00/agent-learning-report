# RAG 闭环实验报告模板

生成日期：2026-06-30  
用途：每次 RAG 优化都用同一份模板记录，防止凭感觉上线。

## 1. 基本信息

| 字段 | 填写 |
|---|---|
| 实验编号 | RAG-EXP-YYYYMMDD-001 |
| 负责人 |  |
| 关联课程 | RAG-XX |
| 关联需求 | REQ-XXX |
| 关联评测集版本 | rag_eval_set_vX |
| 关联索引版本 | index_vX |
| 关联模型/embedding/reranker 版本 |  |
| 实验状态 | draft / running / passed / failed / abandoned |

## 2. 问题定义

用一句话说明这次实验要解决什么失败：

```text
当用户问 [问题类型] 时，系统出现 [失败表现]，导致 [业务影响]。
```

失败归因：

| 层级 | 是否相关 | 证据 |
|---|---|---|
| 数据解析 Parsing |  |  |
| Chunking |  |  |
| Query Understanding |  |  |
| Retrieval |  |  |
| Rerank / Filtering |  |  |
| Context Packing |  |  |
| Generation |  |  |
| Citation / Verification |  |  |
| Policy / ACL |  |  |
| Memory |  |  |
| Freshness / Version |  |  |

## 3. 实验假设

```text
如果我们引入 [最小优化]，那么 [目标指标] 应该从 [baseline] 提升到 [目标值]；
同时 [安全、成本、延迟、引用] 不应退化超过 [阈值]。
```

不要写成“试试某个热门框架”。必须写成“为了解决某个失败，所以做某个最小改变”。

## 4. 对照设计

| 组别 | 设计 | 允许变化 | 不允许变化 |
|---|---|---|---|
| Baseline | 当前方案 | 无 | 文档、问题集、模型、索引版本 |
| Variant A |  | 只改一个变量 | 其他参数 |
| Variant B |  | 只改一个变量 | 其他参数 |

如果一次改了 chunking、rewrite、rerank 和 prompt，就无法知道到底是谁起作用。

## 5. 指标

| 指标 | 类型 | Baseline | 目标 | 阻塞阈值 |
|---|---|---|---|---|
| hit@k | retrieval |  |  |  |
| context precision | retrieval |  |  |  |
| faithfulness | answer |  |  |  |
| citation support | answer |  |  |  |
| unsupported answer rate | safety |  |  |  |
| access violation | security |  |  | 0 |
| p95 latency | cost/perf |  |  |  |
| cost/query | cost/perf |  |  |  |
| regression pass rate | release |  |  |  |

## 6. 失败样例

| case_id | 问题 | 期望证据 | 实际问题 | 失败类型 | 是否进入回归集 |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

失败类型建议使用：

- `retrieval_miss`
- `retrieval_noise`
- `bad_rerank`
- `context_truncation`
- `unsupported_answer`
- `bad_citation`
- `stale_data`
- `memory_pollution`
- `prompt_injection`
- `tenant_escape`
- `cost_regression`

## 7. 上线判断

| 判断项 | 结论 | 证据 |
|---|---|---|
| 是否解决原始失败 | yes / no |  |
| 是否引入新失败 | yes / no |  |
| 安全红队是否通过 | yes / no |  |
| 跨租户隔离是否通过 | yes / no |  |
| 成本是否可接受 | yes / no |  |
| 延迟是否可接受 | yes / no |  |
| 是否写入回归集 | yes / no |  |
| 是否需要人工审批 | yes / no |  |

发布结论只能选一个：

- `ship`：指标通过，安全通过，成本和延迟可接受。
- `ship_with_guardrail`：可小流量上线，但必须有限流、告警或人工兜底。
- `do_not_ship`：存在安全、越权、幻觉、严重退化或证据不足。
- `abandon`：实验假设不成立，复杂度大于收益。

## 8. 课后复述

实验结束后，你应该能这样讲清楚：

```text
这次实验不是为了追某个项目，而是为了解决 [失败]。
我们只改变了 [变量]，用 [指标] 证明它 [有效/无效]。
它的剩余风险是 [风险]。
所以我决定 [上线/不上线/带护栏小流量]。
```

如果这段话说不清楚，就不要进入下一次优化。
