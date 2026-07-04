# RAG 实验执行模板

生成日期：2026-06-30  
用途：每个 RAG 优化实验都按同一套格式执行，避免“感觉变好了”。

## 1. 实验前提

每次实验只允许改一个主变量。

可变变量包括：

- parser。
- chunk size。
- chunk overlap。
- semantic chunking threshold。
- embedding model。
- sparse/dense 权重。
- query rewrite。
- topK。
- reranker。
- context packing。
- citation prompt。
- ACL filter。
- cache threshold。

禁止同时改三四个变量后宣称某个方法有效。

## 2. 实验卡片

```text
实验编号：
实验名称：
对应问题：
假设：
baseline 配置：
优化配置：
固定不变的变量：
数据集版本：
评测命令：
trace 样本：
成本预算：
延迟预算：
安全边界：
```

## 3. Baseline 要求

baseline 必须能复现失败，而不是只跑成功样例。

至少包含：

- 3 个能答对的问题。
- 3 个答错或找不到的问题。
- 1 个权限/安全负例。
- 1 个长文或复杂上下文问题。
- 1 个成本或延迟记录。

## 4. 指标记录

| 指标 | baseline | 优化后 | 变化 | 是否可接受 |
|---|---:|---:|---:|---|
| context recall | | | | |
| context precision | | | | |
| hit@k | | | | |
| answer accuracy | | | | |
| faithfulness | | | | |
| citation support | | | | |
| p95 latency | | | | |
| cost/query | | | | |
| attack success rate | | | | |
| access violation | | | | |

## 5. 结论规则

| 结果 | 判断 |
|---|---|
| 质量提升、成本延迟可接受、安全不退化 | 可进入下一阶段 |
| 质量提升但成本或延迟过高 | 加 route/cache/topN 控制后再测 |
| recall 提升但 precision 大降 | 不直接采用，考虑 rerank/filter |
| 安全或权限退化 | 阻塞 |
| 只在少量样例上提升 | 加入更多样本后再判断 |
| 无稳定提升 | 放弃或保留为 pattern only |

## 6. 实验复盘

每个实验结束必须写：

```text
我们原本以为：
实际发现：
最有价值的失败样本：
新增 regression case：
是否修改诊断矩阵：
是否修改默认路线：
是否需要新小项目参考：
下一步：
```

## 7. 教学说明

讲给学习者时，必须回答：

- 这个实验为什么不能跳过？
- 它对应工业级 RAG 的哪一层？
- 失败时应该看哪个 trace/span？
- 这个优化为什么可能不值得上线？
- 如果上线，release gate 要锁定哪些版本？
