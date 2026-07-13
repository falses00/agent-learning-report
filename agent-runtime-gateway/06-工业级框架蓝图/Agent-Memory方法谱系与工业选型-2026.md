# Agent Memory 方法谱系与工业选型（2026）

- 核验日期：2026-07-13
- 适用阶段：工程主线 S5 / Design-only Phase 06
证据规则：只引用原论文、OpenReview、官方项目仓库和官方文档。论文实验结果不等于独立复现，项目 README 自报数据不等于生产 SLA。

## 1. 一句话定义

Agent Memory 是一套把历史消息、用户事实、业务事件、环境经验和可复用技能选择性写入、组织、召回、纠正、遗忘、删除并评测的控制系统。

它不是一个向量数据库，也不是把完整聊天记录不断塞回 prompt。

## 2. 先分清五个容易混淆的对象

| 对象 | 主要问题 | 生命周期 | 典型存储 | 不负责什么 |
|---|---|---|---|---|
| Runtime State | 当前 Run 运行到哪一步 | 秒到天 | checkpoint、event log | 不负责长期个性化 |
| Working Context | 这一步模型需要看到什么 | 单次调用 | prompt、context pack | 不负责永久保存 |
| Session History | 本次会话发生过什么 | 分钟到周 | message log、summary | 不自动成为长期事实 |
| Long-term Memory | 跨会话值得保留什么 | 天到年 | profile、fact store、vector、graph、skill library | 不等于企业知识库 |
| RAG Knowledge | 有权限访问的外部知识证据 | 按文档版本 | document store、index | 不应混入用户偏好和模型猜测 |

判断口诀：状态回答“现在做到哪”，上下文回答“本步看什么”，记忆回答“以后值得记什么”，RAG 回答“外部证据是什么”。

## 3. 三个分类轴

### 3.1 按时间范围

- **Working memory**：当前步骤的任务状态、最近观察和工具结果。
- **Session memory**：本次会话的消息、摘要和临时约束。
- **Long-term memory**：跨会话保留的事实、偏好、事件、经验和技能。

### 3.2 按内容类型

- **Semantic memory**：稳定事实和明确偏好，例如“用户要求默认使用中文”。
- **Episodic memory**：带时间和上下文的事件，例如“2026-07-12 一次退款审批被拒绝”。
- **Procedural memory**：可复用流程、策略、工具使用方式和环境 gotcha。
- **Resource memory**：文件、截图、页面、数据集等资源的索引和描述。
- **Relational memory**：实体、关系、时间有效性和来源组成的图结构。

### 3.3 按控制方式

- **Rule-controlled**：由明确规则决定写入、TTL、删除和作用域。
- **LLM-mediated**：模型抽取、摘要、链接、合并或生成反思。
- **Agent-controlled**：Agent 通过 memory tool 主动读取和修改不同层级。
- **Policy-learned**：通过训练或反馈学习何时写、读、压缩和遗忘，目前仍偏研究。

工业系统通常是混合控制：规则守住权限和隐私，模型负责抽取与压缩，评测决定策略能否发布。

## 4. 统一生命周期

```text
Capture
-> Select / Write Gate
-> Extract / Normalize
-> Store / Index
-> Consolidate / Evolve
-> Retrieve
-> Context Assembly
-> Use / Act
-> Correct / Expire / Delete
-> Evaluate / Audit
```

### 4.1 Capture

收集消息、工具结果、业务事件、文件、截图或运行轨迹。Capture 只产生候选，不表示允许长期保存。

### 4.2 Select / Write Gate

根据来源、用途、作用域、敏感级别、可验证性和保留期限作出：

- `allow`
- `session_only`
- `needs_confirmation`
- `scoped_allow`
- `versioned_update`
- `deny`
- `deny_and_redact`

### 4.3 Extract / Normalize

把自然语言转成结构化事实、事件、实体、关系或技能。模型抽取结果仍需 schema、来源和置信度，不能因为输出是 JSON 就自动可信。

### 4.4 Store / Index

按查询模式选择 message log、KV/profile、关系库、向量索引、时间图或技能库。主记录与派生索引必须有同一个 `memory_id` 和版本。

### 4.5 Consolidate / Evolve

去重、摘要、聚类、建立链接、处理冲突、降低旧记忆权重，或把多个 episode 提炼成稳定规则。错误合并会把局部错误放大成全局污染。

### 4.6 Retrieve

召回不是只算 embedding 相似度。一个教学用评分模型可以写成：

```text
score = relevance
      + recency
      + importance
      + source_quality
      + task_fit
      - staleness_penalty
      - sensitivity_penalty
      - contradiction_penalty
```

权重必须由 eval 调整，而不是凭感觉设定。权限、租户、有效期和删除状态属于硬过滤，不能靠分数降低来代替阻断。

### 4.7 Context Assembly

对召回结果做去重、排序、引用、压缩和 token 预算控制。进入 prompt 的每条长期记忆至少标注来源、时间和作用域。

### 4.8 Correct / Expire / Delete

纠正应新增版本或失效旧版本，不能无审计地覆盖。删除必须传播到主库、向量索引、图边、缓存和允许保留的备份策略，并用原文、同义词和 ID 再检索证明不可达。

### 4.9 Evaluate / Audit

记录写入、拒绝、召回、使用、更新、删除和导出的决定。线上事故必须进入 regression set。

## 5. 代表方法对比

“工程状态”是课程判断，不是厂商排名：

- **基础模式**：机制成熟，可自行实现。
- **工程框架/产品**：已有持续维护的开发接口，仍需自行验证治理能力。
- **研究原型**：论文和代码可学习，生产边界尚未充分公开验证。

| 方法 | 核心机制 | 适用场景 | 主要优点 | 主要代价与失败模式 | 工程状态 |
|---|---|---|---|---|---|
| Context + trimming | 保留最近 turns，按规则裁剪 | 单会话工具 Agent | 最简单、延迟低、易恢复 | 旧细节丢失，不能跨会话学习 | 基础模式 |
| Summary memory | 定期把历史压成摘要 | 长会话客服、任务交接 | 节省 token，结构清晰 | 摘要漂移、错误被压成“事实” | 基础模式 |
| Vector RAG memory | chunk、embedding、top-k | 大量文本片段和事实宽召回 | 生态成熟、扩展容易 | 多跳、时间和冲突较弱 | 基础模式 |
| Generative Agents | memory stream + relevance/recency/importance + reflection | 社会模拟、角色行为 | 清楚展示观察、反思、计划闭环 | 成本高，生产权限治理不足 | 研究原型 |
| Reflexion | 失败反馈生成 verbal reflection，写入 episodic buffer | 代码、Web、游戏试错 | 不微调即可积累教训 | 评价器错误会产生“自信的坏经验” | 研究模式 |
| Voyager | 把成功轨迹固化为可检索、可组合代码技能 | 工具 Agent、具身 Agent | 技能复用和组合能力强 | 必须沙箱执行并验证技能安全 | 研究模式 |
| MemoryBank | 会话记忆、画像、重要性和时间衰减 | 陪伴和个性化对话 | 引入强化与遗忘 | 事实冲突、租户和审计不是核心 | 研究原型 |
| MemGPT / Letta | core、recall、archival 多层，Agent 通过工具管理虚拟上下文 | 长对话、stateful Agent | 内存层级可观察，主动管理灵活 | 工具开销、错误自写、注入持久化 | 工程框架 |
| Mem0 | 选择性抽取、合并、用户/会话/组织作用域，可选图 | SaaS Agent、客服、个人助手 | API 化、作用域明确、接入快 | 托管与开源能力有差异，基准多为自报 | 工程产品 |
| Zep / Graphiti | episode/entity/community 子图，关系带有效时间，混合检索 | CRM、客服、动态企业事实 | 时间、来源、多跳和冲突表达强 | 实体消歧错误会扩散，图构建成本高 | 工程产品/开源引擎 |
| A-MEM | Zettelkasten 风格 note，动态 tags、links 和 memory evolution | 研究 Agent、跨任务知识积累 | 结构会随新信息演化 | LLM 维护成本和错误链接累积 | 研究原型 |
| HippoRAG / 2 | LLM 抽取图，Personalized PageRank 激活相关 passage | 多跳 QA、复杂文档关联 | 关联检索强，减少反复检索 | 离线抽图成本、增量和 ACL 需补齐 | 研究原型 |
| MemoryOS | short/mid/long 三层，FIFO、摘要和分页式更新 | 个人助手、层级摘要教学 | OS 类比清晰，生命周期完整 | 摘要层丢细节，LoCoMo 外证据有限 | 研究原型 |
| MIRIX | core/episodic/semantic/procedural/resource/vault 六类，多 Agent 管理多模态记忆 | 桌面助手、屏幕与资源记忆 | 覆盖图像、资源和流程 | 系统复杂，持续屏幕采集有隐私风险 | 研究原型 |

## 6. 方法原理与取舍

### 6.1 Context 与摘要

原理：把当前模型窗口当作速度最快、容量最小的工作区。最近消息直接保留，较旧内容裁剪或摘要。

- **优点**：实现简单、调试直观、无需额外召回。
- **缺点**：摘要是有损压缩；长会话会发生事实漂移；跨会话状态需要外部持久化。
- **适用**：所有系统的基础层。
禁用误区：不要把 checkpoint、聊天历史和长期事实做成同一个对象。

### 6.2 Vector RAG memory

原理：把历史片段编码成向量，查询时用相似度召回，再把候选片段放入上下文。

- **优点**：对同义表达和宽召回有效，基础设施成熟。
- **缺点**：相似不代表真实、不代表当前有效，也不代表当前主体有权限。
- **适用**：大量非结构化文本、证据片段。
升级条件：当任务需要时间冲突、实体关系或多跳时，引入结构化 metadata、rerank 或 graph，而不是只调 `top_k`。

### 6.3 Reflection 与 episodic memory

原理：把一次任务轨迹、结果和评价压成经验；在相似任务前召回经验，避免重复错误。

- **优点**：可以保存“怎么做”和“哪里会失败”，不只保存用户事实。
- **缺点**：反思是模型生成物，不一定正确；错误经验会跨任务放大。
- **适用**：代码 Agent、Web Agent、运维 Agent、具身任务。
门禁：只有通过规则或环境验证的经验才能提升为 procedural memory。

### 6.4 Hierarchical / virtual context

原理：借鉴操作系统，把少量核心记忆固定在上下文，把大量历史放在可检索层，由 Agent 主动换入换出。

- **优点**：层级和容量边界清楚，适合长寿命 Agent。
- **缺点**：memory tool 本身成为新的决策面；Agent 可能忘记搜索、错误覆盖或被注入诱导写入。
- **适用**：跨会话个人助手、开发者可观察的 stateful Agent。
门禁：core memory 的写入比普通 archival memory 更严格。

### 6.5 Temporal graph memory

原理：把事实表示为实体、关系、来源和有效时间。新事实到来时，不直接覆盖，而是结束旧边的有效区间并创建新版本。

- **优点**：适合关系、多跳、变化历史和冲突查询。
- **缺点**：实体消歧、关系抽取和图增长都可能出错；图不天然解决权限。
- **适用**：CRM、合同、组织、客户关系和动态业务事件。
门禁：所有节点和边仍需 `tenant_id`、classification、source 和 validity interval。

### 6.6 Skill / procedural memory

原理：从成功轨迹提炼可复用步骤、代码或策略，在新任务中检索和组合。

- **优点**：从“记住用户说过什么”升级为“记住环境里怎样完成任务”。
- **缺点**：环境版本变化后技能会过期；可执行技能可能包含危险操作。
- **适用**：Web、代码、运维、游戏和具身 Agent。
门禁：技能必须绑定环境版本、权限范围、测试结果和回滚方式。

### 6.7 Multimodal memory

原理：把截图、视频、音频、文件与文本事件关联，生成可检索的资源和事件记忆。

- **优点**：能处理桌面和现实环境中只存在于视觉或资源状态的信息。
- **缺点**：存储量、隐私暴露、实体对齐和删除传播更难。
- **适用**：需要屏幕历史或多模态资源的研究与受控产品。
门禁：默认最小采集，优先本地处理，必须支持区域遮罩、敏感识别和按资源删除。

## 7. 工业选型顺序

不要先问“选 Mem0 还是 Letta”，先问下面的问题。

### 7.1 第一步：有没有跨会话收益

若只需要当前任务状态，使用 Runtime State 和 Session History，不建长期记忆。

### 7.2 第二步：记忆内容是什么

| 内容 | 首选表示 |
|---|---|
| 最近消息和工具结果 | message log + trimming |
| 会话主线 | versioned summary |
| 明确用户偏好 | structured profile / semantic fact |
| 大量非结构化片段 | vector + metadata + rerank |
| 动态实体关系和时间冲突 | temporal graph + vector/full-text hybrid |
| 失败教训和任务轨迹 | episodic trace + verified reflection |
| 可复用工作流或代码 | procedural skill library |
| 截图、文件、页面资源 | resource index + multimodal store |

### 7.3 第三步：失败代价是什么

- 低风险偏好可 `needs_confirmation` 后写入。
- 业务事实优先由受控工具或权威系统提供。
- 受监管数据默认不进入自动长期记忆。
- Secret 必须 `deny_and_redact`，不能只设置短 TTL。

### 7.4 第四步：最小架构先行

```text
message log
+ versioned summary
+ structured fact store
+ write/retrieval/delete policy
+ audit
+ memory eval
```

只有当 eval 证明关系、多跳或规模需求无法满足时，才增加 vector、graph、agentic controller 或 multimodal memory。

## 8. 写入与冲突控制

### 8.1 最小 Memory Record

```json
{
  "memory_id": "mem_...",
  "type": "semantic|episodic|procedural|resource|relation",
  "content": "...",
  "source_type": "user_statement|tool_result|system_config|model_inference",
  "source_ref": "run/tool/document/version",
  "principal_id": "...",
  "tenant_id": "...",
  "scope": "session|user|team|tenant",
  "classification": "public|internal|private|secret|regulated",
  "confidence": 0.0,
  "valid_from": "...",
  "valid_to": null,
  "expires_at": "...",
  "version": 1,
  "status": "active|superseded|expired|deleted",
  "policy_version": "..."
}
```

### 8.2 来源优先级不是绝对规则

通常可从高到低考虑：

```text
系统配置 / 权威业务系统
> 当前受控工具结果
> 用户明确声明
> 经验证的历史事实
> 模型摘要
> 模型推断
```

但当前用户偏好可能比旧 CRM 字段更新，法务冻结信息可能覆盖普通系统数据。因此冲突决策还必须看领域、时间、权限和有效区间。

### 8.3 冲突处理

1. 保留两条来源，不静默覆盖。
2. 标记冲突字段和影响范围。
3. 按权威性、时间、作用域和领域规则裁决。
4. 失效旧版本，保留审计。
5. 对旧表达、同义词和依赖它的 summary/graph edge 做回归。

## 9. 删除不是一条 SQL

删除闭环至少包括：

```text
authorize request
-> locate canonical record
-> create tombstone / audit event
-> remove or invalidate primary record
-> propagate to vector index
-> propagate to graph edges
-> evict cache and context packs
-> apply backup retention policy
-> retrieve by id, exact text and paraphrase
-> verify zero unauthorized recall
```

`deletion_success = 1` 只在所有可在线召回的副本都不可达时成立。

## 10. 评测体系

### 10.1 基准

| 基准 | 重点 | 课程用途 | 边界 |
|---|---|---|---|
| LoCoMo（2024） | 约 300 turns、平均 9K tokens、最多 35 sessions 的长期对话，含时间和因果 | 入门测 single-hop、temporal、multi-hop、grounding | 仍以对话记忆为主 |
| LongMemEval（ICLR 2025） | information extraction、multi-session reasoning、knowledge update、temporal、abstention | 测更新、冲突、时间与拒答 | 主要是 assistant 历史 |
| LongMemEval-V2（2026 WIP） | 451 个问题，最多 500 条环境轨迹和 115M tokens，测状态、工作流、gotcha、前提 | 高阶测“是否成为熟悉环境的操作者” | 工作进行中，coding agent 方法延迟高 |
| MemoryAgentBench（ICLR 2026） | 增量多轮写入、检索、更新与记忆管理 | 测在线记忆能力而非一次性静态 QA | 需要结合生产安全指标 |
| DMR | 深层历史事实检索 | 检索压力测试 | 不能覆盖删除和治理 |
| HippoRAG 系列数据集 | 多跳和关联检索 | 比较 vector 与 graph retrieval | 不是完整用户记忆评测 |

### 10.2 工业指标

| 维度 | 指标 | 典型阻塞条件 |
|---|---|---|
| 正确性 | answer accuracy、F1、knowledge update accuracy | 关键事实错误 |
| 召回质量 | memory recall、precision、evidence coverage | precision 下降导致污染 |
| 时间 | temporal reasoning、stale_memory_rate | 过期记忆仍使用 |
| 冲突 | conflict detection/resolution | 无来源覆盖旧值 |
| 安全 | privacy leakage、cross-tenant contamination | 任一泄漏 case 失败 |
| 删除 | deletion_success、paraphrase re-retrieval | 删除后仍可召回 |
| 归因 | source coverage、citation accuracy | 关键记忆无来源 |
| 成本 | write amplification、storage growth、tokens、p50/p95 latency | 超过预算或 SLO |
| 增量价值 | with/without memory ablation | 质量无提升却增加成本或风险 |

平均分不能掩盖跨租户、Secret、删除和错误事实等 critical failure。

## 11. 常见失败与修复

| 失败 | 根因 | 修复 | 必加回归 |
|---|---|---|---|
| 模型猜测写成事实 | 没有来源门禁 | 推断只做 candidate，需确认或工具验证 | 错误偏好不得写入 |
| 摘要不断漂移 | 反复摘要覆盖原始证据 | 保留来源窗口、版本和定期重建 | 多轮摘要事实一致性 |
| 删除后仍召回 | 派生索引未同步 | tombstone + index/cache propagation | exact/paraphrase/id 三类检索 |
| 跨租户召回 | 权限作为 soft score | ACL 硬过滤先于检索 | tenant A 查询 tenant B |
| 图中旧关系仍有效 | 没有 validity interval | 结束旧边并创建新版本 | 指定时间点关系查询 |
| 经验库越积越差 | 反思未验证、无遗忘 | 环境验证、去重、降权和 TTL | 错误反思不能提升为技能 |
| token 和延迟失控 | 无预算、无 ablation | context packer、top-k/rerank、预算门禁 | p95 与质量联合门禁 |
| Prompt injection 持久化 | 把文档指令当记忆 | untrusted 标记、内容/指令分离 | 恶意文档不得改 core memory |

## 12. 未来走向

### 12.1 已有一手证据支持的变化

1. **从用户历史转向环境经验**：LongMemEval-V2 直接评测 Agent 是否记住界面状态、工作流和环境 gotcha。
2. **图与时间成为重要方向**：Graphiti、HippoRAG 2、A-MEM 以及 2026 graph memory survey 都在解决关系、演化和多跳问题。
3. **系统成本开始被单独研究**：2026 年 Agent Memory systems characterization 把构建、召回和生成阶段分开归因，强调 freshness、latency 和 fleet-scale 取舍。
4. **Memory 类型继续细分**：Semantic、episodic、procedural、resource、relation 和不同 user/session/org scope 正在成为显式设计对象。
5. **多模态记忆进入研究系统**：MIRIX 等工作开始处理长期截图和资源记忆，但隐私与存储风险更高。

### 12.2 基于上述证据的课程推断

以下是推断，不是已完成的行业事实：

- 企业 Memory 可能逐步拆成消息历史、用户事实、业务实体图、环境经验和技能库，而不是单一 vector DB。
- Memory Controller 可能从 prompt heuristic 走向可评测的 tool/policy agent，但 controller 自身的错误和延迟会成为新风险。
- Temporal graph 会成为动态企业数据的常见候选，但不会替代向量宽召回和结构化事实库。
- 遗忘、纠错、删除、审计和数据主权的重要性会超过“记住更多”。
- 评测会继续从离线 QA 走向任务成功率、长期运营、staleness 曲线、用户纠正和环境版本迁移。
- 参数化记忆、外部记忆和上下文压缩会共存，工程选择将由更新速度、可删除性、成本和风险决定。

## 13. 推荐学习顺序

1. 实现 message log、trimming 和 versioned summary。
2. 实现 structured fact store、write gate、作用域和删除。
3. 加入 vector retrieval，并做 with/without memory ablation。
4. 加入冲突、TTL、跨租户和 prompt injection eval。
5. 只有多跳和时间需求被 eval 证明后，再实验 temporal graph。
6. 只有任务轨迹能稳定验证后，再构建 episodic/procedural memory。
7. 多模态和 learned controller 放在高级研究路线，不作为默认生产依赖。

## 14. 一页速记

```text
先问：这是不是当前状态，而不是长期记忆？
再问：谁说的、能否验证、属于谁、保留多久、谁能删？

基础栈：message log + summary + structured facts + policy + audit + eval
非结构化宽召回：vector
时间关系与多跳：temporal graph + hybrid retrieval
失败教训：verified episodic reflection
可复用流程：versioned skill library

权限、tenant、过期、deleted 是硬过滤。
模型摘要和反思都是候选证据，不是天然事实。
删除必须验证主库、索引、图、缓存和同义词召回。
任何新增记忆方法都必须用 ablation 证明增量价值。
```

## 15. 预习核对清单

- [ ] 能区分 Runtime State、Working Context、Session History、Long-term Memory 和 RAG。
- [ ] 能解释 semantic、episodic、procedural、resource、relation memory。
- [ ] 能为候选记忆填写 source、scope、classification、TTL、version 和 delete policy。
- [ ] 能说明 vector、summary、hierarchical、graph 和 skill memory 的适用与禁用条件。
- [ ] 能设计模型猜测、Secret、跨租户、过期、冲突和删除测试。
- [ ] 能用 ablation 比较质量、成本、延迟和安全风险。
- [ ] 能说明论文结果、项目自报和生产 SLA 的证据等级不同。

## 16. 一手资料

### 基础与代表方法

- [OpenAI Agents SDK Sessions 官方文档](https://openai.github.io/openai-agents-python/sessions/)
- [OpenAI Session Memory Cookbook](https://developers.openai.com/cookbook/examples/agents_sdk/session_memory)
- [RAG（2020）](https://arxiv.org/abs/2005.11401)
- [Generative Agents（2023）](https://arxiv.org/abs/2304.03442)
- [Reflexion（2023）](https://arxiv.org/abs/2303.11366)
- [Voyager（2023）](https://arxiv.org/abs/2305.16291)
- [MemoryBank（2023）](https://arxiv.org/abs/2305.10250)
- [MemGPT（2023）](https://arxiv.org/abs/2310.08560)
- [Letta Memory Blocks 官方文档](https://docs.letta.com/guides/core-concepts/memory/memory-blocks/)
- [Zep / Graphiti（2025）](https://arxiv.org/abs/2501.13956)
- [Graphiti 官方仓库](https://github.com/getzep/graphiti)
- [A-MEM（2025）](https://arxiv.org/abs/2502.12110)
- [HippoRAG（2024）](https://arxiv.org/abs/2405.14831)
- [HippoRAG 2（2025）](https://arxiv.org/abs/2502.14802)
- [Mem0（2025）](https://arxiv.org/abs/2504.19413)
- [MemoryOS（2025）](https://arxiv.org/abs/2506.06326)
- [MIRIX（2025）](https://arxiv.org/abs/2507.07957)
- [LangMem 官方概念指南](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/)

### 评测与 2026 前沿

- [LoCoMo（2024）](https://arxiv.org/abs/2402.17753)
- [LongMemEval 官方仓库](https://github.com/xiaowu0162/longmemeval)
- [LongMemEval-V2（2026，Work in Progress）](https://arxiv.org/abs/2605.12493)
- [MemoryAgentBench（ICLR 2026）](https://openreview.net/forum?id=DT7JyQC3MR)
- [Graph-based Agent Memory Survey（2026）](https://arxiv.org/abs/2602.05665)
- [Memory for Autonomous LLM Agents Survey（2026）](https://arxiv.org/abs/2603.07670)
- [Agent Memory Systems Characterization（2026）](https://arxiv.org/abs/2606.06448)

## 17. 仍未知或需要独立验证的部分

- 多数论文没有公开长期多租户、真实删除请求和合规审计的完整结果。
- 厂商或项目自报 benchmark 需要独立复现，不能直接比较不同模型、judge 和数据版本的数字。
- 图记忆在高频增量更新、实体消歧错误和权限过滤下的长期退化仍缺统一公开基准。
- 多模态持续采集的隐私、成本和删除传播仍是开放问题。
- Learned memory controller 在分布外环境中的稳定性和安全性仍需长期证据。
