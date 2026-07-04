const p0Topics = [
  "建议与执行分离",
  "Runtime 状态",
  "Tool Gateway",
  "长线任务",
  "RAG 找不到",
  "RAG 找错租户",
  "RAG 引用可信",
  "记忆污染",
  "Eval 门禁",
  "Trace/Audit",
  "沙箱风险",
  "多 Agent 协同",
  "LLM-Wiki 知识层",
];

const pages = [
  {
    id: "home",
    nav: "C 首页",
    subtitle: "学习路线地图",
    phase: "Phase 0.1",
    title: "半懂起步：先知道自己在哪",
    summary: "用路线地图把当前任务、事故样例、复述分数和下一步放在同一屏，避免一上来被系统图压住。",
    primaryTitle: "学习路线地图",
    gate: "当前进行中",
    accident: "模型建议直接变成退款执行",
    accidentText: "如果学习者把模型建议当成执行许可，就会误以为 Agent 只是聊天窗口加按钮。",
    layers: ["Request Gateway", "Policy", "Learning Backlog"],
    evidence: ["学习模式边界条", "Phase 0.1 当前任务", "复述分 2/5", "source_files"],
    sourceFiles: ["00-课程总览/开始这里-半懂版.md", "08-学习可视化前端设计/14-v0.4低保真可点击原型Brief回放.md"],
    question: "为什么 Agent 的建议不等于系统执行许可？",
    feedbackTargets: ["Concept", "FailureCase", "RestatementCard"],
    topics: ["建议与执行分离", "多 Agent 协同"],
    rows: [
      ["学习目标", "理解建议和执行许可的区别，知道本阶段不是写代码。"],
      ["事故样例", "重复退款，模型建议如果绕过策略会造成越权。"],
      ["下一步", "查看受控链路，进入 A 全链路分层控制台。"],
      ["低分回流", "复述低于 3 分时，回到卡点标签和重讲任务。"],
    ],
    bad: "坏设计：复述分低于 3，页面仍然允许进入下一阶段。",
    low: "低分回流：重讲建议与执行分离，补一张失败案例卡，再做同一复述题。",
  },
  {
    id: "flow",
    nav: "A 全链路",
    subtitle: "分层控制台",
    phase: "Phase 3",
    title: "受控 Agent 链路：ToolCall 不是执行",
    summary: "用分层控制台展示请求、运行时、模型、工具、策略、RAG、Trace 和 Eval 如何共同约束一次长线任务。",
    primaryTitle: "系统分层链路",
    gate: "受控链路",
    accident: "绕过 Tool Gateway 和 Policy 导致越权工具调用",
    accidentText: "模型建议如果直接触发工具，就会跳过权限、凭据、审计和评测门禁。",
    layers: ["Runtime", "Tool Gateway", "Policy", "Audit", "Eval"],
    evidence: ["ToolCall 申请", "PolicyDecision", "AuditEvent", "EvalGate"],
    sourceFiles: ["01-产品需求与路线/学习可视化前端PRD.md", "08-学习可视化前端设计/11-页面状态矩阵与逐页验收脚本.md"],
    question: "为什么 ToolCall 是申请，不是执行？",
    feedbackTargets: ["LayerCard", "FailureCase", "EvalCase", "RestatementCard"],
    topics: ["Runtime 状态", "Tool Gateway", "沙箱风险", "Trace/Audit"],
    rows: [
      ["用户请求 User Request", "客户提交退款工单，系统只接收请求和租户上下文。"],
      ["运行时 Runtime", "记录 Run、Step、State、Checkpoint，支持恢复和审计。"],
      ["工具网关 Tool Gateway", "统一工具 schema、权限、凭据代理和审计入口。"],
      ["策略 Policy", "判断 allow / deny / approval，不能由 prompt 决定权限。"],
      ["评测门禁 Eval Gate", "关键退化或高风险 case 失败时阻塞发布学习模拟。"],
    ],
    bad: "坏设计：模型建议直接调用 refund.execute，缺少 Tool Gateway、Policy 和 Audit。",
    low: "低分回流：回看 ToolCall 申请、策略判断和 audit event 的区别。",
  },
  {
    id: "incident",
    nav: "B 事故",
    subtitle: "推演工作台",
    phase: "Phase 4",
    title: "重复退款事故：从失败倒推负责层",
    summary: "默认只聚焦一个事故，展示原因、链路、应拦截层和低分回流，帮助用户从失败路径理解治理价值。",
    primaryTitle: "事故推演工作台",
    gate: "需要阻塞",
    accident: "retry 重复退款",
    accidentText: "长线任务恢复时，如果没有 operation_id 和幂等记录，重试可能再次产生副作用。",
    layers: ["Runtime", "Tool Gateway", "Policy", "Audit"],
    evidence: ["operation_id", "checkpoint", "idempotency record", "audit event"],
    sourceFiles: ["08-学习可视化前端设计/08-v0.3低保真交互与页面流.md", "08-学习可视化前端设计/15-v0.4首轮原型任务说明与验收清单.md"],
    question: "为什么 retry 不能重复副作用？",
    feedbackTargets: ["FailureCase", "EvalCase", "RestatementCard"],
    topics: ["长线任务", "Tool Gateway", "Eval 门禁"],
    rows: [
      ["可能原因", "缺少 operation_id，重试无法识别已执行副作用。"],
      ["事故链路", "用户请求到工具执行之间没有幂等和审计证明。"],
      ["应拦截层", "Runtime 负责 checkpoint，Tool Gateway 负责幂等与工具边界。"],
      ["阻塞判断", "重复退款属于高风险副作用，必须阻塞并回滚学习模拟。"],
    ],
    bad: "坏设计：失败后直接 retry，工具再次执行同一退款动作。",
    low: "低分回流：补讲 checkpoint、operation_id 和幂等记录的关系。",
  },
  {
    id: "rag",
    nav: "RAG 诊断",
    subtitle: "三类问题",
    phase: "Phase 7",
    title: "RAG 问题诊断器：搜到不等于可信",
    summary: "把 RAG 拆成找不到、找错租户、引用不可信三类问题，分别对应不同指标、优化动作和发布门禁。",
    primaryTitle: "RAG 三类问题",
    gate: "证据检查",
    accident: "检索命中但引用不可信或跨租户",
    accidentText: "RAG 如果只看 top_k，就会把错误租户、过期资料或未审核来源当成答案依据。",
    layers: ["RAG", "Policy", "Eval", "Governance"],
    evidence: ["hard retrieval recall", "tenant ACL", "citation freshness", "EvalCase"],
    sourceFiles: ["07-RAG问题诊断与优化/00-RAG索引.md", "22-评测集/RAG评测数据集设计.md"],
    question: "为什么检索命中不等于可信答案？",
    feedbackTargets: ["RAGDiagnostic", "EvalCase", "KnowledgeCard", "RestatementCard"],
    topics: ["RAG 找不到", "RAG 找错租户", "RAG 引用可信"],
    rows: [
      ["找不到", "不是简单加 top_k，要看召回、query rewrite 和 chunk boundary。"],
      ["找错租户", "跨租户命中必须 release blocking，不能发布学习模拟。"],
      ["引用不可信", "未审核或过期来源不能作为可信答案依据。"],
    ],
    bad: "坏设计：把检索命中当成可信事实，忽略 citation、freshness 和 tenant ACL。",
    low: "低分回流：回到三类 RAG 诊断表，补一个 eval case。",
    rag: true,
  },
  {
    id: "wiki",
    nav: "LLM-Wiki",
    subtitle: "知识层",
    phase: "Phase 7.5",
    title: "LLM-Wiki 知识层：外部资料不能直接进课程",
    summary: "展示 GitHub、文章和 LLM 总结如何经过 SourceReview、KnowledgeCard、KnowledgeVersion，再进入课程或评测。",
    primaryTitle: "外部知识治理链路",
    gate: "需要审核",
    accident: "热门资料未经审核直接进入课程正文",
    accidentText: "GitHub star、检索命中和 LLM 总结都不是课程事实，必须先过来源审核和版本记录。",
    layers: ["SourceReview", "KnowledgeCard", "KnowledgeVersion", "ImportQueue"],
    evidence: ["license_status", "review_status", "adoption_mode", "source_files"],
    sourceFiles: ["08-学习可视化前端设计/09-LLM-Wiki知识层与可维护扩展方案.md", "10-GitHub项目调研/LLM-Wiki知识层调研-2026-07-02.md"],
    question: "为什么 GitHub 热门资料不能直接进入课程？",
    feedbackTargets: ["SourceReview", "KnowledgeCard", "KnowledgeVersion", "ImportQueue"],
    topics: ["LLM-Wiki 知识层", "RAG 引用可信"],
    rows: [
      ["ImportQueue", "登记外部来源和触发原因，例如低分回流或新资料更新。"],
      ["SourceReview", "检查 license、freshness、copyright risk 和采用方式。"],
      ["KnowledgeCard", "把可采用模式写成可复述、可审核、可回流的知识卡。"],
      ["KnowledgeVersion", "记录版本、变更原因和替代关系。"],
    ],
    bad: "坏设计：因为 star 高就复制进课程正文，未记录 license 和 review_status。",
    low: "低分回流：把误解送回 ImportQueue，补 SourceReview 和 KnowledgeCard。",
    wiki: true,
  },
  {
    id: "evidence",
    nav: "证据门禁",
    subtitle: "Trace / Eval / Release",
    phase: "Phase 8-11",
    title: "证据与门禁页：证明，而不是感觉",
    summary: "合并首轮 Trace、Audit、Eval 和 Release 学习模拟，说明什么证据能证明系统可以进入下一步。",
    primaryTitle: "Trace / Audit / Eval / Release",
    gate: "Release blocked",
    accident: "Eval critical 失败仍然继续发布学习模拟",
    accidentText: "如果只有漂亮 trace，没有 audit 和 eval gate，事故后无法证明责任，也无法阻塞退化版本。",
    layers: ["Trace", "Audit", "Eval", "Release Gate"],
    evidence: ["mock run timeline", "audit event", "eval case matrix", "rollback plan"],
    sourceFiles: ["06-工业级框架蓝图/工业级发布门禁矩阵.md", "06-工业级框架蓝图/测评审核门禁矩阵.md", "08-学习可视化前端设计/13-学习验证脚本与Go-No-Go.md"],
    question: "为什么 eval 不是分数装饰，而是 release blocking 门禁？",
    feedbackTargets: ["EvalCase", "TraceEvent", "ReleasePacket", "RestatementCard"],
    topics: ["Eval 门禁", "Trace/Audit", "记忆污染", "多 Agent 协同"],
    rows: [
      ["Trace", "定位哪一步出了问题，说明运行路径。"],
      ["Audit", "证明谁做了什么、何时发生、依据是什么。"],
      ["Eval Gate", "critical case 失败时阻塞 release packet。"],
      ["Release 学习模拟", "只做模拟判断，不出现真实发布按钮。"],
    ],
    bad: "坏设计：eval critical 失败，但页面仍提示可以继续发布。",
    low: "低分回流：重讲 trace 和 audit 的区别，再补一条 release blocking case。",
  },
];

const state = {
  pageId: "home",
  mode: "default",
  score: 2,
  ragFocus: "找不到",
  wikiFocus: "ImportQueue",
};

const pageNav = document.querySelector("#pageNav");
const appShell = document.querySelector(".app-shell");

function currentPage() {
  return pages.find((page) => page.id === state.pageId) || pages[0];
}

function renderNav() {
  pageNav.innerHTML = pages
    .map((page, index) => {
      const active = page.id === state.pageId ? "active" : "";
      return `
        <button class="nav-button ${active}" type="button" data-page="${page.id}" aria-current="${active ? "page" : "false"}">
          <span class="nav-index">${index + 1}</span>
          <span>
            <span class="nav-title">${page.nav}</span>
            <span class="nav-subtitle">${page.subtitle}</span>
          </span>
        </button>
      `;
    })
    .join("");
}

function renderRows(page) {
  return page.rows
    .map((row, index) => {
      const selected = index === 0 ? "selected" : "";
      return `
        <article class="path-row ${selected}">
          <span class="path-number">${index + 1}</span>
          <div class="path-main">
            <strong>${row[0]}</strong>
            <p>${row[1]}</p>
          </div>
          <button class="row-action" type="button" data-select-row="${index}">查看证据</button>
        </article>
      `;
    })
    .join("");
}

function renderRagPanel() {
  const items = {
    找不到: ["hard retrieval recall", "query rewrite", "chunk boundary review"],
    找错租户: ["tenant ACL", "policy filter", "release blocking"],
    引用不可信: ["citation precision", "freshness gate", "SourceReview"],
  };
  const buttons = Object.keys(items)
    .map((name) => `<button type="button" class="${state.ragFocus === name ? "active" : ""}" data-rag="${name}">${name}</button>`)
    .join("");
  const details = items[state.ragFocus]
    .map((item) => `<div class="matrix-item"><strong>${item}</strong><p>这是 ${state.ragFocus} 问题的最小诊断证据。</p></div>`)
    .join("");
  return `
    <div class="rag-tabs" aria-label="RAG 问题类型">${buttons}</div>
    <div class="matrix">${details}</div>
  `;
}

function renderWikiPanel() {
  const steps = ["ImportQueue", "SourceReview", "KnowledgeCard", "KnowledgeVersion"];
  const buttons = steps
    .map((name) => `<button type="button" class="${state.wikiFocus === name ? "active" : ""}" data-wiki="${name}">${name}</button>`)
    .join("");
  return `
    <div class="wiki-steps" aria-label="知识治理步骤">${buttons}</div>
    <div class="info-box">
      <strong>${state.wikiFocus}</strong>
      <p>${state.wikiFocus} 负责让外部资料在进入课程前留下来源、审核、版本和回流证据。</p>
    </div>
  `;
}

function renderPrimaryContent(page) {
  const modeBox =
    state.mode === "bad"
      ? `<div class="bad-box"><strong>坏设计路径</strong><p>${page.bad}</p></div>`
      : state.mode === "low"
        ? `<div class="low-box"><strong>低分回流</strong><p>${page.low}</p></div>`
        : `<div class="info-box"><strong>默认教学状态</strong><p>点击节点、切换状态、提交复述评分，观察证据面板如何变化。</p></div>`;
  const extra = page.rag ? renderRagPanel() : page.wiki ? renderWikiPanel() : "";
  return `
    ${extra}
    <div class="path-map">${renderRows(page)}</div>
    ${modeBox}
  `;
}

function renderEvidence(page) {
  document.querySelector("#phaseLabel").textContent = page.phase;
  document.querySelector("#pageTitle").textContent = page.title;
  document.querySelector("#pageSummary").textContent = page.summary;
  document.querySelector("#primaryTitle").textContent = page.primaryTitle;
  document.querySelector("#gateChip").textContent = page.gate;
  document.querySelector("#accidentTitle").textContent = page.accident;
  document.querySelector("#accidentText").textContent = page.accidentText;
  document.querySelector("#restatementQuestion").textContent = page.question;
  document.querySelector("#layerTags").innerHTML = page.layers.map((layer) => `<span>${layer}</span>`).join("");
  document.querySelector("#evidenceList").innerHTML = page.evidence.map((item) => `<li>${item}</li>`).join("");
  document.querySelector("#sourceFiles").innerHTML = page.sourceFiles.map((item) => `<li>${item}</li>`).join("");
  document.querySelector("#stateCoverage").innerHTML = [
    "default",
    "selected",
    "bad_design",
    "blocked",
    "low_score",
    "empty",
    "error",
    "mobile_collapsed",
  ].map((item) => `<span>${item}</span>`).join("");
  document.querySelector("#feedbackTargets").innerHTML = page.feedbackTargets.map((item) => `<span>${item}</span>`).join("");
}

function renderCoverage(page) {
  document.querySelector("#coverageMeter").innerHTML = p0Topics
    .map((topic) => `<span class="${page.topics.includes(topic) ? "covered" : ""}">${topic}</span>`)
    .join("");
}

function scoreMessage() {
  if (state.score < 3) {
    return `当前模拟分 ${state.score}，未过关。请回看事故、负责层和证据。`;
  }
  if (state.score === 3) {
    return "当前模拟分 3，达到过关下限。需要补充失败路径和停止条件。";
  }
  return `当前模拟分 ${state.score}，可以进入下一题，但仍然只代表学习通过。`;
}

function renderScore() {
  document.querySelectorAll("[data-score]").forEach((button) => {
    button.classList.toggle("active", Number(button.dataset.score) === state.score);
  });
  document.querySelector("#scoreFeedback").textContent = scoreMessage();
}

function renderStateButtons() {
  appShell.dataset.state = state.mode;
  document.querySelectorAll("[data-mode]").forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === state.mode);
  });
}

function render() {
  const page = currentPage();
  renderNav();
  renderEvidence(page);
  renderCoverage(page);
  renderStateButtons();
  renderScore();
  document.querySelector("#primaryContent").innerHTML = renderPrimaryContent(page);
}

document.addEventListener("click", (event) => {
  const pageButton = event.target.closest("[data-page]");
  const modeButton = event.target.closest("[data-mode]");
  const scoreButton = event.target.closest("[data-score]");
  const ragButton = event.target.closest("[data-rag]");
  const wikiButton = event.target.closest("[data-wiki]");
  const rowButton = event.target.closest("[data-select-row]");

  if (pageButton) {
    state.pageId = pageButton.dataset.page;
    state.mode = "default";
    state.score = state.pageId === "home" ? 2 : 3;
    render();
    document.querySelector("#main").focus();
  }

  if (modeButton) {
    state.mode = modeButton.dataset.mode;
    render();
  }

  if (scoreButton) {
    state.score = Number(scoreButton.dataset.score);
    if (state.score < 3) state.mode = "low";
    render();
  }

  if (ragButton) {
    state.ragFocus = ragButton.dataset.rag;
    render();
  }

  if (wikiButton) {
    state.wikiFocus = wikiButton.dataset.wiki;
    render();
  }

  if (rowButton) {
    state.mode = "default";
    render();
  }
});

render();
