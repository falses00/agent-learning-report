# Mock 数据字典与样例包

日期：2026-07-02  
状态：v0.4-pre 原型前资产  
用途：给 Product Design 原型和后续前端实现提供统一 mock 数据对象

## 1. 数据原则

- 所有数据都是 mock，不接真实生产系统。
- 所有 ID 使用 `mock_` 前缀。
- 所有对象都要能追溯到 `source_files`。
- 高风险动作只能展示“查看申请”“模拟判断”“查看条件”，不能展示真实执行。
- 数据字段使用英文，界面文案使用中文优先双语。

## 2. 核心对象清单

| 对象 | 用途 | 首屏是否需要 |
|---|---|---|
| Phase | 阶段、当前任务、下一步 | 是 |
| LayerCard | 系统层解释、事故、证据 | 是 |
| FailureCase | 坏设计和事故链路 | 是 |
| RAGDiagnostic | RAG 问题、指标、优化、阻塞 | 是 |
| MemoryLifecycle | 写入、TTL、撤销、审计 | P1 |
| SandboxRisk | 工具风险、sandbox profile、审批 | P1 |
| MultiAgentHandoff | 多 Agent 输入输出和停止条件 | P1 |
| EnhancedPrompt | 原始问题到增强提示词 | 是 |
| SubagentTask | subagent 角色、权限、证据 | 是 |
| TraceEvent | mock run 的 span/event | P1 |
| AuditEvent | 可证明的审计事件 | P1 |
| EvalCase | 发布门禁 case | 是 |
| ReleasePacket | 版本组合和回滚计划 | P1 |
| RestatementRecord | 复述评分、缺失项、回流 | 是 |
| LearningBacklog | 卡点和下次复习 | 是 |
| KnowledgeSource | 外部来源登记 | 是 |
| SourceReview | 来源审核 | 是 |
| KnowledgeTopic | 知识主题树 | 是 |
| KnowledgeCard | 可审核知识卡 | 是 |
| KnowledgeVersion | 知识版本 | 是 |
| ImportQueue | 新资料和低分回流队列 | 是 |

## 3. 首页 mock

```json
{
  "phase": {
    "phase_id": "mock_phase_00_1",
    "title_zh": "Phase 0.1 半懂起步",
    "current_task": "理解建议不等于执行许可",
    "primary_action": "查看受控链路",
    "secondary_actions": ["查看事故样例", "查看复述卡"],
    "source_files": [
      "00-课程总览/开始这里-半懂版.md",
      "02-阶段教学手册/Phase-00.1-半懂起步教学手册.md"
    ]
  },
  "boundary_badges": [
    "学习模式 Learning mode",
    "模拟数据 Mock data",
    "不执行真实操作 No real execution",
    "来源文件 Source files"
  ],
  "learning_status": {
    "restatement_score": 2,
    "missing_parts": ["事故", "验收证据"],
    "next_action": "回看卡点"
  }
}
```

## 4. 全链路 mock

```json
{
  "flow_id": "mock_controlled_agent_flow_001",
  "story": "客户提交退款工单",
  "nodes": [
    {"id": "request_gateway", "label_zh": "请求网关", "label_en": "Request Gateway", "responsibility": "身份、租户、限流、路由"},
    {"id": "runtime", "label_zh": "运行时", "label_en": "Runtime", "responsibility": "Run、Step、State、Checkpoint"},
    {"id": "tool_gateway", "label_zh": "工具网关", "label_en": "Tool Gateway", "responsibility": "schema、权限、凭据、审计"},
    {"id": "policy", "label_zh": "策略", "label_en": "Policy", "responsibility": "allow / deny / approval"},
    {"id": "rag", "label_zh": "检索增强", "label_en": "RAG", "responsibility": "受控检索和证据"},
    {"id": "eval_gate", "label_zh": "评估门禁", "label_en": "Eval Gate", "responsibility": "阻塞高风险退化"}
  ],
  "bad_design_path": {
    "label": "模型建议直接触发退款",
    "accident": "越权退款",
    "missing_layers": ["tool_gateway", "policy", "audit"],
    "release_blocking": true
  },
  "source_files": [
    "01-产品需求与路线/学习可视化前端PRD.md",
    "08-学习可视化前端设计/08-v0.3低保真交互与页面流.md"
  ]
}
```

## 5. RAG 诊断 mock

```json
[
  {
    "rag_diagnostic_id": "mock_rag_not_found_001",
    "problem_label": "找不到",
    "symptom": "用户问的是退款政策，但检索结果没有命中关键政策文档",
    "diagnostic_metrics": ["hard_retrieval_recall", "query_rewrite_success_rate", "expected_doc_hit_rate"],
    "optimization_options": ["query rewrite", "hybrid search", "chunk boundary review"],
    "eval_case_id": "mock_eval_rag_not_found_refund_policy",
    "release_blocking": false,
    "responsible_layers": ["RAG", "Eval"],
    "restatement_question": "为什么 RAG 找不到不是简单加 top_k 就能解决？",
    "feedback_targets": ["RAGDiagnostic", "EvalCase", "RestatementCard"],
    "source_files": [
      "07-RAG问题诊断与优化/00-RAG索引.md",
      "22-评测集/RAG评测数据集设计.md"
    ]
  },
  {
    "rag_diagnostic_id": "mock_rag_cross_tenant_001",
    "problem_label": "找错租户",
    "symptom": "检索命中其他租户的合同或政策文档",
    "diagnostic_metrics": ["tenant_acl_violation_rate", "forbidden_citation_count", "policy_filter_coverage"],
    "optimization_options": ["tenant-scoped index", "policy filter before retrieval", "citation tenant check"],
    "eval_case_id": "mock_eval_cross_tenant_retrieval",
    "release_blocking": true,
    "responsible_layers": ["Policy", "Tool Gateway", "RAG", "Eval"],
    "restatement_question": "为什么找错租户必须阻塞发布？",
    "feedback_targets": ["FailureCase", "RAGDiagnostic", "EvalCase", "RestatementCard"],
    "source_files": [
      "07-RAG问题诊断与优化/00-RAG索引.md",
      "07-RAG问题诊断与优化/RAG安全多租户与数据治理.md",
      "22-评测集/RAG评测数据集设计.md"
    ]
  },
  {
    "rag_diagnostic_id": "mock_rag_untrusted_citation_001",
    "problem_label": "引用不可信",
    "symptom": "答案引用了未审核或过期来源",
    "diagnostic_metrics": ["citation_precision", "freshness_regression", "source_review_pass_rate"],
    "optimization_options": ["citation check", "freshness gate", "SourceReview before KnowledgeCard"],
    "eval_case_id": "mock_eval_untrusted_citation",
    "release_blocking": true,
    "responsible_layers": ["RAG", "Eval", "Governance"],
    "restatement_question": "为什么检索命中不等于可信答案？",
    "feedback_targets": ["KnowledgeCard", "SourceReview", "EvalCase", "RestatementCard"],
    "source_files": [
      "07-RAG问题诊断与优化/00-RAG索引.md",
      "08-学习可视化前端设计/09-LLM-Wiki知识层与可维护扩展方案.md"
    ]
  }
]
```

## 6. LLM-Wiki 知识层 mock

```json
{
  "knowledge_source": {
    "source_id": "mock_source_karpathy_llm_wiki_20260702",
    "title": "LLM Wiki Pattern",
    "url": "https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f",
    "source_type": "gist",
    "license_status": "needs_review",
    "fetched_at": "2026-07-02",
    "adoption_mode": "pattern_only"
  },
  "source_review": {
    "review_id": "mock_review_karpathy_llm_wiki",
    "decision": "pattern_only",
    "review_status": "needs_review",
    "freshness_result": "manual_review_required",
    "copyright_risk": "medium",
    "translation_risk": "medium"
  },
  "knowledge_card": {
    "card_id": "mock_card_knowledge_card_is_not_truth",
    "title_zh": "知识卡不是事实本身",
    "review_status": "needs_review",
    "confidence_score": 0.84,
    "source_files": [
      "10-GitHub项目调研/LLM-Wiki知识层调研-2026-07-02.md"
    ]
  },
  "knowledge_version": {
    "version_id": "mock_kv_001",
    "semver": "0.1.0",
    "change_reason": "initial_prototype_mock",
    "created_at": "2026-07-02"
  },
  "import_queue": {
    "queue_id": "mock_import_queue_low_score_001",
    "trigger_type": "restatement_low_score",
    "status": "needs_source_review",
    "target_doc_path": "07-RAG问题诊断与优化/00-RAG索引.md"
  }
}
```

## 7. 复述与低分回流 mock

```json
{
  "restatement_record": {
    "record_id": "mock_restatement_phase_03_001",
    "phase": "phase-03",
    "question": "为什么 prompt 不能决定工具权限？",
    "answer": "用户自己的中文复述",
    "score": 2,
    "missing_parts": ["负责层", "验收证据"],
    "misconception_tags": ["prompt_controls_permission"],
    "feedback_targets": ["Concept", "FailureCase", "EvalCase", "RestatementCard"]
  },
  "learning_backlog": {
    "backlog_id": "mock_backlog_gateway_policy_001",
    "title": "重讲 Tool Gateway / Policy 边界",
    "priority": "high",
    "next_review_at": "next_session",
    "recommended_subagent": "reviewer"
  }
}
```

## 8. Mock 数据验收

进入原型前检查：

- 每个对象有稳定 ID。
- 每个页面至少引用一个 `source_files`。
- 所有高风险状态有 `release_blocking` 或阻塞说明。
- 所有低分状态有 `feedback_targets`。
- 所有外部来源有 `license_status` 和 `adoption_mode`。
- 所有知识卡有 `review_status`。

## 9. 页面级最小 page_mock

Product Design 首轮原型可以不展开所有复杂细节，但每个页面都必须有一个最小 `page_mock`，避免自行脑补。

```json
[
  {
    "page_id": "page_home_route_map",
    "page_name_zh": "C 首页 / 学习路线地图",
    "phase": "phase-00.1",
    "boundary_badges": ["学习模式 Learning mode", "模拟数据 Mock data", "不执行真实操作 No real execution", "来源文件 Source files"],
    "accident": "模型建议直接变成退款执行",
    "responsible_layers": ["Request Gateway", "Policy"],
    "source_files": ["00-课程总览/开始这里-半懂版.md", "08-学习可视化前端设计/08-v0.3低保真交互与页面流.md"],
    "default_state": "显示当前 Phase、今日任务、主行动和卡点",
    "bad_design_state": "把继续下一阶段作为主按钮，但用户复述低分",
    "restatement_question": "为什么 Agent 的建议不等于系统执行许可？",
    "low_score_feedback_targets": ["Concept", "FailureCase", "RestatementCard"]
  },
  {
    "page_id": "page_layered_flow",
    "page_name_zh": "A 全链路分层控制台",
    "phase": "phase-03",
    "boundary_badges": ["学习模式 Learning mode", "模拟数据 Mock data", "不执行真实操作 No real execution", "来源文件 Source files"],
    "accident": "绕过 Tool Gateway 和 Policy 导致越权工具调用",
    "responsible_layers": ["Tool Gateway", "Policy", "Audit"],
    "source_files": ["01-产品需求与路线/学习可视化前端PRD.md", "08-学习可视化前端设计/11-页面状态矩阵与逐页验收脚本.md"],
    "default_state": "显示正常受控链路",
    "bad_design_state": "显示模型建议直接调用工具",
    "restatement_question": "为什么 ToolCall 是申请，不是执行？",
    "low_score_feedback_targets": ["LayerCard", "FailureCase", "EvalCase", "RestatementCard"]
  },
  {
    "page_id": "page_failure_lab",
    "page_name_zh": "B 事故推演工作台",
    "phase": "phase-04",
    "boundary_badges": ["学习模式 Learning mode", "模拟数据 Mock data", "不执行真实操作 No real execution", "来源文件 Source files"],
    "accident": "retry 重复退款",
    "responsible_layers": ["Runtime", "Tool Gateway", "Policy"],
    "source_files": ["08-学习可视化前端设计/08-v0.3低保真交互与页面流.md"],
    "default_state": "默认聚焦重复退款",
    "bad_design_state": "缺 operation_id，重试产生重复副作用",
    "restatement_question": "为什么 retry 不能重复副作用？",
    "low_score_feedback_targets": ["FailureCase", "EvalCase", "RestatementCard"]
  },
  {
    "page_id": "page_rag_diagnostic",
    "page_name_zh": "RAG 问题诊断器",
    "phase": "phase-07",
    "boundary_badges": ["学习模式 Learning mode", "模拟数据 Mock data", "不执行真实操作 No real execution", "来源文件 Source files"],
    "accident": "检索命中但引用不可信或跨租户",
    "responsible_layers": ["RAG", "Policy", "Eval"],
    "source_files": ["07-RAG问题诊断与优化/00-RAG索引.md", "22-评测集/RAG评测数据集设计.md"],
    "default_state": "显示找不到、找错租户、引用不可信三类问题",
    "bad_design_state": "把检索命中当作可信答案",
    "restatement_question": "为什么检索命中不等于可信答案？",
    "low_score_feedback_targets": ["RAGDiagnostic", "EvalCase", "KnowledgeCard", "RestatementCard"]
  },
  {
    "page_id": "page_memory_lifecycle",
    "page_name_zh": "记忆生命周期",
    "phase": "phase-06",
    "boundary_badges": ["学习模式 Learning mode", "模拟数据 Mock data", "不执行真实操作 No real execution", "来源文件 Source files"],
    "accident": "错误客户事实长期污染",
    "responsible_layers": ["Memory", "Policy", "Audit"],
    "source_files": ["02-阶段教学手册/Phase-06-记忆系统教学手册.md"],
    "default_state": "候选记忆 -> 写入门禁 -> TTL -> 撤销 -> audit",
    "bad_design_state": "自动写长期记忆且不可撤销",
    "restatement_question": "为什么长期记忆必须可撤销、可过期、可审计？",
    "low_score_feedback_targets": ["Concept", "FailureCase", "RestatementCard"]
  },
  {
    "page_id": "page_sandbox_risk",
    "page_name_zh": "沙箱与工具风险",
    "phase": "phase-09",
    "boundary_badges": ["学习模式 Learning mode", "模拟数据 Mock data", "不执行真实操作 No real execution", "来源文件 Source files"],
    "accident": "高风险工具造成文件、网络或凭据外泄",
    "responsible_layers": ["Sandbox", "Tool Gateway", "Credential Broker", "Audit"],
    "source_files": ["02-阶段教学手册/Phase-09-安全隔离与沙箱教学手册.md"],
    "default_state": "显示工具风险矩阵和 sandbox profile",
    "bad_design_state": "把 Docker 当成万能边界",
    "restatement_question": "为什么高风险工具要按风险选择隔离和审批？",
    "low_score_feedback_targets": ["FailureCase", "EvalCase", "RestatementCard"]
  },
  {
    "page_id": "page_multi_agent_handoff",
    "page_name_zh": "多 Agent 协同",
    "phase": "phase-10",
    "boundary_badges": ["学习模式 Learning mode", "模拟数据 Mock data", "不执行真实操作 No real execution", "来源文件 Source files"],
    "accident": "两个 agent 同时修改同一资源导致冲突",
    "responsible_layers": ["Orchestrator", "Reviewer", "Verifier"],
    "source_files": ["02-阶段教学手册/Phase-10-多智能体协同教学手册.md"],
    "default_state": "planner -> executor -> reviewer -> verifier",
    "bad_design_state": "多 Agent 按投票合并而不是按证据合并",
    "restatement_question": "为什么多 Agent 分歧要按证据合并？",
    "low_score_feedback_targets": ["Concept", "FailureCase", "RestatementCard"]
  },
  {
    "page_id": "page_codex_collaboration",
    "page_name_zh": "Codex 协作与提示词增强轨道",
    "phase": "all",
    "boundary_badges": ["学习模式 Learning mode", "模拟数据 Mock data", "不执行真实操作 No real execution", "来源文件 Source files"],
    "accident": "没有明确 subagent 边界导致资料无来源或编辑冲突",
    "responsible_layers": ["Main Thread", "Subagent", "Review"],
    "source_files": ["README.md", "08-学习可视化前端设计/08-v0.3低保真交互与页面流.md"],
    "default_state": "原始问题 -> 增强提示词 -> 推荐 subagent -> 期望证据",
    "bad_design_state": "让多个 agent 编辑同一文件且不设停止条件",
    "restatement_question": "什么时候该调用 researcher / reviewer / verifier？",
    "low_score_feedback_targets": ["EnhancedPrompt", "SubagentTask", "RestatementCard"]
  },
  {
    "page_id": "page_llm_wiki_layer",
    "page_name_zh": "LLM-Wiki 知识层",
    "phase": "phase-07",
    "boundary_badges": ["学习模式 Learning mode", "模拟数据 Mock data", "不执行真实操作 No real execution", "来源文件 Source files"],
    "accident": "未审核外部资料直接进入课程",
    "responsible_layers": ["SourceReview", "KnowledgeCard", "KnowledgeVersion"],
    "source_files": ["08-学习可视化前端设计/09-LLM-Wiki知识层与可维护扩展方案.md", "10-GitHub项目调研/LLM-Wiki知识层调研-2026-07-02.md"],
    "default_state": "ImportQueue -> SourceReview -> KnowledgeCard -> KnowledgeVersion",
    "bad_design_state": "GitHub star 高就直接复制到课程",
    "restatement_question": "为什么知识卡不是事实本身？",
    "low_score_feedback_targets": ["ImportQueue", "SourceReview", "KnowledgeCard", "RestatementCard"]
  },
  {
    "page_id": "page_trace_audit",
    "page_name_zh": "Trace / Audit 回放",
    "phase": "phase-08",
    "boundary_badges": ["学习模式 Learning mode", "模拟数据 Mock data", "不执行真实操作 No real execution", "来源文件 Source files"],
    "accident": "事故后无法定位或证明责任",
    "responsible_layers": ["Observability", "Audit"],
    "source_files": ["02-阶段教学手册/Phase-08-可观测性与审计教学手册.md"],
    "default_state": "mock run 时间线和 trace/audit 双栏",
    "bad_design_state": "只有日志，没有 audit event",
    "restatement_question": "trace 和 audit 有什么不同？",
    "low_score_feedback_targets": ["Concept", "TraceExample", "RestatementCard"]
  },
  {
    "page_id": "page_eval_gate",
    "page_name_zh": "Eval 门禁",
    "phase": "phase-07",
    "boundary_badges": ["学习模式 Learning mode", "模拟数据 Mock data", "不执行真实操作 No real execution", "来源文件 Source files"],
    "accident": "平均分掩盖 red team 或跨租户失败",
    "responsible_layers": ["Eval", "Release Gate"],
    "source_files": ["02-阶段教学手册/Phase-07-测评审核与红队教学手册.md", "22-评测集/RAG评测数据集设计.md"],
    "default_state": "case 矩阵和 release blocking 判断",
    "bad_design_state": "只看总分，不看 critical failure",
    "restatement_question": "为什么 eval 是发布门禁，不是分数装饰？",
    "low_score_feedback_targets": ["EvalCase", "FailureCase", "RestatementCard"]
  },
  {
    "page_id": "page_release_simulation",
    "page_name_zh": "Release 学习模拟",
    "phase": "phase-11",
    "boundary_badges": ["学习模式 Learning mode", "模拟数据 Mock data", "不执行真实操作 No real execution", "来源文件 Source files"],
    "accident": "降低 eval set 后上线导致退化版本发布",
    "responsible_layers": ["Release Gate", "Governance", "Rollback"],
    "source_files": ["02-阶段教学手册/Phase-11-治理控制台与发布教学手册.md"],
    "default_state": "release packet、eval 重跑矩阵和 rollback 学习样例",
    "bad_design_state": "只发代码，不锁定 prompt/model/tool/policy/eval 版本",
    "restatement_question": "为什么发布是版本组合和证据包？",
    "low_score_feedback_targets": ["ReleasePacket", "EvalCase", "RestatementCard"]
  }
]
```
