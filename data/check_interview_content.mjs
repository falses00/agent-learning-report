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
  for (const [field, minimum] of [['roles', 4], ['capabilities', 8], ['domesticSignals', 6], ['prepPath', 7], ['selfTests', 5], ['githubProjects', 6], ['communitySignals', 4], ['sources', 20]]) {
    if (!Array.isArray(lab[field]) || lab[field].length < minimum) errors.push(`${field} must contain at least ${minimum} entries`);
    else unique(lab[field], field);
  }
  if (!Array.isArray(lab.sourceTiers) || lab.sourceTiers.length !== 3) errors.push('sourceTiers must contain A/B/C');
  else {
    unique(lab.sourceTiers, 'sourceTiers');
    if (lab.sourceTiers.map((item) => item.id).join('') !== 'ABC') errors.push('sourceTiers must be ordered A/B/C');
  }
  if (!Array.isArray(lab.markets) || lab.markets.length !== 2) errors.push('markets must contain China and global views');
  else unique(lab.markets, 'markets');
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
  (lab.domesticSignals || []).forEach((item, index) => {
    for (const field of ['id', 'label', 'strength', 'course', 'chapter', 'demand', 'prompt']) requireText(item[field], `domesticSignals[${index}].${field}`);
    if (!Array.isArray(item.sourceIds) || !item.sourceIds.length) errors.push(`domesticSignals[${index}].sourceIds must not be empty`);
    for (const id of item.sourceIds || []) if (!sourceIds.has(id)) errors.push(`domesticSignals[${index}] references unknown source ${id}`);
  });
  const validateChallenge = (challenge, path) => {
    if (!challenge || typeof challenge !== 'object') {
      errors.push(`${path} is missing`);
      return;
    }
    for (const field of ['id', 'title', 'level', 'duration', 'prompt']) requireText(challenge[field], `${path}.${field}`);
    if (!Array.isArray(challenge.constraints) || challenge.constraints.length < 7) errors.push(`${path}.constraints must contain at least 7 constraints`);
    if (!Array.isArray(challenge.phases) || challenge.phases.length < 7) errors.push(`${path}.phases must contain at least 7 phases`);
    else {
      unique(challenge.phases, `${path}.phases`);
      for (const [index, phase] of challenge.phases.entries()) {
        for (const field of ['id', 'label', 'question', 'trap', 'review']) requireText(phase[field], `${path}.phases[${index}].${field}`);
        if (!Array.isArray(phase.mustCover) || phase.mustCover.length < 4) errors.push(`${path}.phases[${index}].mustCover must contain at least 4 items`);
      }
    }
    if (!Array.isArray(challenge.rubric) || challenge.rubric.reduce((sum, item) => sum + item.points, 0) !== 100) errors.push(`${path}.rubric must total 100 points`);
    else unique(challenge.rubric, `${path}.rubric`);
    if (!Array.isArray(challenge.autoFail) || challenge.autoFail.length < 4) errors.push(`${path}.autoFail must contain at least 4 hard failures`);
  };
  validateChallenge(lab.challenge, 'challenge');
  validateChallenge(lab.domesticChallenge, 'domesticChallenge');
  (lab.selfTests || []).forEach((item, index) => {
    for (const field of ['id', 'domain', 'question', 'misconception']) requireText(item[field], `selfTests[${index}].${field}`);
    if (!capabilityIds.has(item.domain)) errors.push(`selfTests[${index}].domain is unknown`);
    if (!Array.isArray(item.options) || item.options.length !== 4) errors.push(`selfTests[${index}].options must contain 4 choices`);
    if (!Number.isInteger(item.answer) || item.answer < 0 || item.answer > 3) errors.push(`selfTests[${index}].answer is invalid`);
  });
  (lab.sources || []).forEach((source, index) => {
    for (const field of ['id', 'tier', 'scope', 'kind', 'company', 'title', 'signal', 'status', 'checkedAt', 'url']) requireText(source[field], `sources[${index}].${field}`);
    if (source.tier !== 'A') errors.push(`sources[${index}] must be tier A`);
    if (!['china', 'global'].includes(source.scope)) errors.push(`sources[${index}].scope must be china or global`);
    if (source.status !== 'current') errors.push(`sources[${index}] must be current or leave the active dataset`);
    if (!source.url.startsWith('https://')) errors.push(`sources[${index}].url must be https`);
  });
  (lab.githubProjects || []).forEach((project, index) => {
    for (const field of ['id', 'name', 'org', 'tier', 'checkedAt', 'activity', 'focus', 'question', 'limitation', 'url']) requireText(project[field], `githubProjects[${index}].${field}`);
    if (project.tier !== 'B' || !project.url.startsWith('https://github.com/')) errors.push(`githubProjects[${index}] must be tier B with a GitHub URL`);
    if (!Array.isArray(project.modules) || project.modules.length < 3) errors.push(`githubProjects[${index}].modules must contain at least three paths`);
  });
  (lab.communitySignals || []).forEach((item, index) => {
    for (const field of ['id', 'platform', 'tier', 'date', 'checkedAt', 'title', 'signal', 'training', 'bias', 'url']) requireText(item[field], `communitySignals[${index}].${field}`);
    if (item.tier !== 'C' || !item.url.startsWith('https://')) errors.push(`communitySignals[${index}] must be tier C with an https URL`);
  });
}

const guidePath = resolve(repoRoot, 'agent-runtime-gateway/00-课程总览/大厂Agent岗位面试知识地图-2026.md');
const guide = readFileSync(guidePath, 'utf8');
for (const section of ['一句话定义与真实性边界', '最新官方岗位交集', '中国国内官方岗位', '必须记住的八域知识', '面试难题', 'GitHub 上游项目深挖', 'Linux DO 与中文社区', '100 分评分尺', '五道自测', '一页速记清单', '面试前预习核对清单', '资料维护门禁']) {
  if (!guide.includes(section)) errors.push(`interview guide is missing section: ${section}`);
}
for (const source of lab?.sources || []) {
  if (!guide.includes(source.url)) errors.push(`interview guide is missing official source: ${source.url}`);
}
for (const project of lab?.githubProjects || []) {
  if (!guide.includes(project.url)) errors.push(`interview guide is missing GitHub source: ${project.url}`);
}
for (const item of lab?.communitySignals || []) {
  if (!guide.includes(item.url)) errors.push(`interview guide is missing community source: ${item.url}`);
}

const frontend = readFileSync(resolve(repoRoot, 'index.html'), 'utf8');
for (const marker of ['data/interview_lab.js', 'data-view-panel="interview"', 'renderInterviewLab()', 'id="interviewMarketTabs"', 'id="interviewRoleTabs"', 'id="interviewDomesticSignals"', 'id="interviewChallengeTabs"', 'id="interviewChallengeDraft"', 'id="interviewRubric"', 'id="interviewProjectTabs"', 'id="interviewEvidenceTabs"', 'openInterviewGuide']) {
  if (!frontend.includes(marker)) errors.push(`frontend is missing interview integration marker: ${marker}`);
}
if ((frontend.match(/data-interview-target=/g) || []).length !== 7) errors.push('frontend must expose seven interview section navigation targets');
if (!frontend.includes('id="mobileBottomNav"') || (frontend.match(/class="mobile-nav-button"/g) || []).length !== 9) errors.push('frontend must expose nine stable mobile navigation buttons');

const maintenance = readFileSync(resolve(repoRoot, 'MAINTENANCE.md'), 'utf8');
for (const marker of ['面试岗位证据', '14 天', 'A / B / C', 'GitHub', '社区经验']) {
  if (!maintenance.includes(marker)) errors.push(`maintenance guide is missing interview lifecycle marker: ${marker}`);
}

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}
console.log(`OK: ${lab.roles.length} roles, ${lab.domesticSignals.length} China signals, 2 challenges, ${lab.githubProjects.length} GitHub projects, ${lab.communitySignals.length} community samples, ${lab.sources.length} current official sources.`);
