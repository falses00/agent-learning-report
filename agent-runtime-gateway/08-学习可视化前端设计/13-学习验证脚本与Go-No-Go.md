# 学习验证脚本与 Go/No-Go

日期：2026-07-02  
状态：v0.4-pre 原型前资产  
用途：验证可视化是否真的帮助用户理解工业级 Agent/RAG，而不是只验证视觉效果

## 1. 核心原则

原型通过与否，不看“好不好看”，先看学习者是否能复述：

```text
事故
负责层
最小验收证据
```

复述评分低于 3，不能进入下一阶段。

## 2. 两层门禁

本文件同时服务两个阶段，不能把它们混在一起。

### 2.1 原型前脚本完整性门禁

进入 Product Design 可点击原型前，只检查脚本是否完整，不要求学习者已经完成看图后评分。

必须满足：

- 每个 P0 验证主题都有页面、看图前问题、坏设计判断题和过关标准。
- 每个问题都能绑定事故、负责层和最小验收证据。
- 每个低分结果都有回流对象。
- RAG 三类问题：找不到、找错租户、引用不可信，都有 mock、eval case、复述题和低分回流。
- 没有真实退款、真实发布、真实凭据或生产系统入口。

### 2.2 原型后学习效果门禁

Product Design 可点击原型完成后，每个测试主题再按同一流程验证：

1. 看图前提问。
2. 记录 0-5 分。
3. 展示对应页面或线框。
4. 让学习者再次回答同一问题。
5. 追加一个坏设计判断题。
6. 记录提升、缺失项和回流对象。
7. 判断是否进入静态前端 / Implementation-later。

## 3. 评分规则

| 分数 | 含义 | 是否过关 |
|---|---|---|
| 0 | 完全说不出，或把 mock 当生产系统 | 不过 |
| 1 | 只背术语，不能解释事故 | 不过 |
| 2 | 能说大概意思，但缺负责层或证据 | 不过 |
| 3 | 能说出事故、负责层、最小验收证据 | 过关下限 |
| 4 | 能补充失败路径和停止条件 | 通过 |
| 5 | 能主动指出设计风险和工程门禁 | 优秀 |

## 4. P0 验证主题

| 主题 | 页面 | 看图前问题 | 坏设计判断题 | 过关标准 |
|---|---|---|---|---|
| 建议与执行分离 | C 首页 / A 链路 | 为什么模型建议不能直接退款？ | 如果模型建议直接调用退款工具，会怎样？ | 说出越权退款、Gateway/Policy、mock 边界 |
| Runtime 状态 | A 链路 / Trace | 为什么聊天记录不是状态？ | 工具失败后只靠聊天记录能恢复吗？ | 说出 Run/Step/Checkpoint |
| Tool Gateway | A 链路 | ToolCall 为什么不是执行？ | 缺 Tool Gateway 会发生什么？ | 说出申请、策略判断、audit |
| 长线任务 | B 事故 | retry 为什么可能重复退款？ | 没有 operation_id 会怎样？ | 说出幂等、checkpoint、阻塞 |
| RAG 找不到 | RAG 诊断器 | 为什么 RAG 找不到不是简单加 top_k？ | 召回不到关键政策时能直接回答吗？ | 说出 hard retrieval recall、query rewrite、EvalCase |
| RAG 找错租户 | RAG 诊断器 | 为什么找错租户必须阻塞？ | 检索到其他租户合同能发布吗？ | 说出 tenant ACL、Policy/Tool Gateway/RAG、release blocking |
| RAG 引用可信 | RAG 诊断器 | 为什么检索命中不等于可信答案？ | 引用未审核来源能发布吗？ | 说出 citation、freshness、EvalCase |
| 记忆污染 | 记忆生命周期 | 长期记忆为什么不能随便写？ | 错误事实写入后会怎样？ | 说出写入门禁、TTL、撤销、audit |
| Eval 门禁 | Eval 页 | eval 为什么不是分数装饰？ | red team 失败能上线吗？ | 说出 release blocking |
| Trace/Audit | Trace 页 | trace 和 audit 有什么不同？ | 事故后只有日志够吗？ | 说出定位和证明 |
| 沙箱风险 | 沙箱页 | 为什么 Docker 不是万能边界？ | 网络外发工具怎么处理？ | 说出工具风险、approval、audit |
| 多 Agent 协同 | 多 Agent 页 | 多 Agent 为什么不按投票合并？ | 两个 agent 同改一文件怎么办？ | 说出角色边界、停止条件、证据合并 |
| LLM-Wiki 知识层 | 知识层页 | 为什么 GitHub 热门资料不能直接进课程？ | license 不明能复制到课程里吗？ | 说出 SourceReview、KnowledgeCard、KnowledgeVersion |

## 5. Go / No-Go 标准

### 5.1 原型前 Go

满足全部条件才进入 Product Design 可点击原型：

- 13 个 P0 验证主题都有页面、问题、坏设计判断题、过关标准和低分回流。
- RAG 三类问题：找不到、找错租户、引用不可信，都有 mock、eval case、复述题和低分回流。
- 每个主题都能绑定事故、负责层和最小验收证据。
- 任一高风险误读没有出现：真实退款、真实发布、真实凭据、生产系统。
- Product Design brief、状态矩阵、mock 数据字典和逐页验收脚本都可互相追溯。

### 5.2 原型后 Go

满足全部条件才进入静态前端 / Implementation-later：

- P0 主题至少 11/13 个看图后评分 >=3。
- RAG 三类问题：找不到、找错租户、引用不可信，全部评分 >=3。
- 任一高风险误读没有出现：真实退款、真实发布、真实凭据、生产系统。
- 低分项都有明确回流对象。
- 用户能用中文说出当前 Phase、事故、负责层和证据。

### 5.3 Conditional Go

可以进入小范围原型，但必须先修复：

- 只有 1-2 个主题低于 3。
- 低分集中在术语解释，而不是系统边界。
- 原型没有生产误读风险。

修复动作：

- 改写 Concept。
- 补 FailureCase。
- 补 EvalCase。
- 重写 RestatementCard。
- 更新页面状态矩阵。

### 5.4 No-Go

出现任一情况，原型前不进入 Product Design；原型后不进入静态前端 / Implementation-later：

- 学习者把页面当成生产控制台。
- 学习者连续两次无法说出事故、负责层和证据。
- RAG 仍被理解为“搜到就可信”。
- LLM-Wiki 仍被理解为“自动生成正确课程内容”。
- 低分没有回流对象。

## 6. 验证记录模板

```json
{
  "validation_id": "mock_validation_phase_03_gateway_001",
  "topic": "Tool Gateway / Policy",
  "before_score": 1,
  "after_score": 3,
  "question": "ToolCall 为什么不是执行？",
  "missing_before": ["事故", "负责层", "证据"],
  "missing_after": [],
  "accident": "越权退款",
  "responsible_layer": "Tool Gateway / Policy",
  "evidence": "ToolCall 申请、PolicyDecision、AuditEvent",
  "go_no_go": "go",
  "actual_feedback_targets": [],
  "feedback_targets_if_low_score": ["Concept", "FailureCase", "EvalCase", "RestatementCard"],
  "source_files": [
    "08-学习可视化前端设计/11-页面状态矩阵与逐页验收脚本.md"
  ]
}
```

## 7. 下一轮执行提示词

```text
请作为 verifier subagent，只读检查 v0.4-pre 原型前冻结包。
检查 13 个 P0 验证主题是否都有页面、问题、坏设计判断题、过关标准和低分回流。
检查是否存在生产误读风险。
输出 P0/P1/P2 发现、证据文件路径和建议修复。
不要编辑文件。
```
