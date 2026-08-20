import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('.', import.meta.url)), '..');
const html = readFileSync(resolve(root, 'index.html'), 'utf8');
const chapters = readFileSync(resolve(root, 'data/chapters.js'), 'utf8');
const errors = [];

for (const marker of [
  'id="readingStatus"',
  'role="progressbar"',
  'id="readingProgressFill"',
  'id="documentOutline"',
  'id="documentOutlineNav"',
  'class="reader-layout"',
  'function buildDocumentOutline()',
  'function updateReaderNavigation()',
  'function estimateReadingTime(content)',
  '约 ${estimateReadingTime(chapter.content)} 分钟',
  "prefers-reduced-motion: reduce",
  'updateReaderNavigation();',
]) {
  if (!html.includes(marker)) errors.push(`reader is missing marker: ${marker}`);
}

for (const style of [
  '.reader-layout {',
  '.document-outline {',
  '.document-outline a.active {',
  '.reading-progress-fill {',
  'grid-template-columns: minmax(0, 76ch)',
]) {
  if (!html.includes(style)) errors.push(`reader is missing style contract: ${style}`);
}

const chapterCount = (chapters.match(/"id":/g) || []).length;
if (chapterCount < 30) errors.push(`expected at least 30 generated chapters, found ${chapterCount}`);

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}

console.log(`OK: reader outline, progress, responsive layout, and ${chapterCount} generated chapters.`);
