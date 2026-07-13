import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const dataDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(dataDir, '..');
const context = vm.createContext({ window: {} });
vm.runInContext(readFileSync(resolve(dataDir, 'memory_lab.js'), 'utf8'), context);

const lab = context.window.MEMORY_LAB;
const errors = [];
const requireText = (value, path) => {
  if (typeof value !== 'string' || !value.trim()) errors.push(`${path} must be non-empty text`);
};
const requireUniqueIds = (items, path) => {
  const ids = items.map((item) => item.id);
  if (new Set(ids).size !== ids.length) errors.push(`${path} ids must be unique`);
};

if (!lab || typeof lab !== 'object') {
  errors.push('window.MEMORY_LAB is missing');
} else {
  if (!Array.isArray(lab.methods) || lab.methods.length !== 14) errors.push('methods must contain exactly 14 entries');
  else {
    requireUniqueIds(lab.methods, 'methods');
    lab.methods.forEach((item, index) => {
      for (const field of ['id', 'name', 'family', 'principle', 'bestFor', 'advantages', 'tradeoffs', 'failure', 'status', 'sourceLabel']) requireText(item[field], `methods[${index}].${field}`);
      if (!Number.isInteger(item.year) || item.year < 2020 || item.year > 2026) errors.push(`methods[${index}].year is invalid`);
      if (typeof item.sourceUrl !== 'string' || !item.sourceUrl.startsWith('https://')) errors.push(`methods[${index}].sourceUrl must be https`);
    });
  }

  if (!Array.isArray(lab.scenarios) || lab.scenarios.length < 7) errors.push('scenarios must contain at least 7 entries');
  else {
    requireUniqueIds(lab.scenarios, 'scenarios');
    const decisionIds = new Set(lab.decisions.map((item) => item.id));
    const lifecycleIds = new Set(lab.lifecycleSteps.map((item) => item.id));
    lab.scenarios.forEach((item, index) => {
      for (const field of ['id', 'title', 'candidate', 'source', 'sensitivity', 'scope', 'ttl', 'expected', 'memoryType', 'reason']) requireText(item[field], `scenarios[${index}].${field}`);
      if (!decisionIds.has(item.expected)) errors.push(`scenarios[${index}].expected is unknown`);
      if (!Array.isArray(item.path) || !item.path.length || item.path.some((step) => !lifecycleIds.has(step))) errors.push(`scenarios[${index}].path is invalid`);
      if (!item.audit || typeof item.audit !== 'object') errors.push(`scenarios[${index}].audit is missing`);
    });
  }

  if (!Array.isArray(lab.workloads) || lab.workloads.length < 6) errors.push('workloads must contain at least 6 entries');
  else requireUniqueIds(lab.workloads, 'workloads');
  if (!Array.isArray(lab.benchmarks) || lab.benchmarks.length < 5) errors.push('benchmarks must contain at least 5 entries');
  else lab.benchmarks.forEach((item, index) => {
    if (typeof item.sourceUrl !== 'string' || !item.sourceUrl.startsWith('https://')) errors.push(`benchmarks[${index}].sourceUrl must be https`);
  });
  if (!Array.isArray(lab.future) || !lab.future.some((item) => item.kind === 'evidence') || !lab.future.some((item) => item.kind === 'inference')) errors.push('future must separate evidence and inference');
  if (!Array.isArray(lab.metrics) || lab.metrics.length < 7) errors.push('metrics must contain at least 7 entries');
}

const evalPath = resolve(repoRoot, 'agent-runtime-gateway/22-评测集/memory-engineering-baseline.jsonl');
const guidePath = resolve(repoRoot, 'agent-runtime-gateway/06-工业级框架蓝图/Agent-Memory方法谱系与工业选型-2026.md');
const guide = readFileSync(guidePath, 'utf8');
for (const section of ['代表方法对比', '工业选型', '删除传播', '评测', '未来', '一页速记', '预习核对']) {
  if (!guide.includes(section)) errors.push(`memory guide is missing section: ${section}`);
}
for (const item of [...(lab?.methods || []), ...(lab?.benchmarks || [])]) {
  if (item.sourceUrl && !guide.includes(item.sourceUrl)) errors.push(`memory guide is missing primary source: ${item.sourceUrl}`);
}
const evalLines = readFileSync(evalPath, 'utf8').split(/\r?\n/).filter(Boolean);
const evalCases = [];
for (const [index, line] of evalLines.entries()) {
  try { evalCases.push(JSON.parse(line)); }
  catch (error) { errors.push(`eval line ${index + 1} is invalid JSON: ${error.message}`); }
}
if (evalCases.length < 12) errors.push('memory eval set must contain at least 12 cases');
else {
  requireUniqueIds(evalCases, 'evalCases');
  evalCases.forEach((item, index) => {
    for (const field of ['id', 'category', 'operation', 'input', 'expected_decision']) requireText(item[field], `evalCases[${index}].${field}`);
    if (!Array.isArray(item.assertions) || !item.assertions.length) errors.push(`evalCases[${index}].assertions must be non-empty`);
    if (typeof item.critical !== 'boolean') errors.push(`evalCases[${index}].critical must be boolean`);
  });
}

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}

console.log(`OK: ${lab.methods.length} memory methods, ${lab.scenarios.length} lab scenarios, ${lab.workloads.length} workload profiles, ${evalCases.length} eval cases.`);
