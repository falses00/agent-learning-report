import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const dataDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(dataDir, '..');
const sandbox = { globalThis: {} };
sandbox.globalThis.globalThis = sandbox.globalThis;
vm.runInNewContext(readFileSync(resolve(dataDir, 'security_lab.js'), 'utf8'), sandbox);
const lab = sandbox.globalThis.SECURITY_LAB;
const errors = [];

const requireText = (value, path) => {
  if (typeof value !== 'string' || !value.trim()) errors.push(`${path} must be non-empty text`);
};
const unique = (items, path) => {
  const ids = items.map((item) => item.id);
  if (new Set(ids).size !== ids.length) errors.push(`${path} ids must be unique`);
};

if (!lab || typeof lab !== 'object') errors.push('window.SECURITY_LAB is missing');
else {
  for (const [field, minimum] of [['controls', 9], ['scenarios', 10], ['projects', 6], ['sources', 10]]) {
    if (!Array.isArray(lab[field]) || lab[field].length < minimum) errors.push(`${field} must contain at least ${minimum} entries`);
    else unique(lab[field], field);
  }
  const decisions = new Set((lab.decisions || []).map((item) => item.id));
  for (const [index, scenario] of (lab.scenarios || []).entries()) {
    for (const field of ['id', 'title', 'observation', 'expected', 'blocker', 'reason', 'misconception']) requireText(scenario[field], `scenarios[${index}].${field}`);
    if (!decisions.has(scenario.expected)) errors.push(`scenarios[${index}].expected is invalid`);
    if (!Array.isArray(scenario.evidence) || scenario.evidence.length < 3) errors.push(`scenarios[${index}].evidence must contain at least 3 entries`);
  }
  for (const [index, project] of (lab.projects || []).entries()) {
    for (const field of ['id', 'name', 'role', 'status', 'commit', 'sourceUrl', 'verified', 'limit']) requireText(project[field], `projects[${index}].${field}`);
    if (!/^[a-f0-9]{40}$/.test(project.commit)) errors.push(`projects[${index}].commit must be a full SHA`);
    if (!project.sourceUrl.includes(project.commit)) errors.push(`projects[${index}].sourceUrl must be commit-pinned`);
    if (!Array.isArray(project.sourcePaths) || project.sourcePaths.length < 3) errors.push(`projects[${index}].sourcePaths must contain at least 3 paths`);
  }
  if (!Array.isArray(lab.future) || !lab.future.some((item) => item.kind === 'evidence') || !lab.future.some((item) => item.kind === 'inference')) errors.push('future must separate evidence and inference');
}

const suite = JSON.parse(readFileSync(resolve(repoRoot, 'agent-runtime-gateway/22-评测集/s8-security-adversarial.json'), 'utf8'));
if (!Array.isArray(suite.cases) || suite.cases.length < 25) errors.push('S8 security suite must contain at least 25 cases');
if (new Set((suite.cases || []).map((item) => item.id)).size !== (suite.cases || []).length) errors.push('S8 security case ids must be unique');
if (!(suite.cases || []).every((item) => item.critical === true)) errors.push('every committed S8 case must be release-critical');

const guide = readFileSync(resolve(repoRoot, 'agent-runtime-gateway/02-阶段教学手册/Phase-09-安全隔离与沙箱教学手册.md'), 'utf8');
for (const source of lab?.sources || []) {
  if (!guide.includes(source.url)) errors.push(`S8 guide is missing source: ${source.url}`);
}
for (const project of lab?.projects || []) {
  if (!guide.includes(project.sourceUrl)) errors.push(`S8 guide is missing commit-pinned project: ${project.sourceUrl}`);
}

const frontend = readFileSync(resolve(repoRoot, 'index.html'), 'utf8');
for (const marker of ['data/security_lab.js', 'data-view-panel="security"', 'renderSecurityLab()', 'securityLabReady']) {
  if (!frontend.includes(marker)) errors.push(`frontend is missing S8 marker: ${marker}`);
}
const gate = readFileSync(resolve(dataDir, 'course_gate.js'), 'utf8');
if (!gate.includes('input.securityLabReady')) errors.push('course gate must require securityLabReady');

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}
console.log(`OK: ${lab.controls.length} controls, ${lab.scenarios.length} scenarios, ${lab.projects.length} source-audited projects, ${lab.sources.length} sources, ${suite.cases.length} critical cases.`);
