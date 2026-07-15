# Industrial Agent Engineering Course

[![Engineering quality gate](https://github.com/falses00/agent-learning-report/actions/workflows/quality-gate.yml/badge.svg)](https://github.com/falses00/agent-learning-report/actions/workflows/quality-gate.yml)

一套以真实工程交付为主线的 Agent 学习项目。课程围绕同一个 **OpsPilot 企业工单 Agent** 持续演进，覆盖契约、Runtime、Tool/Policy Gateway、RAG、持久化执行、Memory、Eval、Observability、安全、多 Agent 和发布治理。

## 在线学习

[打开 Agent 工程学习控制台](https://falses00.github.io/agent-learning-report/)

在线站点提供：

- 首次学习路径与基础自检。
- F0、S0-S10 学习路线、本地进度，以及 5/12 工程实验覆盖率；当前可运行基线为 F0、S0-S3。
- 每阶段 3 项课前检查、明确标注来源的事故或合成工程故障场景、动手步骤和关键概念速记。
- 每阶段 5 题自测、逐题误区反馈、首轮评分和结构化本地自评门禁。
- S5 Agent Memory 实验室：14 类方法对比、工作负载选型、写入生命周期决策与专项门禁。
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
node data/check_memory_content.mjs
```

运行 Agent 教学基线：

```powershell
cd "agent-runtime-gateway\20-源码"
python -m pip install -e ".[test]"
python -m pytest ..\21-测试 -q
python -m agent_course.cli demo
python -m agent_course.cli eval ..\22-评测集\engineering-baseline.json
python -m agent_course.cli eval ..\22-评测集\s3-rag-baseline.json
```

## 可复验质量证据

本地与 GitHub Actions 共用同一个质量门禁：

```powershell
python scripts/run_quality_gate.py
```

命令会生成 `quality-reports/manifest.json`、pytest JUnit 报告、课程检查日志和两套 eval JSON。每次向 `main` 推送后，Actions 会保留整包证据，并使用 GitHub Artifact Attestations 为 manifest 生成可验证的构建来源。下载 CI 产物后可核对：

```powershell
gh attestation verify quality-reports/manifest.json --repo falses00/agent-learning-report
```

manifest 中保存各报告的 SHA-256，因此签名来源、提交版本与报告内容可以串联复核。本地运行的 manifest 只用于预检，不带 GitHub 签名，不能冒充 CI 通过。

## 内容入口

- [课程唯一入口](agent-runtime-gateway/00-课程总览/00-唯一学习入口.md)
- [工程实战主线](agent-runtime-gateway/00-课程总览/工程实战主线-v2.md)
- [统一教学提示词 v2](agent-runtime-gateway/00-课程总览/每节课互动模板.md)
- [真实缺口与演进台账](agent-runtime-gateway/00-课程总览/教学平台真实缺口与演进台账-2026-07-13.md)
- [岗位能力与毕业标准](agent-runtime-gateway/00-课程总览/岗位能力与毕业标准.md)
- [Agent Memory 方法谱系与工业选型](agent-runtime-gateway/06-工业级框架蓝图/Agent-Memory方法谱系与工业选型-2026.md)
- [全链路故障与修复](agent-runtime-gateway/11-工程实战主线/全链路故障与修复手册.md)

当前源码是 F0、S0-S3 教学基线，不是生产系统，不能接入真实资金、客户数据或生产凭据。
