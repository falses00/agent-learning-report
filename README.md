# Industrial Agent Engineering Course

一套以真实工程交付为主线的 Agent 学习项目。课程围绕同一个 **OpsPilot 企业工单 Agent** 持续演进，覆盖契约、Runtime、Tool/Policy Gateway、RAG、持久化执行、Memory、Eval、Observability、安全、多 Agent 和发布治理。

## 在线学习

[打开 Agent 工程学习控制台](https://falses00.github.io/agent-learning-report/)

在线站点提供：

- 首次学习路径与基础自检。
- F0、S0-S10 工程路线和本地进度。
- 每阶段 3 项课前检查、真实事故案例、3 步动手实验和关键概念速记。
- 每阶段 5 题自测、逐题误区反馈、首轮评分和工程证据门禁。
- S5 Agent Memory 实验室：14 类方法对比、工作负载选型、写入生命周期决策与专项门禁。
- 可运行基线命令、故障演练、课程资料阅读和搜索。
- 本地进度导出与重置，不上传学习数据。

## 本地运行

```powershell
node data/build_chapters.mjs
python -m http.server 8000
```

打开 `http://localhost:8000/`。

验证内容是否已重新生成：

```powershell
node data/build_chapters.mjs --check
node data/check_learning_content.mjs
node data/check_memory_content.mjs
```

运行 Agent 教学基线：

```powershell
cd "agent-runtime-gateway\20-源码"
python -m pytest ..\21-测试 -q
python -m agent_course.cli demo
python -m agent_course.cli eval ..\22-评测集\engineering-baseline.json
```

## 内容入口

- [课程唯一入口](agent-runtime-gateway/00-课程总览/00-唯一学习入口.md)
- [工程实战主线](agent-runtime-gateway/00-课程总览/工程实战主线-v2.md)
- [岗位能力与毕业标准](agent-runtime-gateway/00-课程总览/岗位能力与毕业标准.md)
- [Agent Memory 方法谱系与工业选型](agent-runtime-gateway/06-工业级框架蓝图/Agent-Memory方法谱系与工业选型-2026.md)
- [全链路故障与修复](agent-runtime-gateway/11-工程实战主线/全链路故障与修复手册.md)

当前源码是 S0-S2 教学基线，不是生产系统，不能接入真实资金、客户数据或生产凭据。
