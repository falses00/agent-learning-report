export type MaterialLink = {
  file: string;
  role: string;
  why: string;
  status: "ready" | "needs_review";
  target: string;
};

export type MaterialAtlasItem = MaterialLink & {
  caseIds: string[];
  topics: string[];
  phases: string[];
  usageCount: number;
};

export type SystemRoute = {
  id: string;
  title: string;
  subtitle: string;
  goal: string;
  why: string;
  accident: string;
  responsibleLayers: string[];
  evidence: string[];
  caseIds: string[];
  qualityGates: string[];
};

export type LearningCase = {
  id: string;
  topic: string;
  page: string;
  phase: string;
  learningGoal: string;
  materialSummary: string;
  beforeQuestion: string;
  badDesignQuestion: string;
  accident: string;
  responsibleLayer: string;
  evidence: string;
  feedbackTargets: string[];
  sourceFiles: string[];
  materials: MaterialLink[];
  bridgeSteps: string[];
  reviewChecklist: string[];
  visual: "home" | "flow" | "incident" | "rag" | "wiki" | "evidence";
};

type LearningCaseSeed = Omit<LearningCase, "learningGoal" | "materialSummary" | "materials" | "bridgeSteps" | "reviewChecklist">;

const baseLearningCases: LearningCaseSeed[] = [
  {
    id: "v04_p0_001_suggestion_execution",
    topic: "建议与执行分离",
    page: "C 首页 / A 全链路",
    phase: "Phase 0.1",
    beforeQuestion: "为什么模型建议不能直接退款？",
    badDesignQuestion: "如果模型建议直接调用退款工具，会怎样？",
    accident: "越权退款",
    responsibleLayer: "Request Gateway / Policy / Tool Gateway",
    evidence: "学习边界、ToolCall 申请、PolicyDecision、AuditEvent",
    feedbackTargets: ["Concept", "FailureCase", "RestatementCard"],
    sourceFiles: ["00-课程总览/第一节课-用工单故事理解工业级Agent.md", "08-学习可视化前端设计/v0.4-低保真可点击原型/第1课逐题主持脚本.md"],
    visual: "home",
  },
  {
    id: "v04_p0_002_runtime_state",
    topic: "Runtime 状态",
    page: "A 全链路 / 证据与门禁",
    phase: "Phase 2",
    beforeQuestion: "为什么聊天记录不是任务状态？",
    badDesignQuestion: "工具失败后只靠聊天记录能恢复吗？",
    accident: "任务中断后无法恢复",
    responsibleLayer: "Runtime",
    evidence: "Run、Step、Checkpoint、trace_id",
    feedbackTargets: ["Concept", "FailureCase", "StateMatrix"],
    sourceFiles: ["02-阶段教学手册/Phase-02-最小运行时教学手册.md", "08-学习可视化前端设计/11-页面状态矩阵与逐页验收脚本.md"],
    visual: "flow",
  },
  {
    id: "v04_p0_003_tool_gateway",
    topic: "Tool Gateway",
    page: "A 全链路",
    phase: "Phase 3",
    beforeQuestion: "ToolCall 为什么不是执行？",
    badDesignQuestion: "缺 Tool Gateway 会发生什么？",
    accident: "模型直接调用危险工具",
    responsibleLayer: "Tool Gateway / Policy",
    evidence: "工具申请、策略判断、AuditEvent",
    feedbackTargets: ["Concept", "EvalCase", "RestatementCard"],
    sourceFiles: ["02-阶段教学手册/Phase-03-Agent网关与工具治理教学手册.md", "04-测评审核体系/测评审核体系.md"],
    visual: "flow",
  },
  {
    id: "v04_p0_004_long_running",
    topic: "长线任务",
    page: "B 事故",
    phase: "Phase 4",
    beforeQuestion: "retry 为什么可能重复退款？",
    badDesignQuestion: "没有 operation_id 会怎样？",
    accident: "重复副作用",
    responsibleLayer: "Runtime / Checkpoint",
    evidence: "operation_id、checkpoint、resume、blocked",
    feedbackTargets: ["FailureCase", "EvalCase", "StateMatrix"],
    sourceFiles: ["02-阶段教学手册/Phase-04-长线任务与断点恢复教学手册.md", "06-工业级框架蓝图/长线运行可靠性设计.md"],
    visual: "incident",
  },
  {
    id: "v04_p0_005_rag_missing",
    topic: "RAG 找不到",
    page: "RAG 诊断器",
    phase: "Phase 7",
    beforeQuestion: "为什么 RAG 找不到不是简单加 top_k？",
    badDesignQuestion: "召回不到关键政策时能直接回答吗？",
    accident: "缺关键政策仍胡答",
    responsibleLayer: "Retrieval / Eval",
    evidence: "hard retrieval case、query rewrite、recall 指标",
    feedbackTargets: ["RAGCase", "EvalCase", "RestatementCard"],
    sourceFiles: ["07-RAG问题诊断与优化/00-RAG索引.md", "22-评测集/RAG评测数据集设计.md"],
    visual: "rag",
  },
  {
    id: "v04_p0_006_rag_wrong_tenant",
    topic: "RAG 找错租户",
    page: "RAG 诊断器",
    phase: "Phase 7",
    beforeQuestion: "为什么找错租户必须阻塞？",
    badDesignQuestion: "检索到其他租户合同能发布吗？",
    accident: "跨租户数据泄漏",
    responsibleLayer: "Policy / RAG / Tool Gateway",
    evidence: "tenant ACL、blocked case、audit event",
    feedbackTargets: ["RAGCase", "PolicyCase", "EvalCase"],
    sourceFiles: ["07-RAG问题诊断与优化/RAG教学路线总览.md", "04-测评审核体系/测评审核体系.md"],
    visual: "rag",
  },
  {
    id: "v04_p0_007_rag_citation_trust",
    topic: "RAG 引用可信",
    page: "RAG 诊断器",
    phase: "Phase 7",
    beforeQuestion: "为什么检索命中不等于可信答案？",
    badDesignQuestion: "引用未审核来源能发布吗？",
    accident: "引用错误或未审核来源",
    responsibleLayer: "Citation / SourceReview / Eval",
    evidence: "citation、freshness、source_files、EvalCase",
    feedbackTargets: ["CitationCase", "SourceReview", "EvalCase"],
    sourceFiles: ["07-RAG问题诊断与优化/RAG逐课教学手册.md", "08-学习可视化前端设计/09-LLM-Wiki知识层与可维护扩展方案.md"],
    visual: "rag",
  },
  {
    id: "v04_p0_008_memory_pollution",
    topic: "记忆污染",
    page: "证据与门禁 / Phase 6",
    phase: "Phase 6",
    beforeQuestion: "长期记忆为什么不能随便写？",
    badDesignQuestion: "错误事实写入后会怎样？",
    accident: "错误事实长期召回",
    responsibleLayer: "Memory Gate / Audit",
    evidence: "来源、TTL、撤销、audit event",
    feedbackTargets: ["MemoryGate", "FailureCase", "AuditCase"],
    sourceFiles: ["02-阶段教学手册/Phase-06-记忆系统教学手册.md", "04-测评审核体系/测评审核体系.md"],
    visual: "evidence",
  },
  {
    id: "v04_p0_009_eval_gate",
    topic: "Eval 门禁",
    page: "证据与门禁",
    phase: "Phase 7",
    beforeQuestion: "eval 为什么不是分数装饰？",
    badDesignQuestion: "red team 失败能上线吗？",
    accident: "退化版本发布",
    responsibleLayer: "Eval / Release Gate",
    evidence: "release blocking、eval case、regression set",
    feedbackTargets: ["EvalCase", "ReleaseGate", "BlockerRule"],
    sourceFiles: ["02-阶段教学手册/Phase-07-测评审核与红队教学手册.md", "04-测评审核体系/测评审核体系.md"],
    visual: "evidence",
  },
  {
    id: "v04_p0_010_trace_audit",
    topic: "Trace/Audit",
    page: "证据与门禁",
    phase: "Phase 8",
    beforeQuestion: "trace 和 audit 有什么不同？",
    badDesignQuestion: "事故后只有日志够吗？",
    accident: "事故后无法定位或证明",
    responsibleLayer: "Trace / Audit",
    evidence: "trace_id、span、audit event",
    feedbackTargets: ["TraceCase", "AuditCase", "ReplayQuestion"],
    sourceFiles: ["02-阶段教学手册/Phase-08-可观测性与审计教学手册.md", "04-测评审核体系/测评审核体系.md"],
    visual: "evidence",
  },
  {
    id: "v04_p0_011_sandbox_risk",
    topic: "沙箱风险",
    page: "证据与门禁 / Phase 9",
    phase: "Phase 9",
    beforeQuestion: "为什么 Docker 不是万能边界？",
    badDesignQuestion: "网络外发工具怎么处理？",
    accident: "高风险工具外发数据",
    responsibleLayer: "Sandbox / Approval / Audit",
    evidence: "工具风险等级、sandbox profile、approval",
    feedbackTargets: ["SandboxProfile", "ToolRiskCase", "ApprovalRule"],
    sourceFiles: ["02-阶段教学手册/Phase-09-安全隔离与沙箱教学手册.md", "04-测评审核体系/测评审核体系.md"],
    visual: "evidence",
  },
  {
    id: "v04_p0_012_multi_agent",
    topic: "多 Agent 协同",
    page: "证据与门禁 / Phase 10",
    phase: "Phase 10",
    beforeQuestion: "多 Agent 为什么不按投票合并？",
    badDesignQuestion: "两个 agent 同改一文件怎么办？",
    accident: "协同冲突或错误多数票",
    responsibleLayer: "Supervisor / Reviewer / Verifier",
    evidence: "handoff、resource lock、证据合并",
    feedbackTargets: ["HandoffCase", "ConflictCase", "ReviewerPrompt"],
    sourceFiles: ["02-阶段教学手册/Phase-10-多智能体协同教学手册.md", "04-测评审核体系/测评审核体系.md"],
    visual: "evidence",
  },
  {
    id: "v04_p0_013_llm_wiki",
    topic: "LLM-Wiki 知识层",
    page: "LLM-Wiki 知识层",
    phase: "Phase 7.5",
    beforeQuestion: "为什么 GitHub 热门资料不能直接进课程？",
    badDesignQuestion: "license 不明能复制到课程里吗？",
    accident: "未审核资料进入课程",
    responsibleLayer: "SourceReview / KnowledgeCard / KnowledgeVersion",
    evidence: "license_status、review_status、KnowledgeCard、source_files",
    feedbackTargets: ["SourceReview", "KnowledgeCard", "KnowledgeVersion"],
    sourceFiles: ["08-学习可视化前端设计/09-LLM-Wiki知识层与可维护扩展方案.md", "10-GitHub项目调研/LLM-Wiki知识层调研-2026-07-02.md"],
    visual: "wiki",
  },
];

export const learningCases: LearningCase[] = baseLearningCases.map((item) => ({
  ...item,
  learningGoal: `学会用“事故 -> 负责层 -> 最小证据”解释 ${item.topic}，并能判断坏设计为什么必须停下。`,
  materialSummary: buildMaterialSummary(item),
  materials: item.sourceFiles.map((file, index) => buildMaterialLink(file, item, index)),
  bridgeSteps: [
    `先读懂资料中的主问题：${item.beforeQuestion}`,
    `把页面视觉锚到事故：${item.accident}`,
    `用负责层定位拦截点：${item.responsibleLayer}`,
    `用最小证据完成复述：${item.evidence}`,
    `低分时回流到：${item.feedbackTargets.join(" / ")}`,
  ],
  reviewChecklist: [
    `能说出事故：${item.accident}`,
    `能指出负责层：${item.responsibleLayer}`,
    `能列出证据：${item.evidence}`,
    "没有把学习原型误读成真实生产控制台",
  ],
}));

export const materialAtlas: MaterialAtlasItem[] = buildMaterialAtlas(learningCases);

export const systemRoutes: SystemRoute[] = [
  {
    id: "agent-runtime",
    title: "Agent Runtime 主干",
    subtitle: "Run / Step / Checkpoint",
    goal: "把聊天请求变成可恢复、可审计、可暂停的长线任务。",
    why: "最好的 Agent 不是一个会回答的模型，而是一个能被网关、状态机、工具权限和评测约束的运行系统。",
    accident: "任务中断、重复副作用、建议被误当成执行。",
    responsibleLayers: ["Request Gateway", "Runtime", "Checkpoint", "Tool Gateway"],
    evidence: ["Run", "Step", "Checkpoint", "operation_id", "PolicyDecision"],
    caseIds: ["v04_p0_001_suggestion_execution", "v04_p0_002_runtime_state", "v04_p0_004_long_running"],
    qualityGates: ["建议和执行分离", "状态可恢复", "副作用有 operation_id"],
  },
  {
    id: "rag-system",
    title: "RAG 可信检索",
    subtitle: "Retrieval / Citation / Eval",
    goal: "让检索结果先经过权限、引用、freshness 和评测，再进入答案。",
    why: "最好的 RAG 不追求把文档都塞进去，而是能解释找不到、找错租户、引用不可信时该停在哪里。",
    accident: "缺关键政策仍胡答、跨租户泄漏、未审核来源被引用。",
    responsibleLayers: ["RAG", "Policy", "Citation", "SourceReview", "Eval"],
    evidence: ["tenant ACL", "citation", "freshness", "source_files", "hard retrieval case"],
    caseIds: ["v04_p0_005_rag_missing", "v04_p0_006_rag_wrong_tenant", "v04_p0_007_rag_citation_trust"],
    qualityGates: ["召回失败可诊断", "跨租户必须阻塞", "引用可追溯"],
  },
  {
    id: "memory-system",
    title: "记忆系统",
    subtitle: "Memory Gate / TTL / Audit",
    goal: "只把有来源、可撤销、可过期、可审计的信息写入长期记忆。",
    why: "最好的记忆系统不是记得越多越好，而是知道什么时候不能写、什么时候必须过期、谁能撤销。",
    accident: "错误事实长期召回，污染后续决策。",
    responsibleLayers: ["Memory Gate", "Policy", "Audit"],
    evidence: ["来源", "TTL", "撤销记录", "audit event"],
    caseIds: ["v04_p0_008_memory_pollution"],
    qualityGates: ["写入前审查", "TTL 可见", "撤销可证明"],
  },
  {
    id: "tool-policy",
    title: "工具与策略网关",
    subtitle: "Tool Gateway / Policy / Approval",
    goal: "把 ToolCall 当成申请，而不是执行，把危险工具放进策略和审批路径。",
    why: "模型不拥有工具权限。工具网关和策略层负责判断 allow、deny、approval，并留下审计证据。",
    accident: "模型直接调用危险工具或外发数据。",
    responsibleLayers: ["Tool Gateway", "Policy", "Approval", "Sandbox"],
    evidence: ["工具申请", "策略判断", "approval", "sandbox profile"],
    caseIds: ["v04_p0_003_tool_gateway", "v04_p0_011_sandbox_risk"],
    qualityGates: ["危险工具需审批", "凭据不进浏览器", "高风险工具隔离"],
  },
  {
    id: "eval-release",
    title: "评测与发布门禁",
    subtitle: "Eval / Red Team / Release Gate",
    goal: "让版本发布依赖关键 case、red team、回归集和证据包，而不是平均分。",
    why: "最好的发布流程会阻塞关键失败，锁定 prompt、model、tool、policy 和 eval 版本。",
    accident: "退化版本发布，平均分掩盖 critical failure。",
    responsibleLayers: ["Eval", "Release Gate", "Rollback"],
    evidence: ["eval case", "regression set", "release blocking", "rollback target"],
    caseIds: ["v04_p0_009_eval_gate"],
    qualityGates: ["critical failure 阻塞", "回归集重跑", "发布证据完整"],
  },
  {
    id: "trace-audit",
    title: "Trace / Audit 证据",
    subtitle: "Observability / Audit",
    goal: "把调试轨迹和合规审计分开记录，事故后能定位，也能证明。",
    why: "trace 解释系统怎么跑，audit 证明谁在何时允许了什么。两者缺一都无法复盘事故。",
    accident: "事故后无法定位或证明责任。",
    responsibleLayers: ["Trace", "Audit", "Observability"],
    evidence: ["trace_id", "span", "audit event"],
    caseIds: ["v04_p0_010_trace_audit"],
    qualityGates: ["trace 可回放", "audit 不可混同", "事故证据可导出"],
  },
  {
    id: "multi-agent",
    title: "多 Agent 协同",
    subtitle: "Planner / Reviewer / Verifier",
    goal: "用角色、资源边界和证据合并管理多 Agent，而不是让它们投票或抢同一文件。",
    why: "多 Agent 的价值来自分工和独立验证，不来自数量。主线程必须按证据合并结论。",
    accident: "协同冲突或错误多数票。",
    responsibleLayers: ["Supervisor", "Reviewer", "Verifier"],
    evidence: ["handoff", "resource lock", "证据合并"],
    caseIds: ["v04_p0_012_multi_agent"],
    qualityGates: ["文件所有权清楚", "按证据合并", "reviewer/verifier 独立"],
  },
  {
    id: "knowledge-governance",
    title: "知识治理",
    subtitle: "SourceReview / KnowledgeCard",
    goal: "让 GitHub、论文、课程和 LLM 总结先进入来源审核，再变成知识卡和版本。",
    why: "外部资料不能因为热门就进入课程。知识卡是可审核学习单元，不是事实本身。",
    accident: "未审核资料进入课程，license 或 freshness 风险被带入学习内容。",
    responsibleLayers: ["ImportQueue", "SourceReview", "KnowledgeCard", "KnowledgeVersion"],
    evidence: ["license_status", "review_status", "KnowledgeCard", "source_files"],
    caseIds: ["v04_p0_013_llm_wiki"],
    qualityGates: ["license 明确", "采用方式明确", "低分回流到知识卡"],
  },
];

function buildMaterialSummary(item: LearningCaseSeed) {
  if (item.visual === "rag") {
    return "这题从 RAG 诊断资料进入，重点不是检索技巧，而是问题类型、可信证据和发布阻塞条件。";
  }
  if (item.visual === "wiki") {
    return "这题从 LLM-Wiki 知识层进入，重点是外部资料必须经过来源审核、知识卡和版本记录。";
  }
  if (item.visual === "incident") {
    return "这题从事故推演进入，重点是把坏设计路径还原成可拦截、可审计、可复述的学习证据。";
  }
  if (item.visual === "flow") {
    return "这题从分层链路进入，重点是看清申请、判断、执行、记录分别属于哪一层。";
  }
  return "这题从学习路线图进入，重点是先建立边界意识，再进入具体链路和复述评分。";
}

function buildMaterialLink(file: string, item: LearningCaseSeed, index: number): MaterialLink {
  const role = describeSourceRole(file, index);
  const target = index === 0 ? item.feedbackTargets[0] : item.feedbackTargets[Math.min(index, item.feedbackTargets.length - 1)];
  return {
    file,
    role,
    why: `用于支撑“${item.topic}”中的 ${item.accident}、${item.responsibleLayer} 和 ${item.evidence}。`,
    status: file.includes("10-GitHub") || file.includes("LLM-Wiki") ? "needs_review" : "ready",
    target,
  };
}

function describeSourceRole(file: string, index: number) {
  if (file.includes("00-课程总览")) return "课程入口";
  if (file.includes("01-产品需求")) return "产品需求";
  if (file.includes("02-阶段教学手册")) return "阶段手册";
  if (file.includes("04-测评审核体系")) return "评测门禁";
  if (file.includes("06-工业级框架蓝图")) return "架构蓝图";
  if (file.includes("07-RAG")) return "RAG 教学";
  if (file.includes("08-学习可视化")) return "前端设计";
  if (file.includes("10-GitHub")) return "外部资料";
  if (file.includes("22-评测集")) return "评测集";
  return index === 0 ? "主资料" : "补充资料";
}

function buildMaterialAtlas(cases: LearningCase[]): MaterialAtlasItem[] {
  const atlas = new Map<string, MaterialAtlasItem>();

  cases.forEach((item) => {
    item.materials.forEach((material) => {
      const existing = atlas.get(material.file);
      if (existing) {
        existing.caseIds.push(item.id);
        existing.topics.push(item.topic);
        existing.phases = Array.from(new Set([...existing.phases, item.phase]));
        existing.usageCount += 1;
        if (material.status === "needs_review") existing.status = "needs_review";
        return;
      }

      atlas.set(material.file, {
        ...material,
        caseIds: [item.id],
        topics: [item.topic],
        phases: [item.phase],
        usageCount: 1,
      });
    });
  });

  return Array.from(atlas.values()).sort((a, b) => a.role.localeCompare(b.role, "zh-CN") || a.file.localeCompare(b.file, "zh-CN"));
}
