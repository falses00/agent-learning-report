import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const dataDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(dataDir, '..');
const context = vm.createContext({ window: {} });
vm.runInContext(readFileSync(resolve(dataDir, 'rag_lab.js'), 'utf8'), context);
const lab = context.window.RAG_LAB;
const errors = [];

const requireText = (value, path) => {
  if (typeof value !== 'string' || !value.trim()) errors.push(`${path} must be non-empty text`);
};
const unique = (items, path) => {
  const ids = items.map((item) => item.id);
  if (new Set(ids).size !== ids.length) errors.push(`${path} ids must be unique`);
};

if (!lab || typeof lab !== 'object') errors.push('window.RAG_LAB is missing');
else {
  const requirements = [
    ['pipeline', 10], ['methods', 24], ['scenarios', 14], ['plannerProfiles', 5],
    ['projects', 10], ['metrics', 7], ['sources', 36], ['learningPath', 7],
  ];
  for (const [field, minimum] of requirements) {
    if (!Array.isArray(lab[field]) || lab[field].length < minimum) errors.push(`${field} must contain at least ${minimum} entries`);
    else unique(lab[field], field);
  }
  const familyIds = new Set((lab.families || []).map((item) => item.id));
  (lab.methods || []).forEach((item, index) => {
    for (const field of ['id', 'name', 'family', 'symptom', 'principle', 'experiment', 'benefit', 'cost', 'rollback', 'sourceLabel', 'sourceUrl']) requireText(item[field], `methods[${index}].${field}`);
    if (!familyIds.has(item.family)) errors.push(`methods[${index}].family is unknown`);
    if (!Array.isArray(item.metrics) || item.metrics.length < 2) errors.push(`methods[${index}].metrics must contain at least 2 entries`);
    if (!item.sourceUrl.startsWith('https://')) errors.push(`methods[${index}].sourceUrl must be https`);
    if (!['baseline', 'conditional', 'research'].includes(item.adoption)) errors.push(`methods[${index}].adoption is invalid`);
  });
  const actionIds = new Set((lab.actions || []).map((item) => item.id));
  (lab.scenarios || []).forEach((item, index) => {
    for (const field of ['id', 'title', 'symptom', 'expected', 'misconception', 'principle']) requireText(item[field], `scenarios[${index}].${field}`);
    if (!actionIds.has(item.expected)) errors.push(`scenarios[${index}].expected is unknown`);
    if (!Array.isArray(item.signals) || item.signals.length < 1) errors.push(`scenarios[${index}].signals must be non-empty`);
    if (!Array.isArray(item.evidence) || item.evidence.length < 2) errors.push(`scenarios[${index}].evidence must contain at least 2 entries`);
  });
  (lab.projects || []).forEach((item, index) => {
    for (const field of ['id', 'name', 'role', 'status', 'commit', 'verified', 'limit', 'sourceUrl']) requireText(item[field], `projects[${index}].${field}`);
    if (!/^[a-f0-9]{40}$/.test(item.commit)) errors.push(`projects[${index}].commit must be a full SHA`);
    if (!item.sourceUrl.includes(item.commit)) errors.push(`projects[${index}].sourceUrl must be commit-pinned`);
    if (!Array.isArray(item.sourcePaths) || item.sourcePaths.length < 2) errors.push(`projects[${index}].sourcePaths must contain at least 2 paths`);
    if (!['current', 'monitor', 'historical'].includes(item.lifecycle)) errors.push(`projects[${index}].lifecycle is invalid`);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(item.activityAt)) errors.push(`projects[${index}].activityAt must be YYYY-MM-DD`);
  });
  (lab.sources || []).forEach((item, index) => {
    for (const field of ['id', 'label', 'kind', 'url', 'lifecycle', 'reviewedAt']) requireText(item[field], `sources[${index}].${field}`);
    if (!['current', 'monitor', 'historical'].includes(item.lifecycle)) errors.push(`sources[${index}].lifecycle is invalid`);
  });
  if (!Array.isArray(lab.sourcePolicy?.retired) || lab.sourcePolicy.retired.length < 2) errors.push('sourcePolicy.retired must record at least 2 retired items');
  if (lab.sources.some((item) => item.url.includes('langchain-classic/retrievers/parent_document_retriever'))) errors.push('legacy ParentDocumentRetriever must not remain in active sources');
  if (!Array.isArray(lab.future) || !lab.future.some((item) => item.kind === 'evidence') || !lab.future.some((item) => item.kind === 'inference')) errors.push('future must separate evidence and inference');
}

const evalSuite = JSON.parse(readFileSync(resolve(repoRoot, 'agent-runtime-gateway/22-评测集/rag-diagnostic-baseline.json'), 'utf8'));
if (!Array.isArray(evalSuite.cases) || evalSuite.cases.length < 16) errors.push('RAG diagnostic eval must contain at least 16 cases');
const evalIds = new Set((evalSuite.cases || []).map((item) => item.id));
if (evalIds.size !== (evalSuite.cases || []).length) errors.push('RAG diagnostic eval ids must be unique');
const explicitAssertions = (evalSuite.cases || []).reduce((total, item) => total + (item.assertions?.length || 0), 0);
if (explicitAssertions < 64) errors.push('RAG diagnostic eval must contain at least 64 assertions');

const guide = readFileSync(resolve(repoRoot, 'agent-runtime-gateway/07-RAG问题诊断与优化/RAG全链路提升与工业最佳实践-2026.md'), 'utf8');
for (const project of lab?.projects || []) {
  if (!guide.includes(project.sourceUrl)) errors.push(`RAG guide is missing commit-pinned source: ${project.sourceUrl}`);
}
for (const requiredSection of ['一句话定义', '十层主线', '二十五条提升路径', 'GitHub 源码审计', '五道自测', '一页速记与预习核对', '2026 证据与未来走向']) {
  if (!guide.includes(requiredSection)) errors.push(`RAG guide is missing section: ${requiredSection}`);
}

const learningPath = readFileSync(resolve(repoRoot, 'agent-runtime-gateway/07-RAG问题诊断与优化/RAG与Vibe-Coding工程学习路径-2026.md'), 'utf8');
for (const requiredSection of ['一句话定义与关键概念', '七阶段学习路径', 'RAG 专用完整提示词', '工业最佳实践', '五道自测', '一页速记与预习核对']) {
  if (!learningPath.includes(requiredSection)) errors.push(`RAG vibe learning path is missing section: ${requiredSection}`);
}
const route = readFileSync(resolve(repoRoot, 'agent-runtime-gateway/07-RAG问题诊断与优化/RAG教学路线总览.md'), 'utf8');
if (route.includes('| RAG-05 |') || route.includes('RAG逐课教学手册')) errors.push('current RAG route must not restore the retired method-first sequence');
const ragIndex = readFileSync(resolve(repoRoot, 'agent-runtime-gateway/07-RAG问题诊断与优化/00-RAG索引.md'), 'utf8');
if (!ragIndex.includes('已退出主线的参考档案') || !ragIndex.includes('RAG与Vibe-Coding工程学习路径-2026.md')) errors.push('RAG index must separate current path from retired reference archives');
const maintenance = readFileSync(resolve(repoRoot, 'MAINTENANCE.md'), 'utf8');
for (const requiredSection of ['来源分级', '资料准入与淘汰', '标准更新流程', '发布阻塞规则']) {
  if (!maintenance.includes(requiredSection)) errors.push(`maintenance guide is missing section: ${requiredSection}`);
}

const frontend = readFileSync(resolve(repoRoot, 'index.html'), 'utf8');
for (const marker of ['data/rag_lab.js', 'data-view-panel="rag"', 'renderRagLab()', 'ragLabReady', 'id="ragPathList"', 'id="ragMethodSearch"', 'id="ragSourceSummary"', 'openRagVibeGuide', 'openMaintenanceGuide']) {
  if (!frontend.includes(marker)) errors.push(`frontend is missing RAG integration marker: ${marker}`);
}
if ((frontend.match(/data-rag-target=/g) || []).length < 5) errors.push('frontend must expose the five-step RAG section navigation');
if (!frontend.includes('id="mobileBottomNav"') || (frontend.match(/class="mobile-nav-button"/g) || []).length !== 8) errors.push('frontend must expose eight stable mobile navigation buttons');
if (frontend.includes('repeat(7, minmax(0, 1fr))')) errors.push('frontend contains a stale seven-column mobile navigation rule');

const courseGate = readFileSync(resolve(dataDir, 'course_gate.js'), 'utf8');
if (!courseGate.includes('input.ragLabReady')) errors.push('course gate must require ragLabReady');

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}
console.log(`OK: ${lab.pipeline.length} stages, ${lab.methods.length} improvement paths, ${lab.scenarios.length} diagnostic scenarios, ${lab.projects.length} source-audited projects, ${lab.sources.length} sources, ${evalSuite.cases.length} eval cases.`);
