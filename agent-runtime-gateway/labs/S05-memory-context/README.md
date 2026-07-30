# S5 实验：受治理的 Agent Memory

一句话定义：Agent Memory 是把有来源、有限作用域、有限期限且可撤销的信息，经确定性写入门禁保存并按权限召回的外部状态系统，而不是“把所有聊天记录永久塞进向量库”。

## 1. 学习主线与边界

本实验沿用 OpsPilot 企业工单 Agent，完成一条可运行的记忆生命周期：

```text
candidate
  -> source / sensitivity / scope / TTL write gate
  -> canonical record + derived index + audit
  -> tenant / principal / resource ACL hard filter
  -> token-budgeted context pack
  -> versioned correction or TTL expiry
  -> tombstone + de-index + retrieval verification
```

实现入口：

- `../../20-源码/agent_course/memory.py`
- `../../20-源码/agent_course/memory_evals.py`
- `../../20-源码/agent_course/cli.py`
- `../../21-测试/test_memory.py`
- `../../22-评测集/memory-engineering-baseline.jsonl`

这是确定性的单进程 SQLite 教学基线。它真实证明 write gate、受信成员/资源策略、tenant/user/resource 边界、TTL、版本化纠正、删除传播、上下文预算、持久化重开和 fail-closed eval；它没有实现真实身份认证 adapter、embedding、知识图谱、分布式 worker、加密/KMS、备份擦除、法务留存或云产品 SLA。

## 2. 先分清五个对象

| 对象 | 负责什么 | 生命周期 | 不能替代什么 |
|---|---|---|---|
| Runtime state | 当前任务步骤、审批和工具结果 | 一个 run，可 checkpoint | 长期用户事实 |
| Working context | 当前模型本轮能看到的有限内容 | 一次调用或一个短会话 | 权威存储与审计 |
| Session history / summary | 会话消息和压缩后的主线 | 一个或多个相邻 session | 经过核验的业务事实 |
| Long-term memory | 跨会话仍有价值的偏好、事件和经验 | 有 TTL、版本和删除策略 | 企业知识库 |
| RAG knowledge | 有发布流程的政策、文档和业务知识 | 文档版本生命周期 | 用户画像和任务经验 |

判断顺序固定为：先问“它是不是当前状态”，再问“谁说的、属于谁、保留多久、谁能看、谁能删”。

## 3. 七个关键概念

| 概念 | 原理 | 缺少时的事故 | 本实验如何验收 |
|---|---|---|---|
| Candidate vs record | 模型抽取结果先是候选，过门禁后才是事实记录 | 模型猜测永久污染 | `model_inference` 返回 `deny`，主库与索引均为 0 |
| Provenance | 保存 source kind、source ref、时间和置信度 | 无法解释或纠错 | 每次 allow/deny/search/delete 都有 reason code audit |
| Scope and ACL | tenant membership、admin 与 resource grant 来自受信策略，并在相关性前硬过滤 | 伪造 tenant 或自授 subject 越权 | forged tenant 必须 deny；只知道 subject ID 不算授权 |
| TTL and validity | `created_at`、`valid_from/to`、`expires_at` 分开表达 | 过期政策继续影响决策 | 到期后主记录失效、派生索引删除并记录 audit |
| Versioned update | 新事实结束旧版本有效区间，不静默覆盖历史 | 无法回答“当时为什么这样做” | current 返回新值，history 保留 supersedes 链 |
| Tombstone delete | 硬删除 subject 版本链与派生索引，只保留最小删除证明 | 旧版本或派生副本仍可达 | 被删 memory ID、subject 和内容在 exact/paraphrase/ID 查询中都不出现 |
| Context budget | 只打包授权、相关且完整的记录 | token 失控或事实被截断误读 | 超预算记录被跳过，不截断半条事实 |

## 4. 先复现失败，再看修复

阅读[失败注入](failure.md)，重点观察四类不能被平均分掩盖的事故：

1. 模型猜测或文档注入被晋升为长期事实。
2. ACL 在相似度检索之后执行，泄漏其他租户候选。
3. 删除只改主表，向量/缓存/摘要仍能召回。
4. 过期记录仍占据 context budget，挤掉当前事实。

运行完整生命周期演示：

```powershell
cd "agent-runtime-gateway\20-源码"
python -m agent_course.cli memory-demo --db "$env:TEMP\opspilot-s5-memory.db" --reset
```

必须看到：

- 明确语言偏好 `decision == "allow"`。
- 模型猜测 `decision == "deny"`。
- Secret 候选 `decision == "deny_and_redact"`，且 `sensitive_value_persisted == false`。
- 跨租户检索 `decision == "deny"`。
- 删除后 `record_count == 0`、`index_count == 0`、`tombstone_count == 1`。

不带 `--reset` 重跑同一数据库应返回 `MEMORY_DB_EXISTS` 和退出码 2，防止演示静默覆盖已有证据。

## 5. 三类验证

```powershell
python -m pytest ..\21-测试\test_memory.py -q
python -m agent_course.cli memory-eval ..\22-评测集\memory-engineering-baseline.jsonl
```

| 类型 | 代表场景 | 必须看到 |
|---|---|---|
| 正常 | 明确偏好、受控 CRM 事实、版本更新、数据库重开 | 写入有来源，当前值正确，历史可解释，重启后仍可召回 |
| 失败 | TTL 到期、删除、超出 context budget | 过期/删除记录不可达，半条事实不进入 prompt |
| 对抗 | 模型猜测、Secret/PII、跨租户、资源越权、持久化注入 | critical case 为 0 泄漏，未知断言与未知字段 fail closed |

当前 JSONL 基线包含 18 个独立 case。每个 case 使用独立临时 SQLite；`setup` 可以写入、重开数据库、推进时钟，再执行 search/update/delete/expire/eval。任何 Secret 原值落盘、伪造租户成功、自授资源成功、重复 add 产生双当前值、目标记忆删除后仍可达或未知 assertion 被忽略，都必须阻塞发布。

授权事实不从模型或请求 payload 推断。`MemoryAccessPolicy` 是应用认证/Policy Gateway 传入的教学 fixture；生产接入必须用认证主体、服务端租户成员关系和资源 ACL 构造它，不能把前端传来的 `tenant_id`、`is_tenant_admin` 或 `allowed_subject_ids` 原样当真。

## 6. 方法选择：从最小栈升级

| 需求 | 首选 | 何时升级 | 主要代价 |
|---|---|---|---|
| 当前任务 | recent turns + trimming | 跨 session 才加 summary | 旧细节丢失 |
| 长会话主线 | versioned summary | 需要原句时保留 source window | 有损压缩与漂移 |
| 明确偏好/业务事实 | structured fact store | 非结构化规模大再加 vector | schema 与冲突治理 |
| 宽召回 | vector + metadata + rerank | 多跳/时间关系被基线证明后加 graph | 相似不等于真实 |
| 动态关系 | temporal graph + hybrid | 只有实体关系和历史查询有刚需 | 消歧、图增长、ACL 复杂 |
| 失败经验 | verified episodic reflection | 稳定复现后晋升 procedural skill | 错误反思会放大 |
| 可复用流程 | versioned skill library | 绑定环境版本、沙箱和测试后启用 | 旧技能可能危险 |
| 多模态资源 | minimal capture + resource index | 收益覆盖隐私和存储预算后扩展 | 采集、对齐和删除困难 |

SimpleMem 的结构化压缩适合学习“减少冗余但保留可用信息”；ReMe 适合学习经验蒸馏、改写和剪枝；Hindsight 适合学习 retain/recall/reflect 与事实/belief 分离。它们是研究路线和设计参考，不是替代 ACL、TTL、删除与生产评测的捷径。

## 7. 常见易错点与修复

| 易错点 | 为什么错 | 修复与回归 |
|---|---|---|
| “模型置信度高就能写” | 置信度不是来源或授权 | 模型推断默认拒写；用户确认或受控工具验证后再晋升 |
| “tenant ID 对上就能读资源” | ID 和调用方自填 grant 都不是授权事实 | 先校验服务端 tenant membership，再用受信 resource grants 过滤 |
| “TTL 只在查询时过滤即可” | 派生索引继续增长和暴露候选 | 到期任务同步 de-index，并审计过期数量 |
| “删除一行就是删除” | embedding、图边、摘要和缓存仍可达 | tombstone + 全派生层传播 + exact/paraphrase/ID 验证 |
| “摘要更短所以一定更好” | 压缩会丢来源、冲突和少数关键事实 | 保留 source window、版本与压缩前后 coverage eval |
| “反思就是程序性记忆” | 反思仍是模型生成物 | 只有 verified experience 能创建 procedural memory |
| “记忆越多效果越好” | 噪声、延迟、隐私和迎合都会增长 | with/without memory ablation，同时看质量、成本和 critical risk |
| “长期一致就是正确” | 错误前提可能被记忆持续放大 | 加 false-premise 与 sycophancy case，允许拒答和修订 belief |

## 8. 五道自测

1. Runtime checkpoint 与长期 semantic memory 的责任边界是什么？
2. 为什么 `principal_id + tenant_id + subject_id` 仍不足以证明资源授权？
3. 模型总结“用户可能在金融行业”为什么不能凭 0.95 confidence 写入？
4. 用户删除偏好后，如何证明目标原文、同义表达、ID、整个版本链、派生索引和缓存都不可达，同时不误判其他合法相似记录？
5. 何时应从 structured fact + vector 升级 temporal graph 或 procedural memory？

答错时先定位误区属于来源、权限、时间、删除、上下文还是评测，再阅读对应测试名，重跑失败 case，并补一条能让错误实现稳定失败的 assertion。不要只背答案。

## 9. 一页速记清单

```text
一句话：候选信息经来源、权限、敏感度、作用域和期限门禁后，才可能成为可召回记录。
五层：working context / session summary / episodic events / semantic facts / procedural skills。
写入：candidate -> validate -> canonical record -> derived index -> audit。
召回：tenant -> principal/resource ACL -> deleted/TTL -> relevance -> context budget。
纠错：结束旧 validity，创建新版本，保留 provenance 与 supersedes。
删除：subject version chain + index + graph + summary/cache -> tombstone -> target ID/content/subject verify。
禁止：模型猜测、Secret/PII、untrusted instruction、无 TTL 的永久事实。
升级：先 structured fact；有宽召回再 vector；有关系/时间证据再 graph；经验通过回放才变 skill。
评测：recall、precision、staleness、conflict、privacy、isolation、deletion、cost、ablation。
发布：任一 critical 泄漏或删除失败都阻塞，不能被平均分抵消。
```

## 10. 通过与预习核对

- [ ] 能画出 state、context、session、memory、RAG 的边界图。
- [ ] 能解释 semantic、episodic、procedural、resource 和 temporal relation。
- [ ] `test_memory.py` 全部通过，并能解释至少一个失败路径。
- [ ] Memory eval `failed=0`、`critical_failed=0`、所有 assertions 通过。
- [ ] CLI 演示证明 Secret 原值不落盘、跨租户拒绝、删除后索引为 0。
- [ ] 能比较 summary、vector、hierarchical、graph、reflection、skill、SimpleMem、ReMe 和 Hindsight 的适用/禁用条件。
- [ ] 能说明本 SQLite 基线没有证明哪些生产能力。
- [ ] 工程证据按[证据清单](evidence/README.md)登记，不粘贴真实用户数据、凭据或内部日志。

岗位映射：Agent Runtime、数据治理、多租户 SaaS、隐私与删除、SQLite/索引、评测 runner、故障注入、ADR、生产边界答辩。

下一阶段预习：把本阶段 18 条 memory case 按 correctness、trajectory、security、regression 分层，准备解释为什么 critical failure 必须独立阻塞发布。

## 11. 一手资料与未来走向

- [OpenAI Session Memory Cookbook](https://developers.openai.com/cookbook/examples/agents_sdk/session_memory)：短期 session、trimming 与压缩基线。
- [Anthropic Compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)：服务端上下文压缩及其版本边界。
- [Mem0](https://arxiv.org/abs/2504.19413)、[Graphiti](https://github.com/getzep/graphiti)：产品化 memory layer 与 temporal graph 代表。
- [SimpleMem](https://arxiv.org/abs/2601.02553)、[ReMe](https://arxiv.org/abs/2512.10696)、[Hindsight](https://arxiv.org/abs/2512.12818)：结构化压缩、程序经验、retain/recall/reflect 新路线。
- [LongMemEval-V2](https://arxiv.org/abs/2605.12493)、[MemoryAgentBench](https://openreview.net/forum?id=DT7JyQC3MR)：环境经验与在线记忆能力评测。
- [EvoMemBench](https://arxiv.org/abs/2605.18421)、[MemSyco-Bench](https://arxiv.org/abs/2607.01071)、[PM-Bench](https://arxiv.org/abs/2607.12385)：持续演化、记忆迎合与未来承诺的新风险面。

证据支持的方向是：从单一 top-k 召回走向时间/实体/事件与来源，从“记住内容”走向可验证经验，从过去事实回忆扩展到未来意图管理。工程推断是 memory controller 将逐步承担写入晋升、冲突、前提核验和删除证明；但在独立复现、长期多租户和完整删除链路成熟前，不能宣称已获得“像人一样的永久记忆”。
