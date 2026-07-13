import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const dataDir = dirname(fileURLToPath(import.meta.url));
const context = vm.createContext({ window: {} });
vm.runInContext(readFileSync(resolve(dataDir, 'learning_content.js'), 'utf8'), context);

const content = context.window.LEARNING_CONTENT;
const expectedStages = ['f0', 's0', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10'];
const errors = [];
const prompts = new Set();

function requireText(value, path) {
  if (typeof value !== 'string' || !value.trim()) errors.push(`${path} must be non-empty text`);
}

if (!content || typeof content !== 'object') {
  errors.push('window.LEARNING_CONTENT is missing');
} else {
  const actualStages = Object.keys(content);
  if (actualStages.join(',') !== expectedStages.join(',')) {
    errors.push(`stages must be exactly: ${expectedStages.join(', ')}`);
  }

  for (const stageId of expectedStages) {
    const stage = content[stageId];
    if (!stage) continue;
    if (!Array.isArray(stage.prerequisites) || stage.prerequisites.length !== 3) errors.push(`${stageId}.prerequisites must contain 3 items`);
    else stage.prerequisites.forEach((item, index) => requireText(item, `${stageId}.prerequisites[${index}]`));

    if (!Array.isArray(stage.concepts) || stage.concepts.length !== 4) errors.push(`${stageId}.concepts must contain 4 items`);
    else stage.concepts.forEach((item, index) => requireText(item, `${stageId}.concepts[${index}]`));

    for (const field of ['title', 'context', 'symptom', 'lesson']) requireText(stage.caseStudy?.[field], `${stageId}.caseStudy.${field}`);
    requireText(stage.workshop?.title, `${stageId}.workshop.title`);
    requireText(stage.workshop?.evidence, `${stageId}.workshop.evidence`);
    if (!Array.isArray(stage.workshop?.steps) || stage.workshop.steps.length !== 3) errors.push(`${stageId}.workshop.steps must contain 3 items`);
    else stage.workshop.steps.forEach((item, index) => requireText(item, `${stageId}.workshop.steps[${index}]`));

    if (!Array.isArray(stage.quiz) || stage.quiz.length !== 5) {
      errors.push(`${stageId}.quiz must contain 5 questions`);
      continue;
    }
    stage.quiz.forEach((question, index) => {
      const base = `${stageId}.quiz[${index}]`;
      for (const field of ['prompt', 'category', 'misconception', 'explanation', 'example', 'experiment']) requireText(question[field], `${base}.${field}`);
      if (prompts.has(question.prompt)) errors.push(`${base}.prompt is duplicated`);
      prompts.add(question.prompt);
      if (!Array.isArray(question.options) || question.options.length !== 4) errors.push(`${base}.options must contain 4 choices`);
      else question.options.forEach((option, optionIndex) => requireText(option, `${base}.options[${optionIndex}]`));
      if (!Number.isInteger(question.answer) || question.answer < 0 || question.answer > 3) errors.push(`${base}.answer must be an option index from 0 to 3`);
      if (typeof question.critical !== 'boolean') errors.push(`${base}.critical must be boolean`);
    });
    if (!stage.quiz.some((question) => question.critical)) errors.push(`${stageId}.quiz needs at least one critical question`);
  }
}

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}

console.log(`OK: ${expectedStages.length} stages, ${prompts.size} questions, structured teaching content is valid.`);
