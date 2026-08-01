import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const dataDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(dataDir, '..');
const context = vm.createContext({ window: {} });
vm.runInContext(readFileSync(resolve(dataDir, 'eval_lab.js'), 'utf8'), context);

const lab = context.window.EVAL_LAB;
const errors = [];
const requireText = (value, path) => {
  if (typeof value !== 'string' || !value.trim()) errors.push(`${path} must be non-empty text`);
};
const requireUniqueIds = (items, path) => {
  const ids = items.map((item) => item.id);
  if (new Set(ids).size !== ids.length) errors.push(`${path} ids must be unique`);
};

if (!lab || typeof lab !== 'object') {
  errors.push('window.EVAL_LAB is missing');
} else {
  if (!Array.isArray(lab.pipeline) || lab.pipeline.length < 7) errors.push('pipeline must contain at least 7 steps');
  else requireUniqueIds(lab.pipeline, 'pipeline');
  if (!Array.isArray(lab.rules) || lab.rules.length < 8) errors.push('rules must contain at least 8 gate rules');
  else requireUniqueIds(lab.rules, 'rules');
  if (!Array.isArray(lab.scenarios) || lab.scenarios.length < 8) errors.push('scenarios must contain at least 8 entries');
  else {
    requireUniqueIds(lab.scenarios, 'scenarios');
    const decisions = new Set(lab.decisions.map((item) => item.id));
    const pipeline = new Set(lab.pipeline.map((item) => item.id));
    lab.scenarios.forEach((item, index) => {
      for (const field of ['id', 'title', 'profile', 'score', 'expected', 'blocker', 'prompt', 'reason', 'misconception', 'evidence']) requireText(item[field], `scenarios[${index}].${field}`);
      if (!decisions.has(item.expected)) errors.push(`scenarios[${index}].expected is unknown`);
      if (!Array.isArray(item.pipeline) || !item.pipeline.length || item.pipeline.some((step) => !pipeline.has(step))) errors.push(`scenarios[${index}].pipeline is invalid`);
    });
  }
  if (!Array.isArray(lab.sources) || lab.sources.length < 7) errors.push('sources must contain at least 7 primary references');
  else lab.sources.forEach((item, index) => {
    for (const field of ['name', 'focus', 'url']) requireText(item[field], `sources[${index}].${field}`);
    if (!item.url.startsWith('https://')) errors.push(`sources[${index}].url must be https`);
  });
  if (!Array.isArray(lab.future) || !lab.future.some((item) => item.kind === 'evidence') || !lab.future.some((item) => item.kind === 'inference')) errors.push('future must separate evidence and inference');
}

const evalDir = resolve(repoRoot, 'agent-runtime-gateway/22-评测集');
const manifest = JSON.parse(readFileSync(resolve(evalDir, 's6-release-manifest.json'), 'utf8'));
const adversarial = JSON.parse(readFileSync(resolve(evalDir, 's6-release-gate-adversarial.json'), 'utf8'));
const publicHoldout = JSON.parse(readFileSync(resolve(evalDir, 's6-holdout-public-example.json'), 'utf8'));
if (manifest.schema_version !== '1.0') errors.push('release manifest schema_version must be 1.0');
if (!Array.isArray(manifest.source_suites) || manifest.source_suites.length < 5) errors.push('release manifest must aggregate at least 5 source suites');
if (!Array.isArray(manifest.judge_calibration) || manifest.judge_calibration.length < 10) errors.push('judge calibration needs at least 10 examples');
if (!Array.isArray(manifest.red_team) || manifest.red_team.length < 5) errors.push('release manifest needs at least 5 red-team families');
if (!Array.isArray(manifest.regressions) || manifest.regressions.length < 4) errors.push('release manifest needs at least 4 owned regressions');
if (!Array.isArray(adversarial.cases) || adversarial.cases.length < 16) errors.push('gate adversarial set must contain at least 16 cases');
if (!Array.isArray(publicHoldout.cases) || publicHoldout.cases.length < 4) errors.push('public holdout example must contain at least 4 cases');

const guidePath = resolve(repoRoot, 'agent-runtime-gateway/labs/S06-eval-red-team/README.md');
const guide = readFileSync(guidePath, 'utf8');
for (const section of ['一句话定义', '八个关键概念', '攻击门禁本身', '五道自测', '一页速记清单', '通过与预习核对', '未来走向']) {
  if (!guide.includes(section)) errors.push(`S6 guide is missing section: ${section}`);
}
for (const source of lab?.sources || []) {
  if (!guide.includes(source.url)) errors.push(`S6 guide is missing primary source: ${source.url}`);
}

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}

console.log(`OK: ${lab.pipeline.length} pipeline steps, ${lab.rules.length} gate rules, ${lab.scenarios.length} lab scenarios, ${adversarial.cases.length} adversarial cases.`);
