import type { LearningCase } from "@/data/learningCases";

export type AnswerRecord = {
  caseId: string;
  beforeAnswer: string;
  afterAnswer: string;
  badDesignAnswer: string;
  beforeScore: number | null;
  afterScore: number | null;
  missingTags: string[];
  updatedAt: string;
};

export function scoreAnswer(answer: string, item: LearningCase): { score: number; missingTags: string[]; reason: string } {
  const normalized = answer.trim().toLowerCase();
  if (!normalized) {
    return { score: 0, missingTags: ["empty_answer"], reason: "还没有回答。" };
  }

  const accidentHit = hitAny(normalized, item.accident, ["事故", "风险", "越权", "泄漏", "重复", "错误", "发布", "污染", "阻塞"]);
  const layerHit = hitAny(normalized, item.responsibleLayer, ["层", "网关", "策略", "运行时", "审计", "评测", "沙箱", "知识", "source", "gateway", "policy", "runtime", "eval", "audit"]);
  const evidenceHit = hitAny(normalized, item.evidence, ["证据", "记录", "case", "trace", "audit", "source", "checkpoint", "ttl", "版本", "评测"]);
  const badDesignHit = hitAny(normalized, item.badDesignQuestion + item.accident, ["不能", "不应该", "必须", "阻塞", "审批", "回滚", "拦截", "低分"]);

  const missingTags = [
    !accidentHit ? "accident_missing" : "",
    !layerHit ? "layer_missing" : "",
    !evidenceHit ? "evidence_missing" : "",
  ].filter(Boolean);

  if (normalized.includes("生产控制台") || normalized.includes("真实退款") || normalized.includes("直接执行")) {
    missingTags.push("boundary_risk");
  }

  let score = 0;
  if (accidentHit) score = 2;
  if (accidentHit && layerHit && evidenceHit) score = 3;
  if (score >= 3 && badDesignHit) score = 4;
  if (score >= 4 && /验收|评测|审计|回归|门禁|trace|audit|eval/.test(normalized)) score = 5;
  if (missingTags.includes("boundary_risk")) score = Math.min(score, 1);

  return {
    score,
    missingTags,
    reason: score >= 3 ? "能说出事故、负责层和最小证据。" : "还缺事故、负责层或最小证据。",
  };
}

function hitAny(answer: string, source: string, hints: string[]) {
  const tokens = source
    .toLowerCase()
    .split(/[、/,\s]+/)
    .map((token) => token.trim())
    .filter((token) => token.length >= 3);
  return tokens.some((token) => answer.includes(token)) || hints.some((hint) => answer.includes(hint.toLowerCase()));
}

export function summarize(records: AnswerRecord[], total: number) {
  const afterPassed = records.filter((record) => (record.afterScore ?? -1) >= 3).length;
  const ragIds = ["v04_p0_005_rag_missing", "v04_p0_006_rag_wrong_tenant", "v04_p0_007_rag_citation_trust"];
  const ragPassed = ragIds.every((id) => (records.find((record) => record.caseId === id)?.afterScore ?? -1) >= 3);
  const boundaryRisk = records.some((record) => record.missingTags.includes("boundary_risk"));
  const lowWithoutTarget = records.some((record) => (record.afterScore ?? 5) < 3 && record.missingTags.length === 0);

  let verdict: "Go" | "Conditional Go" | "No-Go" = "No-Go";
  if (afterPassed >= 11 && ragPassed && !boundaryRisk && !lowWithoutTarget) verdict = "Go";
  else if (afterPassed >= total - 2 && ragPassed && !boundaryRisk) verdict = "Conditional Go";

  return { afterPassed, ragPassed, boundaryRisk, lowWithoutTarget, verdict };
}
