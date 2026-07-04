# GitHub 项目调研：Agent Runtime Gateway

调研日期：2026-06-28  
最近刷新：2026-06-29  
调研方式：`researcher` subagent + GitHub CLI authenticated REST/API + GitHub 页面抽样核验  
历史数据快照：`H:\Creat A Agent\agent-runtime-gateway\10-GitHub项目调研\GitHub仓库快照-2026-06-28.json`  
最新核心快照：`H:\Creat A Agent\agent-runtime-gateway\10-GitHub项目调研\GitHub核心项目快照-2026-06-29.json`  
最新核心摘要：`H:\Creat A Agent\agent-runtime-gateway\10-GitHub项目调研\GitHub核心项目刷新摘要-2026-06-29.md`  
补充调研：`H:\Creat A Agent\agent-runtime-gateway\10-GitHub项目调研\GitHub补充项目调研-2026-06-29.md`  
补充快照：`H:\Creat A Agent\agent-runtime-gateway\10-GitHub项目调研\GitHub补充项目快照-2026-06-29.json`  
采用准则：`H:\Creat A Agent\agent-runtime-gateway\10-GitHub项目调研\参考项目采用准则.md`  
最新资料证据表：`H:\Creat A Agent\agent-runtime-gateway\10-GitHub项目调研\最新资料证据表-2026-06-29.md`

说明：正文表格保留 2026-06-28 调研记录，最新 GitHub 元数据以 2026-06-29 JSON 快照和刷新摘要为准。

## 1. 研究结论

Agent Runtime Gateway 不应照搬某个单一 Agent framework。靠谱路线是组合这些成熟方向：

- **LangGraph 式可恢复状态机**：用于长线任务、checkpoint、human-in-the-loop。
- **MCP 官方协议与 SDK**：用于工具接入和工具生态兼容。
- **LiteLLM/Portkey 式模型网关**：用于多模型路由、fallback、成本、guardrails。
- **OpenTelemetry + Langfuse/Phoenix**：用于统一 trace、metrics、eval、prompt/dataset 管理。
- **Promptfoo/Ragas**：用于 prompt、RAG、Agent 和安全回归评估。
- **OpenHands/Codex/Cline**：用于学习本地 Agent 权限、workspace、diff、审批、MCP、终端和文件系统组合模型。
- **gVisor/Firecracker/E2B/Wasmtime**：用于分级沙箱，而不是把普通 Docker 当成完整安全边界。
- **OPA/Kong/Envoy/Casdoor**：用于企业策略、网关、IAM、租户隔离和审计。

2026-06-29 补充结论：

- **Mem0/Zep/Graphiti/Letta/TencentDB-Agent-Memory**：用于补强记忆写入、召回、遗忘、评测和知识图谱思路。
- **CAMEL/AG2/Langroid/MindSearch/AgentScope**：用于补强 handoff、共享状态、多 Agent 任务分工和协同评测。
- **AgentOps/Opik/Giskard/DeepEval/LangWatch/Helicone**：用于补强 agent trace、session replay、成本追踪、红队和评测审核体系。
- **mcp-agent/mcp-use/Plano/HumanLayer/Invariant/Garak**：用于补强 MCP lifecycle、agentic gateway、安全 guardrail、human-in-the-loop 和漏洞扫描。

## 2. 可靠性判断方法

本次不按 star 单一排序，而按以下维度判断：

| 维度 | 判断方式 |
|---|---|
| 活跃度 | recent push、latest release、open issues |
| 协议地位 | 是否为官方 SDK/spec/server |
| 架构适配度 | 是否映射到 Runtime/Gateway/Memory/Eval/Sandbox |
| 企业适配 | 是否支持 self-host、policy、auth、observability |
| 风险 | license、维护状态、生态迁移、API churn、安全边界 |
| 可迁移性 | 是抽象模式可借鉴，还是只能作为具体产品形态参考 |

## 3. 必须作为 PRD 设计基准

| 项目 | 快照证据 | 定位 | PRD 采用方式 | 风险 |
|---|---:|---|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | 35,924 stars / 6,013 forks / 584 issues / release `1.2.6` / pushed 2026-06-28 / MIT | 可恢复 Agent 状态机 | 采用 graph state、checkpoint、resume、interrupt 思想 | 不锁死 LangChain 生态 |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | 23,470 stars / release `v1.28.1` / pushed 2026-06-27 / MIT | MCP 官方 Python SDK | Tool Gateway 的协议兼容层 | MCP 不提供完整企业治理 |
| [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) | 12,741 stars / release `v1.29.0` / pushed 2026-06-28 | MCP 官方 TS SDK | 前端/Node 工具生态参考 | license 元数据 `NOASSERTION`，需二次核验 |
| [GitHub MCP Server](https://github.com/github/github-mcp-server) | 31,018 stars / release `v1.5.0` / pushed 2026-06-27 / MIT | 官方 GitHub MCP Server | 参考工具粒度、auth、server 能力 | 不能直接推广到所有企业工具 |
| [gVisor](https://github.com/google/gvisor) | 18,626 stars / Apache-2.0 / pushed 2026-06-27 | 容器增强隔离 | 中高风险工具执行沙箱 | syscall 兼容性和性能权衡 |
| [Firecracker](https://github.com/firecracker-microvm/firecracker) | 35,179 stars / release `v1.16.0` / Apache-2.0 | microVM 隔离 | 高风险租户/代码执行隔离 | KVM/Linux 运维复杂 |
| [E2B](https://github.com/e2b-dev/E2B) | 12,759 stars / release `e2b@2.31.0` / Apache-2.0 | Agent sandbox 平台 | sandbox provider API 参考 | 云/自托管成本与数据驻留 |
| [OpenTelemetry Specification](https://github.com/open-telemetry/opentelemetry-specification) | 4,268 stars / release `v1.58.0` / Apache-2.0 | trace/metric/log 规范 | 观测事件模型底座 | LLM 语义需扩展 |
| [OpenTelemetry Collector](https://github.com/open-telemetry/opentelemetry-collector) | 7,180 stars / release `v0.155.0` / Apache-2.0 | 遥测采集与转发 | collector/exporter/processor 模式 | 部署复杂度 |
| [AWS AgentCore Samples](https://github.com/awslabs/agentcore-samples) | 3,133 stars / Apache-2.0 / pushed 2026-06-26 | Bedrock AgentCore 样例 | runtime/gateway/memory/identity/evaluation 模块边界参考 | AWS 生态绑定，需抽象化 |

## 3.1 参考模式与许可证风险

| 参考模式 | 含义 | 适用情况 |
|---|---|---|
| `dependency allowed` | 可作为候选依赖继续评估 | license 明确、API 稳定、部署边界清晰 |
| `adapter candidate after license review` | 可以做 adapter 候选，但必须先做许可证/商业条款审查 | license 为 `NOASSERTION`、ELv2、商业条款不清或部署模式复杂 |
| `pattern only` | 只借鉴设计模式，不引入依赖 | 产品形态有启发但不适合企业 runtime 或 license/维护状态不明 |

当前需要特别标注为 `adapter candidate after license review` 或 `pattern only` 的项目：

- LiteLLM：license 元数据为 `NOASSERTION`，PRD 只先借鉴 AI Gateway 模式。
- MCP TypeScript SDK：license 元数据为 `NOASSERTION`，使用前需要核验 package license。
- MCP Registry：license 元数据为 `NOASSERTION`，只参考 registry schema/server discovery，不直接作为依赖。
- Langfuse：license 元数据为 `NOASSERTION`，先作为观测/eval 产品模式参考。
- Phoenix：license 元数据为 `NOASSERTION`，企业嵌入前需审查许可证和部署条款。
- OpenHands：license 元数据为 `NOASSERTION`，只作为 workspace/sandbox/human approval 模式参考。

## 4. 建议重点参考

| 项目 | 快照证据 | 定位 | 可借鉴能力 | 不照搬原因 |
|---|---:|---|---|---|
| [LiteLLM](https://github.com/BerriAI/litellm) | 51,805 stars / release `v1.90.0` / pushed 2026-06-28 | OpenAI-compatible AI Gateway | 多模型路由、fallback、成本、proxy | 不让模型网关取代 Agent runtime |
| [Portkey Gateway](https://github.com/Portkey-AI/gateway) | 12,226 stars / release `v1.15.2` / MIT | AI Gateway | routing、guardrails、load balancing、MCP gateway 思路 | 不锁死外部 SaaS 控制面 |
| [CrewAI](https://github.com/crewAIInc/crewAI) | 54,481 stars / release `1.15.1` / MIT | 多角色 Agent 协作 | crew/role/task/process UX | role-playing 不适合作唯一控制流 |
| [AutoGen](https://github.com/microsoft/autogen) | 59,303 stars / release `python-v0.7.5` / CC-BY-4.0 | 多 Agent 编程框架 | message/team/tool patterns | 当前版本线和迁移方向需核验 |
| [Pydantic AI](https://github.com/pydantic/pydantic-ai) | 18,040 stars / release `v2.0.0` / MIT | 类型安全 Agent framework | schema-first tool/result validation | API churn，不能锁死 |
| [smolagents](https://github.com/huggingface/smolagents) | 28,057 stars / release `v1.26.0` / Apache-2.0 | code-agent 轻量框架 | 简洁 agent loop、code execution 风险 | 不适合完整企业 runtime |
| [OpenHands](https://github.com/OpenHands/OpenHands) | 78,533 stars / release `cloud-1.40.0` | 软件工程 Agent | workspace、sandbox、session、approval | 编码 Agent 不等于通用 Runtime Gateway |
| [OpenAI Codex](https://github.com/openai/codex) | 94,123 stars / release `rust-v0.142.3` / Apache-2.0 | 终端 coding agent | 本地权限、patch、worktree、工具审批 | 企业能力需参考官方 OpenAI 文档再定 |
| [Cline](https://github.com/cline/cline) | 63,968 stars / release `v4.0.1` / Apache-2.0 | IDE/CLI coding agent | human-in-loop、MCP、工具确认 | IDE 产品形态不等于平台底座 |
| [Composio](https://github.com/ComposioHQ/composio) | 28,995 stars / release `@composio/slim@0.13.1` / MIT | toolkits/auth/connectors | connector registry、auth broker | 核心凭据控制不能外包 |
| [FastMCP](https://github.com/PrefectHQ/fastmcp) | 25,827 stars / release `v3.4.2` / Apache-2.0 | MCP server/client DX | Pythonic MCP 开发体验 | 不是企业治理层 |
| [Langfuse](https://github.com/langfuse/langfuse) | 29,909 stars / release `v3.201.1` | LLM observability/evals | trace、prompt、dataset、eval | 后端可插拔，底层用 OTel |
| [Phoenix](https://github.com/Arize-ai/phoenix) | 10,301 stars / release `arize-phoenix-client-v2.10.0` | AI observability/eval | OpenInference、tracing、dataset、experiments | license 元数据需企业审查 |
| [Promptfoo](https://github.com/promptfoo/promptfoo) | 22,665 stars / release `code-scan-action-0.1.8` / MIT | eval/red team/CI | prompt/RAG/agent 测试与红队 | 不是线上 runtime |
| [Ragas](https://github.com/vibrantlabsai/ragas) | 14,553 stars / release `v0.4.3` / Apache-2.0 | LLM/RAG eval | faithfulness、context precision/recall | LLM-as-judge 不能单独裁决 |

## 5. 可选参考

| 项目 | 快照证据 | 可选价值 | 风险 |
|---|---:|---|---|
| [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) | 约 185k stars，平台 beta 活跃 | Agent protocol、benchmark、低代码平台化 | 早期自主循环不适合高风险生产 |
| [LlamaIndex](https://github.com/run-llama/llama_index) | 50,457 stars / release `v0.14.23` / MIT | ingestion、index、retriever、agent workflow | 记忆层不要锁死单一 RAG 框架 |
| [Microsoft GraphRAG](https://github.com/microsoft/graphrag) | 34,035 stars / release `v3.1.0` / MIT | graph-based RAG | 成本和复杂度高，不默认启用 |
| [RedisVL](https://github.com/redis/redis-vl-python) | 411 stars / release `v0.22.0` / MIT | Redis vector/search client | 项目小，适合作 adapter |
| [Playwright MCP](https://github.com/microsoft/playwright-mcp) | 约 34k stars | 浏览器工具权限与会话边界 | 浏览器自动化风险高 |
| [Casdoor](https://github.com/casdoor/casdoor) | 13,842 stars / release `v3.100.0` / Apache-2.0 | IAM/OIDC/SAML/SCIM | MCP gateway 成熟度需核验 |
| [OPA](https://github.com/open-policy-agent/opa) | 11,907 stars / release `v1.18.0` / Apache-2.0 | policy as code | 策略学习成本 |
| [Kong](https://github.com/Kong/kong) | 43,687 stars / release `3.9.3` / Apache-2.0 | API gateway plugins | 不等同 Agent Gateway |
| [Envoy](https://github.com/envoyproxy/envoy) | 28,474 stars / release `v1.38.3` / Apache-2.0 | L7 proxy/sidecar | 需要平台工程能力 |
| [Temporal](https://github.com/temporalio/temporal) | 21,283 stars / release `v1.31.1` / MIT | durable workflow | 与 Agent state graph 边界需设计 |
| [Wasmtime](https://github.com/bytecodealliance/wasmtime) | 18,263 stars / release `v46.0.1` / Apache-2.0 | WASM plugin sandbox | 不适合完整 Linux coding workspace |

## 6. 协议与生态补充

| 来源 | 链接 | 影响 |
|---|---|---|
| MCP Specification | https://modelcontextprotocol.io/specification/2025-11-25 | PRD 必须兼容 latest stable MCP tool/resource/prompt 语义 |
| MCP Releases | https://github.com/modelcontextprotocol/modelcontextprotocol/releases | 需处理 spec stable/RC 并存与版本协商 |
| MCP Registry About | https://modelcontextprotocol.io/registry/about | 公共 registry 可参考，但企业应建设 private/curated registry |
| MCP Registry repo | https://github.com/modelcontextprotocol/registry | server discovery 和 metadata schema 参考；快照为 6,966 stars / release `v1.7.9`；license 元数据 `NOASSERTION`，采用模式为 `pattern only` |
| AWS Bedrock AgentCore samples | https://github.com/awslabs/agentcore-samples | runtime/gateway/memory/identity/evaluation 的企业模块边界参考；快照为 3,133 stars |
| AgentCore TypeScript samples | https://github.com/awslabs/bedrock-agentcore-samples-typescript | AgentCore 多语言样例参考 |
| AgentCore multi-tenant sample | https://github.com/aws-samples/sample-agentcore-multi-tenant | 多租户模式参考，项目较小需谨慎 |

## 7. PRD 映射

| PRD 模块 | 核心参考 | 采用判断 |
|---|---|---|
| Agent Gateway | LiteLLM、Portkey、Kong、Envoy | 参考入口、路由、限流、fallback，不替代 Runtime |
| Agent Runtime | LangGraph、Temporal、AgentCore | 显式状态机 + durable workflow 思想 |
| Tool Gateway | MCP SDK、GitHub MCP、FastMCP、Composio | MCP 兼容 + 企业权限/审计补齐 |
| Memory | LlamaIndex、RedisVL、GraphRAG | 分层 memory，GraphRAG 可选 |
| Evaluation | Promptfoo、Ragas、Langfuse、Phoenix | CI gate + offline/online eval |
| Observability | OpenTelemetry、Langfuse、Phoenix | OTel 底座，LLM 事件扩展 |
| Sandbox | gVisor、Firecracker、E2B、Wasmtime | 风险分级沙箱 |
| Security/Governance | OPA、Casdoor、Kong、Envoy | policy、IAM、gateway、audit |
| Coding Agent Lessons | OpenHands、Codex、Cline | workspace、diff、approval、MCP、人机协作 |

## 8. 需要二次核验

- AutoGen 当前版本线和 Microsoft Agent Framework 迁移方向。
- MCP Registry 是否仍处于 preview，以及 registry schema 最新状态。
- Casdoor 的 MCP/Agent Gateway 能力成熟度。
- Phoenix/Langfuse 企业部署、telemetry 和许可证细节。
- OpenAI Codex 企业集成能力应以官方 OpenAI/Codex 文档为准。
- AWS Bedrock AgentCore 是否适合作为竞品/设计参照，需结合 AWS 官方文档继续核验。
