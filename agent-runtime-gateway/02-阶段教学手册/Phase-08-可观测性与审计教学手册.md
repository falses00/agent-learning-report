# Phase 08：Observability 与 SRE 教学手册

更新日期：2026-08-08
学习模式：Implementation + Evidence

## 一句话定义

Agent Observability 是把一次运行的路径、趋势、责任事实和版本谱系连接起来，使团队能定位用户影响、自动止损，并把事故变成可重复的回归防线。

## 1. 关键概念

| 概念 | 白话解释 | 为什么存在 | 缺少时的事故 | 验收证据 |
|---|---|---|---|---|
| Trace Context | 跨组件传递同一次请求的身份 | 串联网关、Agent、检索与工具 | 日志很多，却找不到同一次运行 | 合法 `traceparent`，全链路同一 trace-id |
| Span | 一次操作的边界、父子关系和结果 | 定位哪一层慢、错或未执行 | 只能看到总耗时，无法归因 | `invoke_agent/retrieval/guardrail/execute_tool` |
| Metric / SLI | 对大量运行做低基数聚合 | 判断整体趋势而不是单次故事 | 平均值正常，尾延迟和错误正在恶化 | success、P95、cost、coverage、burn rate |
| SLO | 用户可接受的 SLI 目标 | 定义什么算可靠和可运营 | 仪表盘很多，却不知道何时止损 | 目标、窗口、数据源、owner、动作 |
| Error Budget | SLO 允许的非关键失败额度 | 连接可靠性和发布速度 | 预算耗尽仍继续发布高风险变更 | burn rate、freeze policy、例外条件 |
| Audit Event | 证明谁对什么资源做了什么决定 | 支持责任追踪与合规复盘 | 高风险动作完成，却无法证明授权 | actor/resource hash、action、outcome、reason |
| Replay Packet | 重建失败所需的最小版本和证据包 | 防止“现在复现不了” | Prompt、模型或策略变化后无法解释差异 | request hash、trace、终态、版本、audit head |
| Incident Regression | 从事故提炼出的永久测试 | 防止同类问题再次静默发生 | 复盘写完后同一故障复发 | case ID、owner、修复前失败、修复后通过 |

## 2. 信号分工

```text
Trace  : 这一次请求怎样经过各层？
Metric : 整体是否正在退化？
Log    : 某个组件在某一时刻发生了什么？
Audit  : 谁基于什么权限做了什么决定？
Replay : 能否用同一版本重建失败？
```

Trace 和 audit 不能混成一张表。Trace 面向诊断，可以采样；audit 面向责任事实，字段稳定、访问受控，并需要独立完整性和保留策略。两者都不能记录 secret 明文。

## 3. 本阶段工程边界

本阶段真实实现：

- 执行现有 `AgentRuntime`，读取真实 run 与 audit event。
- 将运行证据适配为 W3C trace context 和固定版本的 GenAI span contract。
- 默认 `metadata_only`，对 actor、resource 和 request 做 SHA-256 引用。
- 生成可验证的 audit hash chain、replay packet 与 evidence hash。
- 从 6 个教学运行聚合 success、P95、token、cost、trace/audit coverage 和 burn rate。
- 对 SLO、零预算事件、采样策略和版本谱系做 fail-closed 判定。
- 自动生成 alert、incident 和 regression owner；快速 burn 分页，慢速 burn 建立有 owner 的工单。
- 用 14 类 mutation 反向攻击观测门禁。

本阶段仍未实现：

- 真实 OpenTelemetry SDK、Collector、Tempo/Jaeger/Prometheus 或商业后端。
- 真实模型 token、成本和生产延迟。课程中的这三类值是确定性夹具。
- append-only/WORM 审计存储、KMS 签名、细粒度访问控制和法务保留。
- 真实 page/ticket 通知、值班系统和生产流量多窗口查询。

因此，本阶段证明的是观测合同、失败判定和事故闭环可运行，不证明生产 SLO 已达到。

## 4. 为什么固定上游语义版本

OpenTelemetry GenAI agent spans 当前标注为 `Development`，字段仍可能改变。课程将上游提交固定为：

```text
open-telemetry/semantic-conventions-genai
f77b9235f2ad49fe95b61e9809ca82bb08ef9d47
```

内部合同使用 `opspilot.observability.v1`。将来升级上游时，先迁移内部 schema 并运行回归，不让课程或生产证据直接依赖 `main` 分支。

## 5. 可运行实验

### 5.1 安装与运行

```powershell
cd "agent-runtime-gateway\20-源码"
python -m pip install -e ".[test]"
python -m pytest ..\21-测试\test_observability.py -q
python -m agent_course.cli observability ..\22-评测集\s7-observability-manifest.json
python -m agent_course.cli observability-eval ..\22-评测集\s7-observability-adversarial.json
```

### 5.2 预期结果

| 证据 | 预期 |
|---|---:|
| Runtime cases | 6 / 6 |
| Assertions | 36 / 36 |
| Trace coverage | 100% |
| Audit coverage | 100% |
| Replay coverage | 100% |
| Sensitive exposure | 0 |
| P95 教学夹具 | 640 ms |
| Cost / success 教学夹具 | 0.00333333 USD |
| Gate attacks | 14 / 14 |
| Gate assertions | 46 / 46 |

### 5.3 证据链

```text
RunRequest
-> AgentRuntime / SQLite audit
-> sanitized audit export
-> W3C trace + GenAI operation spans
-> audit hash chain
-> replay packet + version lineage
-> SLI/SLO/error budget
-> alert + incident + regression owner
-> evidence SHA-256 + decision SHA-256
```

## 6. 必做失败实验

| 注入 | 正确阻断 | 为什么 |
|---|---|---|
| 删除一个 child span | `TRACE_COVERAGE_GAP` | 关键路径出现不可见区 |
| 损坏 trace-id | `TRACE_CONTEXT_INVALID` | 无法跨组件关联 |
| 删除审批 audit | `AUDIT_COVERAGE_GAP` | 高风险动作缺责任证据 |
| 修改 hash chain 内事件 | `AUDIT_CHAIN_INVALID` | 导出证据被篡改 |
| 把 secret canary 写入 span | `SENSITIVE_TELEMETRY_DETECTED` | 观测系统成为泄漏面 |
| P95 提高到 5000ms | `P95_LATENCY_SLO_BREACH` | 端到端体验不可接受 |
| cost/success 超预算 | `COST_PER_SUCCESS_BUDGET_EXCEEDED` | 候选不可运营 |
| 一个关键运行失败 | `ERROR_BUDGET_FAST_BURN` | 99% SLO 的小预算被快速消耗 |
| 删除 replay 版本 | `REPLAY_PACKET_INCOMPLETE` | 无法复现同一候选 |
| 信任外部 sampled flag | `EXTERNAL_SAMPLING_OVERRIDE_TRUSTED` | 可被滥用放大存储和账单 |
| 使用 semconv `main` | `SEMCONV_VERSION_UNPINNED` | 证据 schema 不可重复 |
| 未设置 regression owner | `INCIDENT_REGRESSION_OWNER_MISSING` | 事故没有永久防线负责人 |
| 未知 mutation | `OBSERVABILITY_EVAL_FAILED_CLOSED` | 门禁不认识输入时不能放行 |

## 7. SLO 与告警原理

### 7.1 从用户影响定义 SLI

不要从“现有监控能提供什么”倒推 SLO。先定义用户任务成功，再选择：

- 端到端任务成功率，不只看模型 API 200。
- P95/P99 端到端延迟，不用平均值掩盖尾延迟。
- cost per successful task，不把失败调用成本分母忽略。
- critical safety block rate、trace coverage、audit coverage。
- 需要时按 model route、tool、tenant class、release version 分层，但避免高基数泄漏。

### 7.2 错误预算不是安全事故额度

预算永远为 0：

- secret 或 PII 泄漏。
- 跨租户、越权写入、重复副作用。
- 关键 audit 缺失或完整性失效。
- 关键 trace 无法关联，导致事故不可定位。

可以使用预算：

- 可恢复 provider timeout。
- 非关键回答质量退化。
- fallback 触发。
- 非关键 debug 事件缺失。

### 7.3 为什么使用 burn rate

单次错误不等于立即分页。Google SRE 建议用多窗口 burn rate 区分快速事故和慢性退化：

- 快速燃烧：长短窗口同时超过 page 阈值，立即止损。
- 慢速燃烧：创建 ticket，绑定 owner 和期限。
- 单次可恢复故障：保留 exemplar，观察聚合 SLI。

课程计算的是单个确定性快照，用来验证门禁公式；生产实现必须接入真实长短窗口查询。

### 7.4 采样也是需要运营的系统

OpenTelemetry 将头采样与尾采样分开：

- Head sampling 决策早、开销低，但无法根据完整轨迹的错误或延迟决定保留。
- Tail sampling 可保留错误、高延迟、高风险或新版本轨迹，但需要等待 span 完成，是有状态、有容量上限的组件。
- 采样器本身要有队列、丢弃率、决策延迟和降级监控，否则“为了省观测成本”可能让关键失败不可见。
- 入口不信任外部 `sampled=1`；最终保留策略由内部风险、数据分类和成本预算决定。

## 8. 真实案例与常见误区

### 案例：所有子 Span 成功，用户仍等待 30 秒

模型和工具 span 都成功，但队列等待没有 span。局部状态正常不能证明端到端健康。修复顺序：

1. 从用户入口记录端到端 duration。
2. 比较 root duration 与可见 child duration。
3. 给 queue、retry、approval wait 增加边界。
4. 按 release version 和 route 查看 P95/P99。
5. 将不可见等待加入 regression 和 coverage gate。

### 常见误区

| 误区 | 问题 | 修复 |
|---|---|---|
| 日志越多越好 | 高基数、泄漏和噪声同时增加 | 先写问题，再选择最小信号 |
| 记录完整 prompt 才能调试 | 把用户内容复制到更多系统 | 默认 metadata-only，受控 opt-in |
| 所有 error span 都分页 | 产生告警疲劳 | 用用户影响和 burn rate 分级 |
| Trace 等于 audit | 调试采样会破坏责任证据 | 分开 schema、存储、访问和保留 |
| 平均延迟正常就健康 | 尾部用户仍可能非常慢 | 使用 P95/P99 和端到端边界 |
| 只记录 token 不记录任务结果 | 无法计算 cost/success | token、cost 与 terminal outcome 关联 |
| OTel 字段永远稳定 | GenAI 约定仍在演进 | 固定 commit，内部 schema 版本化 |
| Tail sampling 只是免费的降成本开关 | 它需要缓存完整 trace，会过载也会错过证据 | 为 sampler 设容量、丢弃率和降级 SLO |
| 复盘完成等于事故关闭 | 没有永久回归防线 | 事故必须产生 regression/policy/alert/runbook |

## 9. 五道自测题

1. Trace、metric、log、audit 和 replay 各回答什么问题？
2. 为什么外部 `sampled=1` 不能无条件覆盖内部采样策略？
3. 一次 provider timeout 在什么条件下应该 page，什么条件下只保留 trace？
4. 为什么 secret leakage 和 audit gap 的错误预算必须为 0？
5. 一个可复现的 replay packet 至少要包含哪些版本和证据引用？

答案核对：

1. 单次路径、整体趋势、局部事件、责任事实、版本化重建。
2. 它是外部不可信输入，可能放大性能、存储和费用风险。
3. 用户影响和长短窗口 burn rate 越过 page 阈值时 page；fallback 成功且窗口健康时观察。
4. 它们分别破坏数据边界和责任证据，不能用普通质量平均值抵消。
5. request hash、run/trace、预期终态、audit chain head，以及 agent/prompt/model/tool/policy/knowledge/eval/schema 版本。

答错时不要只背答案。回到对应 mutation，先让门禁错误放行，再补规则并重跑专项测试。

## 10. 一页速记清单

- [ ] 每次运行有合法 W3C trace context。
- [ ] root span 覆盖端到端时间，关键层有 child span。
- [ ] prompt/output 默认不采集，actor/resource/request 使用最小引用。
- [ ] Trace、metric、log、audit、replay 的责任边界清楚。
- [ ] P95、cost/success、success、coverage 与 burn rate 从同一候选聚合。
- [ ] secret、越权、重复副作用、关键 audit gap 的预算为 0。
- [ ] 告警按用户影响和 multi-window burn rate 分级。
- [ ] Head/tail sampling 的保留规则、容量上限和丢弃告警已定义。
- [ ] audit export 可验证完整性，但不冒充 WORM 存储。
- [ ] replay packet 锁定全部行为版本。
- [ ] 每个事故有 regression case、owner 和截止条件。
- [ ] 上游 GenAI semconv 固定 commit，并有内部 schema version。
- [ ] 教学性能夹具与生产 telemetry 明确分开。

## 11. 预习核对清单

进入 S8 Security 与 Sandbox 前：

- [ ] 能解释为什么观测后端也是敏感数据资产。
- [ ] 能从 trace 识别不可信内容进入工具参数的路径。
- [ ] 能列出 secret、network egress、filesystem 与 process 的信任边界。
- [ ] 能说明 audit 为什么不能替代 sandbox。
- [ ] 已完成 4 个运营实验室判定，并保存正常、失败和对抗证据。

## 12. 大厂岗位映射

| 面试要求 | 本阶段证据 |
|---|---|
| 分布式追踪 | W3C trace context、父子 span、schema pin |
| SRE | SLI/SLO、P95、error budget、burn-rate alert |
| Agent 工程 | tool/guardrail/retrieval/terminal trajectory |
| 安全与合规 | metadata-only、secret canary、audit integrity |
| 事故处理 | alert、incident、replay、regression owner |
| 工程表达 | 能说明教学适配器与生产 Collector/WORM 的边界 |

## 13. 当前资料与未来方向

已有一手证据支持：

- [OpenTelemetry GenAI agent spans](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md)：`invoke_agent`、`execute_tool` 等语义，当前为 Development。
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)：跨系统 trace context、采样和隐私边界。
- [Google SRE SLO](https://sre.google/sre-book/service-level-objectives/)：SLI、SLO、分位数和错误预算。
- [Google SRE Alerting](https://sre.google/workbook/alerting-on-slos/)：多窗口、多 burn rate 告警。
- [OpenAI Observability](https://developers.openai.com/api/docs/guides/agents/integrations-observability)：模型、工具、handoff、guardrail 和 custom spans。
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)：敏感字段、访问和保留治理。
- [NIST SP 800-92](https://csrc.nist.gov/pubs/sp/800/92/final)：企业日志管理生命周期。
- [OpenTelemetry Sampling](https://opentelemetry.io/docs/concepts/sampling/)：head/tail sampling 的能力、运营代价与遗漏风险。
- [OpenInference Semantic Conventions](https://arize-ai.github.io/openinference/spec/semantic_conventions.html)：`AGENT`、`TOOL`、`RETRIEVER`、`GUARDRAIL` 和 `EVALUATOR` 跨工具语义对照。
- [NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)：上线后持续监测、事故响应、恢复、停用与变更管理。
- [OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)：工具、记忆、策略或 provider 变更后的对抗回归与 CI gate。
- [OWASP Agent Observability Standard](https://owasp.org/www-project-agent-observability-standard-2/)：演进中的可插桩、可追踪、可检查方向，不应当作已稳定规范。

工程推断，仍需真实生产验证：

- 树状 trace 会扩展为多 Agent、异步工具与 artifact 的因果图。
- Tail sampling 会进一步同时考虑错误、风险、稀有轨迹、成本和数据分类；这是基于现有采样能力的工程推断。
- Prompt、tool registry、memory、eval、trace 与 deployment decision 会进入统一 lineage。
- 跨 Agent 观测可能同时承担运行时控制面，但 AOS 仍在演进，需要先用内部合同和迁移测试隔离变动。

## 14. 通过条件

- 14 个专项 pytest 全部通过。
- 6/6 Runtime case、36/36 观测断言通过。
- 14/14 gate attack、46/46 门禁断言通过。
- trace、audit、replay coverage 均为 100%，secret exposure 为 0。
- 正确完成前端至少 4 个事故响应场景。
- 提交正常、失败、对抗证据，并能口头解释三个生产缺口。

满足这些条件，只代表 S7 教学工程门禁通过。生产上线仍需要真实 SDK/Collector、访问控制、WORM/签名审计、真实多窗口 SLO 和值班系统。
