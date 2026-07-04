import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join } from 'path';

const base = 'H:\\Creat A Agent';

const chapters = [
  { id: 'phase0', num: 'Phase 0', title: '课程总览与路线审核', meta: 'PRD · 调研 · 路线', src: 'agent-runtime-gateway\\00-课程总览\\课程地图.md', group: 'main' },
  { id: 'phase0_1', num: 'Phase 0.1', title: '半懂起步', meta: '工单故事 · 建议与执行分离', src: 'agent-runtime-gateway\\02-阶段教学手册\\Phase-00.1-半懂起步教学手册.md', group: 'main' },
  { id: 'phase1', num: 'Phase 1', title: '契约层', meta: 'AgentManifest · ToolCall', src: 'agent-runtime-gateway\\02-阶段教学手册\\第1阶段-契约层教学手册.md', group: 'main' },
  { id: 'phase2', num: 'Phase 2', title: '最小运行时', meta: 'Run/Step · Mock Model', src: 'agent-runtime-gateway\\02-阶段教学手册\\Phase-02-最小运行时教学手册.md', group: 'main' },
  { id: 'phase3', num: 'Phase 3', title: 'Agent 网关与工具治理', meta: 'Gateway · Policy · Audit', src: 'agent-runtime-gateway\\02-阶段教学手册\\Phase-03-Agent网关与工具治理教学手册.md', group: 'main' },
  { id: 'phase4', num: 'Phase 4', title: '长线任务与断点恢复', meta: 'Checkpoint · Resume · HITL', src: 'agent-runtime-gateway\\02-阶段教学手册\\Phase-04-长线任务与断点恢复教学手册.md', group: 'main' },
  { id: 'phase5', num: 'Phase 5', title: 'MCP 与工具生态', meta: 'Adapter · Registry · Credential', src: 'agent-runtime-gateway\\02-阶段教学手册\\Phase-05-MCP与工具生态教学手册.md', group: 'main' },
  { id: 'phase6', num: 'Phase 6', title: '记忆系统', meta: 'Memory Store · Write Gate', src: 'agent-runtime-gateway\\02-阶段教学手册\\Phase-06-记忆系统教学手册.md', group: 'main' },
  { id: 'phase7', num: 'Phase 7', title: '测评审核与红队', meta: 'Golden Set · CI Gate', src: 'agent-runtime-gateway\\02-阶段教学手册\\Phase-07-测评审核与红队教学手册.md', group: 'main' },
  { id: 'phase8', num: 'Phase 8', title: '可观测性与审计', meta: 'Trace · Span · Replay', src: 'agent-runtime-gateway\\02-阶段教学手册\\Phase-08-可观测性与审计教学手册.md', group: 'main' },
  { id: 'phase9', num: 'Phase 9', title: '安全隔离与沙箱', meta: 'Sandbox Profile · Isolation', src: 'agent-runtime-gateway\\02-阶段教学手册\\Phase-09-安全隔离与沙箱教学手册.md', group: 'main' },
  { id: 'phase10', num: 'Phase 10', title: '多智能体协同', meta: 'Handoff · Shared State', src: 'agent-runtime-gateway\\02-阶段教学手册\\Phase-10-多智能体协同教学手册.md', group: 'main' },
  { id: 'phase11', num: 'Phase 11', title: '治理控制台与发布', meta: 'Admin Console · Release Gate', src: 'agent-runtime-gateway\\02-阶段教学手册\\Phase-11-治理控制台与发布教学手册.md', group: 'main' },
  { id: 'rag_route', num: 'RAG专项', title: 'RAG 教学路线总览', meta: 'Chunking · GraphRAG', src: 'agent-runtime-gateway\\07-RAG问题诊断与优化\\RAG教学路线总览.md', group: 'main' },
  { id: 'appendix-c', num: '附录 C', title: '阶段验收清单', meta: '各阶段交付物与验收标准', src: 'agent-runtime-gateway\\02-阶段教学手册\\阶段验收清单.md', group: 'appendix' }
];

let js = `// chapters.js - 自动生成\n// 生成时间: ${new Date().toISOString()}\nconst CHAPTERS = [\n`;

for (const ch of chapters) {
  const fullPath = join(base, ch.src);
  let content = '';
  if (existsSync(fullPath)) {
    content = readFileSync(fullPath, 'utf-8');
    
    // 剔除所有包含代码的内容，仅保留架构思维
    // 匹配 ```(lang) ... ``` 并替换
    content = content.replace(/```[\s\S]*?```/g, '\n> **[工程架构提示]** *此处包含的具体代码段已依最佳实践要求剥离，以突出非代码化架构契约与演练步骤设计。*\n');

    console.log(`OK: ${ch.src} (${content.length} chars)`);
  } else {
    content = `# ${ch.title}\n\n内容文件未找到: ${ch.src}`;
    console.log(`WARN: ${ch.src} not found`);
  }
  
  js += `  { id:${JSON.stringify(ch.id)}, num:${JSON.stringify(ch.num)}, title:${JSON.stringify(ch.title)}, meta:${JSON.stringify(ch.meta)}, source:${JSON.stringify(ch.src.replace(/\\\\/g,'/'))}, group:${JSON.stringify(ch.group)}, content:${JSON.stringify(content)} },\n`;
}

js += `];\n`;

const outPath = join(base, 'data', 'chapters.js');
writeFileSync(outPath, js, 'utf-8');
console.log(`\nDone! ${outPath} (${js.length} bytes, ${chapters.length} chapters)`);
