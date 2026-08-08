import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('./observability_lab.js', import.meta.url), 'utf8');
const context = { globalThis: {} };
context.globalThis.globalThis = context.globalThis;
vm.runInNewContext(source, context);
const lab = context.globalThis.OBSERVABILITY_LAB;

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(lab && typeof lab === 'object', 'OBSERVABILITY_LAB missing');
assert(Array.isArray(lab.signals) && lab.signals.length === 5, 'five signal types required');
assert(Array.isArray(lab.trace) && lab.trace.length >= 5, 'trace topology is incomplete');
assert(Array.isArray(lab.rules) && lab.rules.length >= 8, 'SLO/alert rules are incomplete');
assert(Array.isArray(lab.responses) && lab.responses.map((item) => item.id).join(',') === 'page,ticket,observe', 'incident responses are incomplete');
assert(Array.isArray(lab.scenarios) && lab.scenarios.length >= 8, 'incident scenarios are incomplete');
assert(Array.isArray(lab.sources) && lab.sources.length >= 13, 'primary sources are incomplete');
assert(Array.isArray(lab.future) && lab.future.some((item) => item.kind === 'evidence') && lab.future.some((item) => item.kind === 'inference'), 'future claims must separate evidence and inference');

for (const field of ['signals', 'trace', 'scenarios']) {
  const ids = lab[field].map((item) => item.id);
  assert(new Set(ids).size === ids.length, `${field} ids must be unique`);
}
for (const scenario of lab.scenarios) {
  assert(['page', 'ticket', 'observe'].includes(scenario.expected), `invalid response for ${scenario.id}`);
  assert(scenario.reason && scenario.misconception && scenario.evidence, `teaching feedback incomplete for ${scenario.id}`);
  assert(Array.isArray(scenario.signalIds) && scenario.signalIds.length >= 2, `signal path incomplete for ${scenario.id}`);
}
for (const sourceItem of lab.sources) assert(/^https:\/\//.test(sourceItem.url), `source URL invalid: ${sourceItem.name}`);

const manifest = JSON.parse(readFileSync(new URL('../agent-runtime-gateway/22-评测集/s7-observability-manifest.json', import.meta.url), 'utf8'));
const adversarial = JSON.parse(readFileSync(new URL('../agent-runtime-gateway/22-评测集/s7-observability-adversarial.json', import.meta.url), 'utf8'));
assert(manifest.cases.length === lab.baseline.runs, 'frontend run count drifted from manifest');
assert(manifest.cases.reduce((total, item) => total + item.assertions.length, 0) === lab.baseline.assertions, 'frontend assertion count drifted from manifest');
assert(adversarial.cases.length === lab.baseline.attacks, 'frontend attack count drifted from suite');

console.log(`OK: ${lab.signals.length} signals, ${lab.rules.length} rules, ${lab.scenarios.length} scenarios, ${adversarial.cases.length} adversarial cases.`);
