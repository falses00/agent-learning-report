# Industrial Agent Engineering Course

[![Engineering quality gate](https://github.com/falses00/agent-learning-report/actions/workflows/quality-gate.yml/badge.svg)](https://github.com/falses00/agent-learning-report/actions/workflows/quality-gate.yml)

一套以真实工程交付为主线的 Agent 学习项目。课程围绕同一个 **OpsPilot 企业工单 Agent** 持续演进，覆盖契约、Runtime、Tool/Policy Gateway、RAG、持久化执行、Memory、Eval、Observability、安全、多 Agent 和发布治理。

## 在线学习

[打开 Agent 工程学习控制台](https://falses00.github.io/agent-learning-report/)

在线站点提供：

- 首次学习路径与基础自检。
- F0、S0-S10 学习路线、本地进度，以及 10/12 工程实验覆盖率；当前可运行基线为 F0、S0-S8。
- 每阶段 3 项课前检查、明确标注来源的事故或合成工程故障场景、动手步骤和关键概念速记。
- 每阶段 5 题自测、逐题误区反馈、首轮评分和结构化本地自评门禁。
- S3 RAG 全链路实验室：RAG × Vibe Coding 七阶段主线、10 层证据链、25 条提升路径、14 类故障诊断、10 个固定 commit 源码项目、资料生命周期与可消融架构规划。
- S5 Agent Memory 实验室：21 类方法、六轴分类、8 个固定 commit 源码项目、工作负载选型、写入生命周期决策、SQLite 治理实验与 18 条专项评测。
- S6 Eval 与发布门禁实验室：35 个前序 Agent case、183 条断言、16 个门禁攻击、grader/holdout/critical gate 和证据 hash。
- S7 Observability 与事故响应实验室：信号契约、W3C trace、SLO/burn-rate 分级、8 个事故判定、6 个 Runtime run 与 14 个门禁攻击。
- S8 Security 与 Sandbox 实验室：9 层控制链、4 类安全终态、10 个交互事故、6 个固定 commit 源码项目与 25 个 critical 攻击 case。
- I1 大厂 Agent 面试验收：国内/国际双市场、4 类岗位画像、7 条国内招聘雷达、8 域必记知识、2 道 60 分钟综合系统设计难题、100 分评分尺、5 道自测、6 个 GitHub 上游项目深挖和 A/B/C 来源生命周期。
- 工程化 Vibe Coding 工作方式：探索/交付/高风险受限三种模式，七步闭环、任务契约、8 类反模式、6 条证据主张与 14 个一手来源；明确区分随机实验、观察研究、厂商遥测和课程推论。
- 长教材阅读器：稳定正文宽度、粘性阅读进度、当前位置、桌面章内目录与移动端折叠目录。
- 可运行基线命令、故障演练、课程资料阅读和搜索。
- 本地进度导出与重置，不上传学习数据；导出包明确标记为 `self-reported`，不能替代 CI 或独立工程复验。

## 本地运行

```powershell
node data/build_chapters.mjs
node data/build_baseline_metrics.mjs
python -m http.server 8000
```

打开 `http://localhost:8000/`。

验证内容是否已重新生成：

```powershell
node data/build_chapters.mjs --check
node data/build_baseline_metrics.mjs --check
node data/check_course_gate.mjs
node data/check_learning_content.mjs
node data/check_rag_content.mjs
node data/check_memory_content.mjs
node data/check_eval_content.mjs
node data/check_observability_content.mjs
node data/check_security_content.mjs
node data/check_vibe_coding_content.mjs
node data/check_interview_content.mjs
node data/check_reader_content.mjs
```

运行 Agent 教学基线：

```powershell
cd "agent-runtime-gateway\20-源码"
python -m pip install -e ".[test]"
python -m pytest ..\21-测试 -q
python -m agent_course.cli demo
python -m agent_course.cli eval ..\22-评测集\engineering-baseline.json
python -m agent_course.cli eval ..\22-评测集\s3-rag-baseline.json
python -m agent_course.cli rag-diagnostic-eval ..\22-评测集\rag-diagnostic-baseline.json
python -m agent_course.cli eval ..\22-评测集\s4-durable-baseline.json
python -m agent_course.cli durable-demo --work-dir "$env:TEMP\opspilot-s4" --reset
python -m agent_course.cli memory-eval ..\22-评测集\memory-engineering-baseline.jsonl
python -m agent_course.cli memory-demo --db "$env:TEMP\opspilot-s5-memory.db" --reset
python -m agent_course.cli release-gate ..\22-评测集\s6-release-manifest.json
python -m agent_course.cli release-gate-eval ..\22-评测集\s6-release-gate-adversarial.json
python -m agent_course.cli observability ..\22-评测集\s7-observability-manifest.json
python -m agent_course.cli observability-eval ..\22-评测集\s7-observability-adversarial.json
python -m agent_course.cli security-eval ..\22-评测集\s8-security-adversarial.json
```

## 可复验质量证据

本地与 GitHub Actions 共用同一个质量门禁：

```powershell
python scripts/run_quality_gate.py
```

命令当前执行 23 项检查，生成 `quality-reports/manifest.json`、pytest JUnit、内容检查（含 Vibe Coding、I1 面试验收与长文阅读器）、S3 基础与诊断 eval、S4/S5 eval、S6 release gate、S7 observability，以及 S8 security adversarial JSON。每次向 `main` 推送后，Actions 会保留整包证据，并使用 GitHub Artifact Attestations 为 manifest 生成可验证的构建来源。下载 CI 产物后可核对：

```powershell
gh attestation verify quality-reports/manifest.json --repo falses00/agent-learning-report
```

manifest 中保存各报告的 SHA-256，因此签名来源、提交版本与报告内容可以串联复核。本地运行的 manifest 只用于预检，不带 GitHub 签名，不能冒充 CI 通过。

## 内容入口

- [课程唯一入口](agent-runtime-gateway/00-课程总览/00-唯一学习入口.md)
- [工程实战主线](agent-runtime-gateway/00-课程总览/工程实战主线-v2.md)
- [统一教学提示词 v4](agent-runtime-gateway/00-课程总览/每节课互动模板.md)
- [Vibe Coding 最佳实践](agent-runtime-gateway/00-课程总览/Vibe-Coding最佳实践-2026.md)
- [真实缺口与演进台账](agent-runtime-gateway/00-课程总览/教学平台真实缺口与演进台账-2026-07-13.md)
- [岗位能力与毕业标准](agent-runtime-gateway/00-课程总览/岗位能力与毕业标准.md)
- [大厂 Agent 岗位面试知识地图](agent-runtime-gateway/00-课程总览/大厂Agent岗位面试知识地图-2026.md)
- [Agent Memory 方法谱系与工业选型](agent-runtime-gateway/06-工业级框架蓝图/Agent-Memory方法谱系与工业选型-2026.md)
- [RAG 全链路提升与工业最佳实践](agent-runtime-gateway/07-RAG问题诊断与优化/RAG全链路提升与工业最佳实践-2026.md)
- [RAG × Vibe Coding 工程学习路径](agent-runtime-gateway/07-RAG问题诊断与优化/RAG与Vibe-Coding工程学习路径-2026.md)
- [S3 多租户 RAG 与故障诊断实验](agent-runtime-gateway/labs/S03-rag-citations/README.md)
- [教学平台维护规范](MAINTENANCE.md)
- [S4 崩溃恢复与副作用对账实验](agent-runtime-gateway/labs/S04-durable-execution/README.md)
- [S5 受治理 Agent Memory 实验](agent-runtime-gateway/labs/S05-memory-context/README.md)
- [S6 可阻塞发布的 Eval 与红队门禁实验](agent-runtime-gateway/labs/S06-eval-red-team/README.md)
- [S7 Observability、SLO 与事故回归实验](agent-runtime-gateway/labs/S07-observability-sre/README.md)
- [S8 Agent Security 与 Sandbox 对抗实验](agent-runtime-gateway/labs/S08-security-sandbox/README.md)
- [全链路故障与修复](agent-runtime-gateway/11-工程实战主线/全链路故障与修复手册.md)

当前源码是 F0、S0-S8 教学基线，不是生产系统，不能接入真实资金、客户数据或生产凭据。
