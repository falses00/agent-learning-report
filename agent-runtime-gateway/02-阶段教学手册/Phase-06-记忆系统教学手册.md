# Phase 06 - 记忆系统教学手册

更新日期：2026-07-13
学习模式：原理教材 + 前端决策实验 + 工程设计；生产存储实现留到 Implementation-later
目标：让你理解记忆不是“把聊天记录塞进向量库”，而是一个有来源、权限、生命周期、写入门禁、召回策略、删除机制和评测闭环的数据治理系统。

> 必读主教材：[Agent Memory 方法谱系与工业选型（2026）](../06-工业级框架蓝图/Agent-Memory方法谱系与工业选型-2026.md)。先比较方法，再做架构选择；不要先选产品再寻找问题。

## 1. 本阶段解决的失控风险

如果记忆系统设计错误，Agent 会越来越不可靠：

- 临时猜测被写成长期事实。
- 错误事实长期污染后续任务。
- 一个用户或租户的记忆被另一个用户召回。
- 过期规则仍然影响决策。
- 敏感信息被写入长期记忆。
- 删除请求无法生效。
- 评测只看回答准确率，不看记忆污染。

Phase 6 的目标是让记忆可写入、可拒绝、可召回、可解释、可过期、可删除、可评测。

## 2. 本阶段边界

本阶段学习：

```text
Working Memory
Session Memory
Long-term Memory
Semantic Memory
Episodic Memory
Graph Memory
Memory Write Gate
Memory Retrieval Policy
Memory TTL
Memory Delete
Memory Eval
```

不做：

- 真实向量数据库实现。
- 真实知识图谱构建。
- 个人隐私数据采集。
- 自动永久记忆所有对话。
- 把外部记忆产品直接作为核心依赖。

## 3. 先建立一个判断

你需要先把记忆拆成五个决策：

```text
该不该写
写成什么
何时召回
何时忘记
如何证明它没有污染、泄漏或拖慢系统
```

记忆系统的核心不是存储，而是门禁和治理。Mem0、Letta、Zep、Graphiti、LangMem 等项目值得研究，但教学阶段先学习它们的设计模式，不急着绑定某个实现。

## 4. 课时拆分

| 课时 | 主题 | 你要理解 | 必交产物 |
|---|---|---|---|
| 6.1 | 边界与分层 | state、context、session、memory、RAG 的区别 | 边界图 |
| 6.2 | 方法谱系 | 上下文裁剪、摘要、向量、层级、反思、图、技能、多模态的原理与代价 | 14 类方法比较表 |
| 6.3 | 工业选型 | 按工作负载、敏感度、关系复杂度和更新频率选择最小架构 | 选型决策记录 |
| 6.4 | 写入门禁 | 不是所有内容都能记，先判来源、范围、敏感度和 TTL | memory write gate 表 |
| 6.5 | 生命周期 | capture、normalize、store、consolidate、retrieve、use、correct、expire/delete | 生命周期审计图 |
| 6.6 | 权限与租户 | 召回必须带 principal、tenant、scope | 召回权限矩阵 |
| 6.7 | 纠错与删除 | 版本冲突、tombstone、索引传播和缓存失效 | 删除传播测试 |
| 6.8 | Memory Eval | 同时评测召回、污染、时效、删除、泄漏、成本和延迟 | 12 条专项评测基线 |
| 6.9 | 趋势判断 | 区分论文事实、项目自报结果和工程推断 | 趋势证据卡 |

推荐顺序：先在站点“记忆实验室”完成 1 次工作负载选型，再完成至少 4 个生命周期场景，最后才进入工程证据验收。

## 5. 课堂练习

### 练习 A：设计 memory write gate

对每个候选记忆，先判断：

| 字段 | 你要写清楚 |
|---|---|
| candidate_fact | 候选记忆内容 |
| source | 来自用户明确声明、工具结果、推断、系统配置还是模型猜测 |
| confidence | 高、中、低 |
| scope | user、team、tenant、global |
| sensitivity | public、internal、private、secret |
| ttl | 永久、30 天、会话内、审批后 |
| write_decision | allow、deny、needs_confirmation、temporary |
| reason | 为什么允许或拒绝 |
| delete_policy | 如何删除或撤销 |

### 练习 B：判断哪些内容能写入长期记忆

| 输入 | 写入决策 | 原因 |
|---|---|---|
| 用户说“我以后默认用中文沟通” | allow | 用户明确偏好，低风险，可删除 |
| 模型猜测“用户可能在金融行业” | deny | 只是推断，不可当事实 |
| 工具返回“客户 A 合同 2026-08 到期” | scoped allow | 需要来源、租户、权限、TTL |
| 用户粘贴 API key | deny + secret handling | 敏感信息不能写长期记忆 |
| 用户临时说“这次只看上海数据” | session only | 本轮条件，不是长期偏好 |

### 练习 C：设计一次错误记忆撤销

场景：

```text
Agent 记住了“客户 A 属于 VIP”。
后来发现这是模型误推断，真实 CRM 中客户 A 不是 VIP。
```

你要说明：

- 这条记忆的来源是什么？
- 为什么 write gate 当初应该拦住？
- 撤销后是否要保留审计记录？
- 回归评测应该新增什么 case？
- 以后同类事实应该从工具结果还是用户口述写入？

## 6. 失败案例

| 失败案例 | 根因 | 正确设计 |
|---|---|---|
| 模型推断被写入长期记忆 | write gate 缺来源判断 | 只有明确来源和足够置信度才能写 |
| 跨租户召回客户资料 | retrieval policy 缺租户过滤 | principal + tenant + scope 强制过滤 |
| 过期政策仍被召回 | 缺 TTL 和版本 | memory 有 effective_at、expires_at、source_version |
| 用户删除偏好后仍被使用 | 删除只删存储不清索引 | delete tombstone + index refresh + eval |
| 敏感信息进入记忆 | secret 识别缺失 | secret denylist + redaction + audit |
| 记忆越多回答越差 | 没有召回精度评测 | memory precision、pollution、staleness 指标 |

## 7. 架构评审问题

- 这条记忆是谁写的，基于什么来源？
- 它属于用户、团队、租户还是全局？
- 它什么时候过期，谁能删除？
- 它能否被另一个 Agent、另一个用户或另一个租户召回？
- 它与 RAG 知识库证据是否混在一起？
- 召回结果进入模型前是否标注来源、置信度和时间？
- 记忆写入失败、拒绝、删除是否写 audit？
- 记忆污染是否进入 regression set？

## 8. 阶段过关标准

你应该能复述：

```text
Phase 6 解决的是长期上下文污染和隐私越界。
记忆不是向量库，而是数据治理系统。
每条记忆都必须有来源、作用域、权限、TTL、删除策略、召回策略和评测样例。
错误记忆不能靠“模型以后注意点”解决，必须靠 write gate、delete、audit 和 regression eval。
```

除通用课前、自测和工程证据门禁外，S5 还要求：

- 在记忆实验室完成一次架构选型，并能解释为什么没有直接采用最复杂方案。
- 至少正确完成 4 个写入/拒绝/临时保存/纠错/删除场景。
- 能从 `memory-engineering-baseline.jsonl` 中挑出一条安全失败用例，说明预期结果和审计证据。

## 9. 后续 Implementation-later 门禁

后续工程阶段才需要：

- memory write gate 拒绝模型猜测和敏感信息。
- retrieval policy 强制 principal/tenant/scope。
- delete/tombstone 能阻止再次召回。
- memory eval 覆盖 recall、precision、pollution、staleness、privacy leakage。
- 记忆写入、拒绝、召回和删除都有 audit。
- RAG 证据、会话状态和长期记忆分开存放、分开评测。

## 10. 参考锚点

- [数据治理与记忆生命周期](../06-工业级框架蓝图/数据治理与记忆生命周期.md)
- [Agent Memory 方法谱系与工业选型（2026）](../06-工业级框架蓝图/Agent-Memory方法谱系与工业选型-2026.md)
- [Memory 专项评测基线](../22-评测集/memory-engineering-baseline.jsonl)
- [RAG 跨层契约与版本治理](../06-工业级框架蓝图/RAG跨层契约与版本治理.md)
- [测评审核体系](../04-测评审核体系/测评审核体系.md)
- [证据索引](../10-GitHub项目调研/00-证据索引.md)
- [Mem0](https://github.com/mem0ai/mem0)
- [Letta](https://github.com/letta-ai/letta)

## 11. 进入 Phase 7 条件

进入下一阶段前：

- 你能区分 working、session、long-term、semantic、episodic、graph memory。
- 你能设计 memory write gate。
- 你能解释为什么模型推断不能直接成为长期事实。
- 你能设计一次跨租户泄漏评测和一次错误记忆撤销流程。
- 你已经在记忆实验室完成一次最小架构选型和至少 4 个生命周期决策。
- 你能说明下一阶段为什么必须用 eval 证明 Agent 没有退化。
