import { readFileSync, readdirSync } from "node:fs";
import { join, relative } from "node:path";

const root = process.cwd();
const ignoredDirs = new Set([".git", ".next", "node_modules", "out", "dist", "build"]);
const textExtensions = new Set([
  ".css",
  ".env",
  ".example",
  ".json",
  ".js",
  ".jsx",
  ".md",
  ".mjs",
  ".ts",
  ".tsx",
  ".txt",
  ".yml",
  ".yaml",
]);

const secretPatterns = [
  { name: "hardcoded secret-like token", regex: /sk-[A-Za-z0-9_-]{20,}/g },
  { name: "filled AGNES_API_KEY assignment", regex: /AGNES_API_KEY\s*=\s*[^#\s][^\r\n]*/g },
  { name: "client-exposed Agnes variable", regex: /NEXT_PUBLIC_[A-Z0-9_]*AGNES[A-Z0-9_]*/g },
  { name: "hardcoded bearer token", regex: /Bearer\s+[A-Za-z0-9_.-]{20,}/g },
];

const findings = [];

function hasTextExtension(filePath) {
  const lower = filePath.toLowerCase();
  return Array.from(textExtensions).some((extension) => lower.endsWith(extension));
}

function walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      if (!ignoredDirs.has(entry.name)) walk(join(dir, entry.name));
      continue;
    }
    const filePath = join(dir, entry.name);
    if (hasTextExtension(filePath)) scanFile(filePath);
  }
}

function scanFile(filePath) {
  const rel = relative(root, filePath);
  const content = readFileSync(filePath, "utf8");
  const lines = content.split(/\r?\n/);

  for (const [lineIndex, line] of lines.entries()) {
    for (const pattern of secretPatterns) {
      pattern.regex.lastIndex = 0;
      if (!pattern.regex.test(line)) continue;

      if (/^AGNES_API_KEY\s*=\s*$/.test(line.trim())) continue;
      if (/^AGNES_API_KEY\s*=\s*(\.\.\.|<[^>]+>)\s*$/.test(line.trim())) continue;
      if (pattern.name === "client-exposed Agnes variable" && isWarningDocLine(rel, line)) continue;
      findings.push({
        file: rel,
        line: lineIndex + 1,
        type: pattern.name,
      });
    }
  }
}

function isWarningDocLine(filePath, line) {
  return filePath.toLowerCase().endsWith(".md") && /不要|禁止|never|do not/i.test(line);
}

walk(root);

if (findings.length) {
  console.error("Secret scan failed. Values are intentionally redacted:");
  for (const finding of findings) {
    console.error(`- ${finding.file}:${finding.line} ${finding.type}`);
  }
  process.exit(1);
}

console.log("Secret scan passed. No secret-like Agnes keys were found in scanned text files.");
console.log(`Scanned from: ${root}`);
