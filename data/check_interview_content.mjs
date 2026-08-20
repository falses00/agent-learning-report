import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const dataDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(dataDir, '..');
const context = vm.createContext({ globalThis: {} });
vm.runInContext(readFileSync(resolve(dataDir, 'interview_lab.js'), 'utf8'), context);
const lab = context.INTERVIEW_LAB || context.globalThis?.INTERVIEW_LAB;
const errors = [];

const requireText = (value, path) => {
  if (typeof value !== 'string' || !value.trim()) errors.push(`${path} must be non-empty text`);
};
const unique = (items, path) => {
  const ids = items.map((item) => item.id);
  if (new Set(ids).size !== ids.length) errors.push(`${path} ids must be unique`);
};

if (!lab || typeof lab !== 'object') errors.push('globalThis.INTERVIEW_LAB is missing');
else {
  for (const [field, minimum] of [['roles', 3], ['capabilities', 8], ['prepPath', 7], ['selfTests', 5], ['sources', 10]]) {
    if (!Array.isArray(lab[field]) || lab[field].length < minimum) errors.push(`${field} must contain at least ${minimum} entries`);
    else unique(lab[field], field);
  }
  if (!Array.isArray(lab.answerFrame) || lab.answerFrame.length !== 6) errors.push('answerFrame must contain six evidence prompts');
  else unique(lab.answerFrame, 'answerFrame');
  for (const field of ['reviewedAt', 'reviewDueAt', 'definition', 'truthBoundary']) requireText(lab[field], field);

  const capabilityIds = new Set((lab.capabilities || []).map((item) => item.id));
  const sourceIds = new Set((lab.sources || []).map((item) => item.id));
  (lab.roles || []).forEach((role, index) => {
    for (const field of ['id', 'label', 'target', 'interviewFocus', 'proof']) requireText(role[field], `roles[${index}].${field}`);
    if (!role.priorities || Object.keys(role.priorities).length !== capabilityIds.size) errors.push(`roles[${index}].priorities must cover every capability`);
    for (const id of role.sourceIds || []) if (!sourceIds.has(id)) errors.push(`roles[${index}] references unknown source ${id}`);
  });
  (lab.capabilities || []).forEach((item, index) => {
    for (const field of ['id', 'label', 'course', 'chapter', 'remember', 'explain', 'failure', 'evidence']) requireText(item[field], `capabilities[${index}].${field}`);
  });
  const challenge = lab.challenge;
  if (!challenge || typeof challenge !== 'object') errors.push('challenge is missing');
  else {
    for (const field of ['id', 'title', 'level', 'duration', 'prompt']) requireText(challenge[field], `challenge.${field}`);
    if (!Array.isArray(challenge.constraints) || challenge.constraints.length < 7) errors.push('challenge.constraints must contain at least 7 constraints');
    if (!Array.isArray(challenge.phases) || challenge.phases.length < 7) errors.push('challenge.phases must contain at least 7 phases');
    else {
      unique(challenge.phases, 'challenge.phases');
      for (const [index, phase] of challenge.phases.entries()) {
        for (const field of ['id', 'label', 'question', 'trap', 'review']) requireText(phase[field], `challenge.phases[${index}].${field}`);
        if (!Array.isArray(phase.mustCover) || phase.mustCover.length < 4) errors.push(`challenge.phases[${index}].mustCover must contain at least 4 items`);
      }
    }
    if (!Array.isArray(challenge.rubric) || challenge.rubric.reduce((sum, item) => sum + item.points, 0) !== 100) errors.push('challenge.rubric must total 100 points');
    else unique(challenge.rubric, 'challenge.rubric');
    if (!Array.isArray(challenge.autoFail) || challenge.autoFail.length < 4) errors.push('challenge.autoFail must contain at least 4 hard failures');
  }
  (lab.selfTests || []).forEach((item, index) => {
    for (const field of ['id', 'domain', 'question', 'misconception']) requireText(item[field], `selfTests[${index}].${field}`);
    if (!capabilityIds.has(item.domain)) errors.push(`selfTests[${index}].domain is unknown`);
    if (!Array.isArray(item.options) || item.options.length !== 4) errors.push(`selfTests[${index}].options must contain 4 choices`);
    if (!Number.isInteger(item.answer) || item.answer < 0 || item.answer > 3) errors.push(`selfTests[${index}].answer is invalid`);
  });
  (lab.sources || []).forEach((source, index) => {
    for (const field of ['id', 'kind', 'company', 'title', 'signal', 'status', 'checkedAt', 'url']) requireText(source[field], `sources[${index}].${field}`);
    if (source.status !== 'current') errors.push(`sources[${index}] must be current or leave the active dataset`);
    if (!source.url.startsWith('https://')) errors.push(`sources[${index}].url must be https`);
  });
}

const guidePath = resolve(repoRoot, 'agent-runtime-gateway/00-课程总览/大厂Agent岗位面试知识地图-2026.md');
const guide = readFileSync(guidePath, 'utf8');
for (const section of ['一句话定义与真实性边界', '最新官方岗位交集', '必须记住的八域知识', '面试难题', '100 分评分尺', '五道自测', '一页速记清单', '面试前预习核对清单', '资料维护门禁']) {
  if (!guide.includes(section)) errors.push(`interview guide is missing section: ${section}`);
}
for (const source of lab?.sources || []) {
  if (!guide.includes(source.url)) errors.push(`interview guide is missing official source: ${source.url}`);
}

const frontend = readFileSync(resolve(repoRoot, 'index.html'), 'utf8');
for (const marker of ['data/interview_lab.js', 'data-view-panel="interview"', 'renderInterviewLab()', 'id="interviewRoleTabs"', 'id="interviewChallengeDraft"', 'id="interviewRubric"', 'openInterviewGuide']) {
  if (!frontend.includes(marker)) errors.push(`frontend is missing interview integration marker: ${marker}`);
}
if (!frontend.includes('id="mobileBottomNav"') || (frontend.match(/class="mobile-nav-button"/g) || []).length !== 9) errors.push('frontend must expose nine stable mobile navigation buttons');

const maintenance = readFileSync(resolve(repoRoot, 'MAINTENANCE.md'), 'utf8');
for (const marker of ['面试岗位证据', '30 天', '官方岗位']) {
  if (!maintenance.includes(marker)) errors.push(`maintenance guide is missing interview lifecycle marker: ${marker}`);
}

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}
console.log(`OK: ${lab.roles.length} roles, ${lab.capabilities.length} capability domains, ${lab.challenge.phases.length} challenge phases, ${lab.selfTests.length} self-tests, ${lab.sources.length} current official sources.`);
