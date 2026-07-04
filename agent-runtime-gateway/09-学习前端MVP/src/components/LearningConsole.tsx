"use client";

import Image from "next/image";
import {
  AlertTriangle,
  ArrowRight,
  BookOpenCheck,
  Bot,
  BrainCircuit,
  CheckCircle2,
  ClipboardList,
  Database,
  Download,
  FileText,
  Filter,
  Gauge,
  GitBranch,
  Layers3,
  Link2,
  ListChecks,
  MapPinned,
  MessageSquareText,
  RotateCcw,
  Search,
  ShieldCheck,
  Sparkles,
  Waypoints,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { learningCases, materialAtlas, systemRoutes, type LearningCase, type SystemRoute } from "@/data/learningCases";
import { loadRecords, saveRecords } from "@/lib/storage";
import { scoreAnswer, summarize, type AnswerRecord } from "@/lib/score";

type TutorState = {
  loading: boolean;
  feedback: string;
  mode: "idle" | "local" | "agnes";
};

type WorkspaceView = "task" | "materials" | "atlas" | "backlog";
type EvidenceView = "gate" | "sources" | "coach";
type GuidedStep = "understand" | "evidence" | "design" | "restate" | "bad" | "backlog";
type DesignOption = {
  id: string;
  label: string;
  group: "负责层" | "最小证据" | "通过门禁" | "误导选项";
  required: boolean;
};

type DesignVerdict = {
  ready: boolean;
  missing: DesignOption[];
  risky: DesignOption[];
  selectedRequired: number;
  totalRequired: number;
};

const visuals = {
  home: { src: "/images/direction-c.png", label: "C 学习路线地图" },
  flow: { src: "/images/direction-a.png", label: "A 分层控制台" },
  incident: { src: "/images/direction-b.png", label: "B 事故推演" },
  rag: { src: "/images/direction-a.png", label: "RAG 诊断视角" },
  wiki: { src: "/images/direction-c.png", label: "LLM-Wiki 知识层" },
  evidence: { src: "/images/direction-b.png", label: "证据与门禁" },
} satisfies Record<LearningCase["visual"], { src: string; label: string }>;

export function LearningConsole() {
  const [activeId, setActiveId] = useState(learningCases[0]?.id ?? "");
  const [query, setQuery] = useState("");
  const [phaseFilter, setPhaseFilter] = useState("all");
  const [activeRouteId, setActiveRouteId] = useState(systemRoutes[0]?.id ?? "");
  const [workspaceView, setWorkspaceView] = useState<WorkspaceView>("task");
  const [evidenceView, setEvidenceView] = useState<EvidenceView>("gate");
  const [guidedStep, setGuidedStep] = useState<GuidedStep>("understand");
  const [records, setRecords] = useState<AnswerRecord[]>([]);
  const [beforeAnswer, setBeforeAnswer] = useState("");
  const [afterAnswer, setAfterAnswer] = useState("");
  const [badDesignAnswer, setBadDesignAnswer] = useState("");
  const [tutor, setTutor] = useState<TutorState>({ loading: false, feedback: "导师反馈会在这里显示。未配置 Agnes 时使用本地反馈。", mode: "idle" });

  const item = learningCases.find((entry) => entry.id === activeId) ?? learningCases[0];
  const activeRoute = systemRoutes.find((route) => route.id === activeRouteId) ?? systemRoutes[0];
  const activeIndex = caseOrder(item.id);
  const currentRecord = records.find((record) => record.caseId === item.id);
  const summary = useMemo(() => summarize(records, learningCases.length), [records]);
  const phases = useMemo(() => Array.from(new Set(learningCases.map((entry) => entry.phase))), []);
  const filteredCases = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    return learningCases.filter((entry) => {
      const phaseMatch = phaseFilter === "all" || entry.phase === phaseFilter;
      const text = `${entry.topic} ${entry.phase} ${entry.page} ${entry.accident} ${entry.responsibleLayer} ${entry.sourceFiles.join(" ")}`.toLowerCase();
      return phaseMatch && (!keyword || text.includes(keyword));
    });
  }, [phaseFilter, query]);
  const beforeScore = beforeAnswer ? scoreAnswer(beforeAnswer, item) : null;
  const afterScore = afterAnswer ? scoreAnswer(afterAnswer, item) : null;
  const canContinue = (currentRecord?.afterScore ?? -1) >= 3;
  const visual = visuals[item.visual];
  const completedCount = records.filter((record) => (record.afterScore ?? -1) >= 3).length;
  const nextCase = learningCases[Math.min(activeIndex + 1, learningCases.length - 1)];

  useEffect(() => {
    setRecords(loadRecords());
  }, []);

  useEffect(() => {
    if (filteredCases.length > 0 && !filteredCases.some((entry) => entry.id === activeId)) {
      setActiveId(filteredCases[0].id);
    }
  }, [activeId, filteredCases]);

  useEffect(() => {
    const record = records.find((entry) => entry.caseId === item.id);
    setBeforeAnswer(record?.beforeAnswer ?? "");
    setAfterAnswer(record?.afterAnswer ?? "");
    setBadDesignAnswer(record?.badDesignAnswer ?? "");
    setTutor({ loading: false, feedback: "导师反馈会在这里显示。未配置 Agnes 时使用本地反馈。", mode: "idle" });
    setGuidedStep("understand");
  }, [activeIndex, item.id, records]);

  useEffect(() => {
    const route = systemRoutes.find((candidate) => candidate.caseIds.includes(item.id));
    if (route) setActiveRouteId(route.id);
  }, [item.id]);

  function openCase(caseId: string, view: WorkspaceView = "task") {
    setActiveId(caseId);
    setWorkspaceView(view);
  }

  function selectRoute(routeId: string) {
    const route = systemRoutes.find((candidate) => candidate.id === routeId);
    setActiveRouteId(routeId);
    if (route && !route.caseIds.includes(item.id)) {
      openCase(route.caseIds[0], "task");
    }
  }

  function persist(record: AnswerRecord) {
    const next = [...records.filter((entry) => entry.caseId !== record.caseId), record].sort((a, b) => caseOrder(a.caseId) - caseOrder(b.caseId));
    setRecords(next);
    saveRecords(next);
  }

  function recordScores() {
    const before = scoreAnswer(beforeAnswer, item);
    const after = scoreAnswer(afterAnswer, item);
    const missingTags = Array.from(new Set([...before.missingTags, ...after.missingTags]));
    persist({
      caseId: item.id,
      beforeAnswer,
      afterAnswer,
      badDesignAnswer,
      beforeScore: before.score,
      afterScore: after.score,
      missingTags,
      updatedAt: new Date().toISOString(),
    });
  }

  async function askTutor(stage: "before" | "after" | "bad_design") {
    const answer = stage === "before" ? beforeAnswer : stage === "after" ? afterAnswer : badDesignAnswer;
    setTutor({ loading: true, feedback: "正在生成导师反馈...", mode: "idle" });
    try {
      const response = await fetch("/api/agnes/tutor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ caseId: item.id, answer, stage }),
      });
      const data = (await response.json()) as { feedback?: string; mode?: "local" | "agnes"; error?: string };
      setTutor({
        loading: false,
        feedback: data.feedback || data.error || "没有收到有效反馈。",
        mode: data.mode || "local",
      });
    } catch {
      setTutor({ loading: false, feedback: "导师服务暂不可用，请先按本地评分继续。", mode: "local" });
    }
  }

  function resetLearning() {
    setRecords([]);
    saveRecords([]);
    setActiveId(learningCases[0]?.id ?? "");
  }

  function exportRecords() {
    const payload = {
      exported_at: new Date().toISOString(),
      verdict: summary.verdict,
      records,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "agent-learning-records.json";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">AG</span>
          <span>
            <strong>Agent + RAG 学习控制台</strong>
            <small>Design-only MVP · 已过 {completedCount}/{learningCases.length}</small>
          </span>
        </div>
        <div className="boundary" aria-label="学习边界">
          <span>学习模式 <b>Learning mode</b></span>
          <span>模拟数据 <b>Mock data</b></span>
          <span>不执行真实操作 <b>No real execution</b></span>
          <span>来源文件 <b>Source files</b></span>
        </div>
      </header>

      <aside className="rail">
        <section className="rail-head">
          <small>第 1 课</small>
          <h1>逐题学习</h1>
          <p>每次只做一题，低于 3 分停下重讲。</p>
        </section>
        <section className="rail-controls" aria-label="筛选学习主题">
          <label className="search-box">
            <Search size={15} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索主题、事故、资料" />
          </label>
          <label className="select-box">
            <Filter size={15} />
            <select value={phaseFilter} onChange={(event) => setPhaseFilter(event.target.value)}>
              <option value="all">全部 Phase</option>
              {phases.map((phase) => (
                <option key={phase} value={phase}>{phase}</option>
              ))}
            </select>
          </label>
        </section>
        <nav className="topic-list" aria-label="13 个 P0 主题">
          {filteredCases.map((entry) => {
            const record = records.find((candidate) => candidate.caseId === entry.id);
            const passed = (record?.afterScore ?? -1) >= 3;
            const active = entry.id === item.id;
            const index = caseOrder(entry.id);
            return (
              <button key={entry.id} className={active ? "topic active" : "topic"} type="button" onClick={() => setActiveId(entry.id)}>
                <span className={passed ? "topic-index passed" : "topic-index"}>{passed ? <CheckCircle2 size={14} /> : index + 1}</span>
                <span>
                  <strong>{entry.topic}</strong>
                  <small>{entry.phase}</small>
                </span>
              </button>
            );
          })}
          {filteredCases.length === 0 ? <p className="empty-note">没有匹配的学习题，换个关键词试试。</p> : null}
        </nav>
        <section className="rail-note">
          <ShieldCheck size={17} />
          <span>本页没有真实退款、审批、发布或工具执行入口。</span>
        </section>
      </aside>

      <section className="workspace">
        <div className="page-head">
          <div>
            <small>{item.phase}</small>
            <h2>{item.topic}</h2>
            <p>{item.page}</p>
          </div>
          <div className="head-actions">
            <button type="button" onClick={exportRecords}>
              <Download size={16} />
              导出记录
            </button>
            <button type="button" onClick={resetLearning}>
              <RotateCcw size={16} />
              重置学习
            </button>
          </div>
        </div>

        <section className="case-overview" aria-label="当前学习资料对接">
          <SystemRouteWorkbench
            activeRoute={activeRoute}
            activeCaseId={item.id}
            records={records}
            onSelectRoute={selectRoute}
            onSelectCase={(caseId) => openCase(caseId)}
          />
          <div className="lesson-brief">
            <div className="brief-block">
              <span className="section-icon"><Layers3 size={17} /></span>
              <div>
                <small>当前学习目标</small>
                <h3>{item.learningGoal}</h3>
                <p>{item.materialSummary}</p>
              </div>
            </div>
            <BridgeSteps steps={item.bridgeSteps} />
          </div>
        </section>

        <section className="learning-panel">
          <div className="panel-heading">
            <span className="section-icon"><BookOpenCheck size={17} /></span>
            <div>
              <small>逐题主持</small>
              <h3>先回答，再评分，再看图复述</h3>
            </div>
          </div>
          <div className="view-tabs" role="tablist" aria-label="学习视图">
            <button type="button" className={workspaceView === "task" ? "active" : ""} onClick={() => setWorkspaceView("task")}>学习任务</button>
            <button type="button" className={workspaceView === "materials" ? "active" : ""} onClick={() => setWorkspaceView("materials")}>资料证据</button>
            <button type="button" className={workspaceView === "atlas" ? "active" : ""} onClick={() => setWorkspaceView("atlas")}>资料地图</button>
            <button type="button" className={workspaceView === "backlog" ? "active" : ""} onClick={() => setWorkspaceView("backlog")}>低分回流</button>
          </div>

          {workspaceView === "task" ? (
            <GuidedLearningPanel
              item={item}
              activeRoute={activeRoute}
              visual={visual}
              step={guidedStep}
              onStepChange={setGuidedStep}
              beforeAnswer={beforeAnswer}
              afterAnswer={afterAnswer}
              badDesignAnswer={badDesignAnswer}
              beforeScore={beforeScore}
              afterScore={afterScore}
              currentRecord={currentRecord}
              canContinue={canContinue}
              isLastCase={activeIndex >= learningCases.length - 1}
              onBeforeChange={setBeforeAnswer}
              onAfterChange={setAfterAnswer}
              onBadDesignChange={setBadDesignAnswer}
              onTutor={askTutor}
              onRecordScores={recordScores}
              onNextCase={() => setActiveId(nextCase.id)}
            />
          ) : null}

          {workspaceView === "materials" ? <MaterialsPanel item={item} /> : null}
          {workspaceView === "atlas" ? <MaterialAtlasPanel onSelectCase={(caseId) => {
            openCase(caseId, "materials");
          }} /> : null}
          {workspaceView === "backlog" ? <BacklogPanel item={item} record={currentRecord} /> : null}
        </section>
      </section>

      <aside className="evidence">
        <div className="side-tabs" role="tablist" aria-label="证据面板">
          <button type="button" className={evidenceView === "gate" ? "active" : ""} onClick={() => setEvidenceView("gate")}>门禁</button>
          <button type="button" className={evidenceView === "sources" ? "active" : ""} onClick={() => setEvidenceView("sources")}>来源</button>
          <button type="button" className={evidenceView === "coach" ? "active" : ""} onClick={() => setEvidenceView("coach")}>导师</button>
        </div>

        {evidenceView === "gate" ? (
          <>
            <section className="score-card">
              <div className="panel-heading compact">
                <span className="section-icon"><Gauge size={17} /></span>
                <div>
                  <small>Go / No-Go</small>
                  <h3>{summary.verdict}</h3>
                </div>
              </div>
              <dl className="metrics">
                <div><dt>看图后通过</dt><dd>{summary.afterPassed}/13</dd></div>
                <div><dt>RAG 三类</dt><dd>{summary.ragPassed ? "通过" : "未过"}</dd></div>
                <div><dt>生产误读</dt><dd>{summary.boundaryRisk ? "有风险" : "未发现"}</dd></div>
              </dl>
            </section>

            <section className="score-card">
              <div className="panel-heading compact">
                <span className="section-icon"><AlertTriangle size={17} /></span>
                <div>
                  <small>事故</small>
                  <h3>{item.accident}</h3>
                </div>
              </div>
              <InfoList title="负责层" items={item.responsibleLayer.split(" / ")} />
              <InfoList title="最小证据" items={item.evidence.split("、")} />
              <InfoList title="低分回流" items={item.feedbackTargets} />
            </section>
          </>
        ) : null}

        {evidenceView === "sources" ? (
          <section className="score-card">
            <div className="panel-heading compact">
              <span className="section-icon"><FileText size={17} /></span>
              <div>
                <small>Source files</small>
                <h3>来源文件</h3>
              </div>
            </div>
            <SourceCards item={item} compact />
          </section>
        ) : null}

        {evidenceView === "coach" ? (
          <section className="score-card tutor-card">
            <div className="panel-heading compact">
              <span className="section-icon"><BrainCircuit size={17} /></span>
              <div>
                <small>Agnes 导师代理</small>
                <h3>{tutor.mode === "agnes" ? "Agnes 反馈" : "本地反馈"}</h3>
              </div>
            </div>
            <p>{tutor.loading ? "正在等待反馈..." : tutor.feedback}</p>
            <p className="fine-print">API Key 仅由服务端环境变量读取，浏览器不会接触密钥。</p>
          </section>
        ) : null}
      </aside>
    </main>
  );
}

function SystemRouteWorkbench({
  activeRoute,
  activeCaseId,
  records,
  onSelectRoute,
  onSelectCase,
}: {
  activeRoute: SystemRoute;
  activeCaseId: string;
  records: AnswerRecord[];
  onSelectRoute: (routeId: string) => void;
  onSelectCase: (caseId: string) => void;
}) {
  const completed = activeRoute.caseIds.filter((caseId) => (records.find((record) => record.caseId === caseId)?.afterScore ?? -1) >= 3).length;
  const total = activeRoute.caseIds.length;

  return (
    <section className="route-workbench" aria-label="工业级 Agent 主路线">
      <div className="route-map-head">
        <div>
          <small>主路线</small>
          <h3>如何设计一个可靠的 Agent 系统</h3>
          <p>先搭主干，再补 RAG、记忆、工具、评测和治理。点击节点查看它防什么事故。</p>
        </div>
        <span className="route-progress">{completed}/{total} 已过</span>
      </div>

      <div className="route-map">
        {systemRoutes.map((route, index) => {
          const selected = route.id === activeRoute.id;
          const active = route.caseIds.includes(activeCaseId);
          return (
            <button
              key={route.id}
              type="button"
              className={selected ? "route-node selected" : active ? "route-node related" : "route-node"}
              onClick={() => onSelectRoute(route.id)}
            >
              <span className="route-node-icon">{routeIcon(route.id)}</span>
              <span>
                <strong>{route.title}</strong>
                <small>{route.subtitle}</small>
              </span>
              <em>{index + 1}</em>
            </button>
          );
        })}
      </div>

      <article className="route-detail">
        <div className="route-detail-head">
          <div>
            <small>{activeRoute.subtitle}</small>
            <h4>{activeRoute.title}</h4>
          </div>
          <button type="button" onClick={() => onSelectCase(activeRoute.caseIds[0])}>查看路线课程</button>
        </div>
        <p>{activeRoute.goal}</p>
        <p className="route-why">{activeRoute.why}</p>

        <div className="route-evidence-grid">
          <InfoList title="防止事故" items={[activeRoute.accident]} />
          <InfoList title="负责层" items={activeRoute.responsibleLayers} />
          <InfoList title="最小证据" items={activeRoute.evidence} />
          <InfoList title="通过门禁" items={activeRoute.qualityGates} />
        </div>

        <div className="route-cases">
          {activeRoute.caseIds.map((caseId) => {
            const course = learningCases.find((entry) => entry.id === caseId);
            if (!course) return null;
            return (
              <button key={caseId} type="button" className={caseId === activeCaseId ? "active" : ""} onClick={() => onSelectCase(caseId)}>
                {course.topic}
              </button>
            );
          })}
        </div>
      </article>
    </section>
  );
}

function routeIcon(routeId: string) {
  if (routeId === "agent-runtime") return <Bot size={18} />;
  if (routeId === "rag-system") return <Search size={18} />;
  if (routeId === "memory-system") return <Database size={18} />;
  if (routeId === "tool-policy") return <ShieldCheck size={18} />;
  if (routeId === "eval-release") return <Gauge size={18} />;
  if (routeId === "trace-audit") return <Waypoints size={18} />;
  if (routeId === "multi-agent") return <GitBranch size={18} />;
  return <FileText size={18} />;
}

function buildRequiredDesignItems(route: SystemRoute): DesignOption[] {
  return [
    ...route.responsibleLayers.map((label) => designOption(route.id, "负责层", label, true)),
    ...route.evidence.map((label) => designOption(route.id, "最小证据", label, true)),
    ...route.qualityGates.map((label) => designOption(route.id, "通过门禁", label, true)),
  ];
}

function buildDistractorDesignItems(route: SystemRoute): DesignOption[] {
  const labels = [
    "模型建议直接执行工具",
    "只看平均分放行",
    "检索命中就可信",
    "长期记忆自动写入",
    "GitHub star 高直接入课",
    "只有聊天记录不建 Run",
  ];
  const routeText = `${route.title} ${route.goal} ${route.accident} ${route.responsibleLayers.join(" ")} ${route.evidence.join(" ")} ${route.qualityGates.join(" ")}`;
  return labels
    .filter((label) => !routeText.includes(label))
    .slice(0, 4)
    .map((label) => designOption(route.id, "误导选项", label, false));
}

function designOption(routeId: string, group: DesignOption["group"], label: string, required: boolean): DesignOption {
  return {
    id: `${routeId}:${group}:${label}`,
    label,
    group,
    required,
  };
}

function getDesignVerdict(requiredItems: DesignOption[], distractorItems: DesignOption[], selectedItems: string[]): DesignVerdict {
  const selectedSet = new Set(selectedItems);
  const missing = requiredItems.filter((option) => !selectedSet.has(option.id));
  const risky = distractorItems.filter((option) => selectedSet.has(option.id));
  return {
    ready: missing.length === 0 && risky.length === 0,
    missing,
    risky,
    selectedRequired: requiredItems.length - missing.length,
    totalRequired: requiredItems.length,
  };
}

function GuidedLearningPanel({
  item,
  activeRoute,
  visual,
  step,
  onStepChange,
  beforeAnswer,
  afterAnswer,
  badDesignAnswer,
  beforeScore,
  afterScore,
  currentRecord,
  canContinue,
  isLastCase,
  onBeforeChange,
  onAfterChange,
  onBadDesignChange,
  onTutor,
  onRecordScores,
  onNextCase,
}: {
  item: LearningCase;
  activeRoute: SystemRoute;
  visual: { src: string; label: string };
  step: GuidedStep;
  onStepChange: (step: GuidedStep) => void;
  beforeAnswer: string;
  afterAnswer: string;
  badDesignAnswer: string;
  beforeScore: ReturnType<typeof scoreAnswer> | null;
  afterScore: ReturnType<typeof scoreAnswer> | null;
  currentRecord?: AnswerRecord;
  canContinue: boolean;
  isLastCase: boolean;
  onBeforeChange: (value: string) => void;
  onAfterChange: (value: string) => void;
  onBadDesignChange: (value: string) => void;
  onTutor: (stage: "before" | "after" | "bad_design") => void;
  onRecordScores: () => void;
  onNextCase: () => void;
}) {
  const [selectedDesignItems, setSelectedDesignItems] = useState<string[]>([]);
  const requiredDesignItems = useMemo(() => buildRequiredDesignItems(activeRoute), [activeRoute]);
  const distractorDesignItems = useMemo(() => buildDistractorDesignItems(activeRoute), [activeRoute]);
  const designVerdict = useMemo(() => getDesignVerdict(requiredDesignItems, distractorDesignItems, selectedDesignItems), [distractorDesignItems, requiredDesignItems, selectedDesignItems]);

  useEffect(() => {
    setSelectedDesignItems([]);
  }, [activeRoute.id, item.id]);

  const steps: Array<{ id: GuidedStep; label: string; hint: string; status: string; state: "idle" | "pass" | "low" }> = [
    {
      id: "understand",
      label: "理解问题",
      hint: item.beforeQuestion,
      status: beforeScore ? `${beforeScore.score}/5` : "待写",
      state: beforeScore ? (beforeScore.score >= 3 ? "pass" : "low") : "idle",
    },
    {
      id: "evidence",
      label: "看证据",
      hint: `${item.accident} / ${item.responsibleLayer}`,
      status: "必看",
      state: "idle",
    },
    {
      id: "design",
      label: "方案装配",
      hint: "选负责层、证据和门禁",
      status: designVerdict.ready ? "可继续" : "待补齐",
      state: designVerdict.ready ? "pass" : selectedDesignItems.length ? "low" : "idle",
    },
    {
      id: "restate",
      label: "复述验收",
      hint: "事故、负责层、最小证据",
      status: afterScore ? `${afterScore.score}/5` : "待写",
      state: afterScore ? (afterScore.score >= 3 ? "pass" : "low") : "idle",
    },
    {
      id: "bad",
      label: "坏设计判断",
      hint: item.badDesignQuestion,
      status: badDesignAnswer ? "已写" : "待写",
      state: badDesignAnswer ? "pass" : "idle",
    },
    {
      id: "backlog",
      label: "回流下一步",
      hint: "低分进入卡点和资料修订",
      status: currentRecord ? "已记录" : "未记录",
      state: canContinue ? "pass" : currentRecord ? "low" : "idle",
    },
  ];

  return (
    <div className="guided-shell">
      <aside className="guided-rail" aria-label="学习流程">
        {steps.map((entry, index) => (
          <button key={entry.id} type="button" className={step === entry.id ? `active ${entry.state}` : entry.state} onClick={() => onStepChange(entry.id)}>
            <span>{index + 1}</span>
            <strong>{entry.label}</strong>
            <small>{entry.hint}</small>
            <em>{entry.status}</em>
          </button>
        ))}
      </aside>

      <section className="guided-stage">
        {step === "understand" ? (
          <AnswerBox
            title="第一步"
            question={item.beforeQuestion}
            value={beforeAnswer}
            onChange={onBeforeChange}
            score={beforeScore?.score}
            reason={beforeScore?.reason}
            onTutor={() => onTutor("before")}
          />
        ) : null}

        {step === "evidence" ? (
          <div className="evidence-stage">
            <EvidenceBox item={item} visual={visual} />
            <section className="evidence-brief">
              <h4>看证据时只抓三件事</h4>
              <InfoList title="事故" items={[item.accident]} />
              <InfoList title="负责层" items={item.responsibleLayer.split(" / ")} />
              <InfoList title="最小证据" items={item.evidence.split("、")} />
            </section>
          </div>
        ) : null}

        {step === "design" ? (
          <DesignAssemblyPanel
            activeRoute={activeRoute}
            requiredItems={requiredDesignItems}
            distractorItems={distractorDesignItems}
            selectedItems={selectedDesignItems}
            verdict={designVerdict}
            onToggle={(id) => {
              setSelectedDesignItems((current) => current.includes(id) ? current.filter((itemId) => itemId !== id) : [...current, id]);
            }}
            onUseRecommended={() => setSelectedDesignItems(requiredDesignItems.map((option) => option.id))}
            onClear={() => setSelectedDesignItems([])}
          />
        ) : null}

        {step === "restate" ? (
          <AnswerBox
            title="第三步"
            question="现在请补齐事故、负责层、最小证据。"
            value={afterAnswer}
            onChange={onAfterChange}
            score={afterScore?.score}
            reason={afterScore?.reason}
            onTutor={() => onTutor("after")}
          />
        ) : null}

        {step === "bad" ? (
          <AnswerBox
            title="第四步"
            question={item.badDesignQuestion}
            value={badDesignAnswer}
            onChange={onBadDesignChange}
            onTutor={() => onTutor("bad_design")}
          />
        ) : null}

        {step === "backlog" ? <BacklogPanel item={item} record={currentRecord} /> : null}

        <div className="guided-actions">
          <button className="primary-action" type="button" onClick={onRecordScores}>
            <ClipboardList size={16} />
            记录本题评分
          </button>
          <button className="secondary-action" type="button" disabled={!canContinue || isLastCase} onClick={onNextCase}>
            进入下一题
          </button>
          <span className={canContinue ? "gate pass" : "gate hold"}>
            {canContinue ? "本题可继续" : "低于 3 分时停下重讲"}
          </span>
        </div>
      </section>
    </div>
  );
}

function DesignAssemblyPanel({
  activeRoute,
  requiredItems,
  distractorItems,
  selectedItems,
  verdict,
  onToggle,
  onUseRecommended,
  onClear,
}: {
  activeRoute: SystemRoute;
  requiredItems: DesignOption[];
  distractorItems: DesignOption[];
  selectedItems: string[];
  verdict: DesignVerdict;
  onToggle: (id: string) => void;
  onUseRecommended: () => void;
  onClear: () => void;
}) {
  const groupedRequired = groupDesignOptions(requiredItems);
  const selectedSet = new Set(selectedItems);

  return (
    <section className="assembly-panel">
      <div className="assembly-head">
        <div>
          <small>方案装配</small>
          <h4>把“{activeRoute.title}”装成可验收设计</h4>
          <p>选择应该进入方案的负责层、证据和门禁。误选危险捷径会让方案进入 review。</p>
        </div>
        <span className={verdict.ready ? "assembly-verdict pass" : "assembly-verdict hold"}>
          {verdict.ready ? "可继续" : "需要修订"}
        </span>
      </div>

      <div className="assembly-score">
        <div>
          <strong>{verdict.selectedRequired}/{verdict.totalRequired}</strong>
          <span>必选项已选</span>
        </div>
        <div>
          <strong>{verdict.risky.length}</strong>
          <span>误导项</span>
        </div>
        <div>
          <strong>{verdict.missing.length}</strong>
          <span>缺失项</span>
        </div>
      </div>

      <div className="assembly-groups">
        {Object.entries(groupedRequired).map(([group, options]) => (
          <section key={group} className="assembly-group">
            <strong>{group}</strong>
            <div>
              {options.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  className={selectedSet.has(option.id) ? "assembly-option selected" : "assembly-option"}
                  onClick={() => onToggle(option.id)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </section>
        ))}

        <section className="assembly-group danger">
          <strong>不要选这些捷径</strong>
          <div>
            {distractorItems.map((option) => (
              <button
                key={option.id}
                type="button"
                className={selectedSet.has(option.id) ? "assembly-option risky selected" : "assembly-option risky"}
                onClick={() => onToggle(option.id)}
              >
                {option.label}
              </button>
            ))}
          </div>
        </section>
      </div>

      <div className="assembly-feedback">
        <div>
          <strong>下一步判断</strong>
          <p>{verdict.ready ? "方案已经包含负责层、证据和门禁，可以进入复述验收。" : "先补齐缺失项，并移除误导项，再进入复述。"}</p>
        </div>
        <div className="assembly-tags">
          {verdict.missing.slice(0, 6).map((option) => (
            <span key={option.id}>缺：{option.label}</span>
          ))}
          {verdict.risky.map((option) => (
            <span key={option.id} className="risk">误选：{option.label}</span>
          ))}
        </div>
      </div>

      <div className="assembly-actions">
        <button type="button" onClick={onUseRecommended}>应用标准方案</button>
        <button type="button" onClick={onClear}>清空选择</button>
      </div>
    </section>
  );
}

function groupDesignOptions(options: DesignOption[]) {
  return options.reduce<Record<string, DesignOption[]>>((groups, option) => {
    groups[option.group] = [...(groups[option.group] ?? []), option];
    return groups;
  }, {});
}

function AnswerBox({
  title,
  question,
  value,
  score,
  reason,
  onChange,
  onTutor,
}: {
  title: string;
  question: string;
  value: string;
  score?: number;
  reason?: string;
  onChange: (value: string) => void;
  onTutor: () => void;
}) {
  return (
    <section className="answer-box">
      <div className="answer-head">
        <div>
          <small>{title}</small>
          <h4>{question}</h4>
        </div>
        {typeof score === "number" ? <span className={score >= 3 ? "score pass" : "score low"}>{score}/5</span> : <span className="score">未评</span>}
      </div>
      <textarea value={value} onChange={(event) => onChange(event.target.value)} placeholder="用自己的话回答，不用背术语。" />
      <div className="answer-foot">
        <span>{reason || "回答后会显示本地评分。"}</span>
        <button type="button" onClick={onTutor}>
          <MessageSquareText size={15} />
          请导师反馈
        </button>
      </div>
    </section>
  );
}

function EvidenceBox({ item, visual }: { item: LearningCase; visual: { src: string; label: string } }) {
  return (
    <section className="evidence-box">
      <div className="answer-head">
        <div>
          <small>看图提示</small>
          <h4>{visual.label}</h4>
        </div>
        <Sparkles size={18} />
      </div>
      <div className="mini-visual">
        <Image src={visual.src} alt={visual.label} width={640} height={260} loading="eager" />
      </div>
      <ul>
        <li>事故：{item.accident}</li>
        <li>负责层：{item.responsibleLayer}</li>
        <li>证据：{item.evidence}</li>
      </ul>
    </section>
  );
}

function BridgeSteps({ steps }: { steps: string[] }) {
  return (
    <ol className="bridge-steps" aria-label="资料到复述的桥接步骤">
      {steps.map((step, index) => (
        <li key={step}>
          <span>{index + 1}</span>
          <p>{step}</p>
        </li>
      ))}
    </ol>
  );
}

function MaterialsPanel({ item }: { item: LearningCase }) {
  return (
    <div className="materials-panel">
      <section className="material-flow">
        <div className="panel-heading compact">
          <span className="section-icon"><Link2 size={17} /></span>
          <div>
            <small>资料对接链路</small>
            <h3>来源文件如何进入本题</h3>
          </div>
        </div>
        <div className="flow-row" aria-label="资料进入学习页的路径">
          {["Source files", "教学问题", "事故路径", "证据门禁", "低分回流"].map((label, index, list) => (
            <span key={label}>
              <b>{label}</b>
              {index < list.length - 1 ? <ArrowRight size={15} /> : null}
            </span>
          ))}
        </div>
        <p>{item.materialSummary}</p>
      </section>

      <SourceCards item={item} />
    </div>
  );
}

function SourceCards({ item, compact = false }: { item: LearningCase; compact?: boolean }) {
  return (
    <div className={compact ? "source-cards compact" : "source-cards"}>
      {item.materials.map((material) => (
        <article key={material.file} className="source-card">
          <div>
            <strong>{material.role}</strong>
            <StatusPill status={material.status} />
          </div>
          <p>{material.file}</p>
          {!compact ? <small>{material.why}</small> : null}
          <span>回流目标：{material.target}</span>
        </article>
      ))}
    </div>
  );
}

function MaterialAtlasPanel({ onSelectCase }: { onSelectCase: (caseId: string) => void }) {
  const needsReview = materialAtlas.filter((material) => material.status === "needs_review").length;
  const ready = materialAtlas.length - needsReview;
  const roles = Array.from(new Set(materialAtlas.map((material) => material.role)));

  return (
    <div className="atlas-panel">
      <section className="atlas-summary">
        <div className="panel-heading compact">
          <span className="section-icon"><MapPinned size={17} /></span>
          <div>
            <small>全局资料地图</small>
            <h3>所有来源文件如何支撑这 13 道题</h3>
          </div>
        </div>
        <dl className="atlas-metrics">
          <div><dt>去重资料</dt><dd>{materialAtlas.length}</dd></div>
          <div><dt>已接入</dt><dd>{ready}</dd></div>
          <div><dt>需审核</dt><dd>{needsReview}</dd></div>
          <div><dt>资料角色</dt><dd>{roles.length}</dd></div>
        </dl>
      </section>

      <div className="atlas-list">
        {materialAtlas.map((material) => (
          <article key={material.file} className="atlas-card">
            <div className="atlas-card-head">
              <div>
                <strong>{material.role}</strong>
                <p>{material.file}</p>
              </div>
              <StatusPill status={material.status} />
            </div>
            <div className="atlas-meta">
              <span>使用 {material.usageCount} 次</span>
              {material.phases.map((phase) => (
                <span key={phase}>{phase}</span>
              ))}
            </div>
            <div className="case-links" aria-label={`${material.file} 关联题目`}>
              {material.caseIds.map((caseId, index) => (
                <button key={caseId} type="button" onClick={() => onSelectCase(caseId)}>
                  {material.topics[index]}
                </button>
              ))}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function BacklogPanel({ item, record }: { item: LearningCase; record?: AnswerRecord }) {
  const score = record?.afterScore;
  const missing = record?.missingTags.length ? record.missingTags : ["等待复述评分"];

  return (
    <div className="backlog-panel">
      <section className="gate-decision">
        <div>
          <small>当前判断</small>
          <h3>{typeof score === "number" ? (score >= 3 ? "可以继续，但仍保留证据" : "停下重讲") : "还没有记录评分"}</h3>
          <p>{typeof score === "number" ? `看图后复述得分：${score}/5` : "先完成看图后复述并记录评分。"}</p>
        </div>
        <span className={typeof score === "number" && score >= 3 ? "gate pass" : "gate hold"}>
          {typeof score === "number" && score >= 3 ? "pass" : "blocked / review"}
        </span>
      </section>

      <section className="review-checklist">
        <div className="panel-heading compact">
          <span className="section-icon"><ListChecks size={17} /></span>
          <div>
            <small>验收清单</small>
            <h3>复述必须包含这些证据</h3>
          </div>
        </div>
        <ul>
          {item.reviewChecklist.map((check) => (
            <li key={check}>{check}</li>
          ))}
        </ul>
      </section>

      <section className="backlog-targets">
        <strong>缺失项</strong>
        <div>
          {missing.map((tag) => (
            <span key={tag}>{tag}</span>
          ))}
        </div>
        <strong>回流对象</strong>
        <div>
          {item.feedbackTargets.map((target) => (
            <span key={target}>{target}</span>
          ))}
        </div>
      </section>
    </div>
  );
}

function StatusPill({ status }: { status: "ready" | "needs_review" }) {
  return <span className={status === "ready" ? "status ready" : "status review"}>{status === "ready" ? "已接入" : "需审核"}</span>;
}

function InfoList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="info-list">
      <strong>{title}</strong>
      <div>
        {items.map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>
    </div>
  );
}

function caseOrder(caseId: string) {
  return learningCases.findIndex((item) => item.id === caseId);
}
