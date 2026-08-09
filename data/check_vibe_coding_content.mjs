import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const dataDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(dataDir, '..');
const sandbox = { globalThis: {} };
sandbox.globalThis.globalThis = sandbox.globalThis;
vm.runInNewContext(readFileSync(resolve(dataDir, 'vibe_coding.js'), 'utf8'), sandbox);
const content = sandbox.globalThis.VIBE_CODING;
const errors = [];

const requireText = (value, path) => {
  if (typeof value !== 'string' || !value.trim()) errors.push(`${path} must be non-empty text`);
};
const unique = (items, path) => {
  const ids = items.map((item) => item.id);
  if (new Set(ids).size !== ids.length) errors.push(`${path} ids must be unique`);
};

if (!content || typeof content !== 'object') errors.push('window.VIBE_CODING is missing');
else {
  requireText(content.definition, 'definition');
  requireText(content.principle, 'principle');
  requireText(content.taskContract, 'taskContract');
  for (const [field, count] of [['modes', 3], ['loop', 7], ['guardrails', 8], ['antiPatterns', 8], ['sources', 10]]) {
    if (!Array.isArray(content[field]) || content[field].length < count) errors.push(`${field} must contain at least ${count} entries`);
  }
  unique(content.modes || [], 'modes');
  unique(content.loop || [], 'loop');
  unique(content.antiPatterns || [], 'antiPatterns');
  unique(content.sources || [], 'sources');
  for (const [index, step] of (content.loop || []).entries()) {
    for (const field of ['id', 'name', 'action', 'artifact', 'failure']) requireText(step[field], `loop[${index}].${field}`);
  }
  for (const [index, mode] of (content.modes || []).entries()) {
    for (const field of ['id', 'name', 'fit', 'autonomy', 'exit']) requireText(mode[field], `modes[${index}].${field}`);
  }
}

const guide = readFileSync(resolve(repoRoot, 'agent-runtime-gateway/00-课程总览/Vibe-Coding最佳实践-2026.md'), 'utf8');
for (const source of content?.sources || []) {
  if (!guide.includes(source.url)) errors.push(`guide is missing source: ${source.url}`);
}
for (const marker of ['一句话定义', '五道自测', '一页速记', '预习核对清单', '退出 Vibe Coding']) {
  if (!guide.includes(marker)) errors.push(`guide is missing teaching marker: ${marker}`);
}

const frontend = readFileSync(resolve(repoRoot, 'index.html'), 'utf8');
for (const marker of ['data/vibe_coding.js', 'vibePractice', 'renderVibePractice()', 'openVibeGuide']) {
  if (!frontend.includes(marker)) errors.push(`frontend is missing Vibe Coding marker: ${marker}`);
}

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}
console.log(`OK: ${content.modes.length} modes, ${content.loop.length} workflow steps, ${content.guardrails.length} guardrails, ${content.antiPatterns.length} anti-patterns, ${content.sources.length} sources.`);
