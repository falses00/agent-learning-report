(function attachObservabilityLab(root) {
  'use strict';

  root.OBSERVABILITY_LAB = Object.freeze({
    version: '2026-08-08',
    baseline: {
      runs: 6,
      assertions: 36,
      attacks: 14,
      attackAssertions: 46,
      traceCoverage: '100%',
      auditCoverage: '100%',
      p95: '640 ms',
      costPerSuccess: '$0.0033',
    },
    signals: [
      { id: 'trace', name: 'Trace', question: '这一次请求经过了什么路径？', evidence: 'W3C traceparent、父子 span、状态与耗时', retention: '短期调试，错误与高风险运行尾采样保留' },
      { id: 'metric', name: 'Metric', question: '整体是否正在退化？', evidence: '成功率、P95、token、cost、coverage、burn rate', retention: '低基数聚合，按 SLO 窗口保留' },
      { id: 'log', name: 'Log', question: '组件在某一时刻发生了什么？', evidence: '结构化事件、低基数 error.type、run_id', retention: '按诊断价值和数据分类设置期限' },
      { id: 'audit', name: 'Audit', question: '谁基于什么权限做了什么决定？', evidence: 'actor/resource hash、action、outcome、reason、hash chain', retention: '受控访问，按合规期限保留' },
      { id: 'replay', name: 'Replay', question: '能否用同一版本重建失败？', evidence: 'request hash、trace、终态、版本谱系、audit head', retention: '与事故和 regression 生命周期绑定' },
    ],
    trace: [
      { id: 'gateway', label: 'Request gateway', operation: 'invoke_agent', detail: '验证入口事实，生成内部 trace context。', duration: '18 ms' },
      { id: 'retrieval', label: 'Knowledge retrieval', operation: 'retrieval', detail: '先做 tenant、freshness 与 source trust。', duration: '96 ms' },
      { id: 'policy', label: 'Policy decision', operation: 'guardrail', detail: '记录 allow、deny 或 require_approval。', duration: '12 ms' },
      { id: 'tool', label: 'Tool execution', operation: 'execute_tool', detail: '只记录最小元数据与结果引用。', duration: '380 ms' },
      { id: 'terminal', label: 'Terminal state', operation: 'invoke_agent', detail: '核对回复、operation ledger 与 audit。', duration: '134 ms' },
    ],
    rules: [
      { signal: 'secret / PII 出现在导出', severity: 'P0', response: 'PAGE + DISABLE', reason: '泄漏事件错误预算永远为 0', evidence: 'finding path + trace + access audit' },
      { signal: 'trace 或关键 audit 缺失', severity: 'P1', response: 'PAGE + FREEZE', reason: '无法定位和追责的版本不能继续发布', evidence: 'coverage diff + writer health' },
      { signal: 'audit hash chain 失效', severity: 'P1', response: 'PAGE + PRESERVE', reason: '证据可能被修改或导出不完整', evidence: 'chain head + failed ordinal' },
      { signal: '短窗 burn rate >= 14.4', severity: 'P1', response: 'PAGE', reason: '约 1 小时内快速消耗月度预算', evidence: '长短窗口 SLI + release version' },
      { signal: '长窗 burn rate >= 3', severity: 'P2', response: 'TICKET', reason: '慢性退化需要负责人和截止时间', evidence: 'slice + trend + owner' },
      { signal: 'P95 或 cost 超预算', severity: 'P2', response: 'FREEZE / TICKET', reason: '不可运营的候选不能进入下一阶段', evidence: '端到端分位数 + usage source' },
      { signal: '单次可恢复 provider timeout', severity: 'P3', response: 'OBSERVE', reason: '没有用户影响或预算快速燃烧时不应叫醒值班者', evidence: 'retry outcome + aggregate SLI' },
      { signal: '非关键 debug log 缺失', severity: 'P3', response: 'BACKLOG', reason: '保留信噪比，避免告警疲劳', evidence: 'diagnostic gap + owner' },
    ],
    responses: [
      { id: 'page', label: '立即分页', detail: '马上止损，冻结发布并保全证据。' },
      { id: 'ticket', label: '建立工单', detail: '绑定 owner、截止时间和回归用例。' },
      { id: 'observe', label: '继续观察', detail: '保留轨迹并监测聚合 SLI，不制造告警疲劳。' },
    ],
    scenarios: [
      {
        id: 'secret-export', title: 'Span 导出包含 API key', observation: '一个 error span 的 debug.prompt 中出现 secret canary；请求尚未产生外部副作用。', expected: 'page', severity: 'P0', blocker: 'SENSITIVE_TELEMETRY_DETECTED', reason: '敏感内容进入观测后端本身就是泄漏，需要停用采集路径并保全访问证据。', misconception: '误区：只有发送给最终用户才算泄漏。', evidence: 'finding path、trace_id、exporter 配置、访问 audit、secret rotation 记录', signalIds: ['trace', 'audit', 'replay']
      },
      {
        id: 'audit-gap', title: '退款已完成但 tool.approve audit 缺失', observation: 'operation ledger 显示 committed，trace 中有 execute_tool，但审批责任证据不存在。', expected: 'page', severity: 'P1', blocker: 'AUDIT_COVERAGE_GAP', reason: '高风险动作无法证明授权链，应冻结同类发布并核查绕过路径。', misconception: '误区：工具执行成功就足以证明流程正确。', evidence: 'operation_id、trace、audit writer health、gateway route diff', signalIds: ['trace', 'audit', 'replay']
      },
      {
        id: 'fast-burn', title: '1 小时窗口 burn rate = 16.7', observation: '端到端成功率跌破 99% SLO，短窗和长窗同时越过 page 阈值。', expected: 'page', severity: 'P1', blocker: 'ERROR_BUDGET_FAST_BURN', reason: '快速预算燃烧说明用户影响正在扩大，应立即止损而不是等日报。', misconception: '误区：只有服务完全不可用才值得分页。', evidence: 'short/long window SLI、版本切片、trace exemplars、回滚结果', signalIds: ['metric', 'trace', 'replay']
      },
      {
        id: 'slow-burn', title: '3 天窗口 burn rate = 3.4', observation: '没有突发尖峰，但某模型路由的失败率连续三天缓慢上升。', expected: 'ticket', severity: 'P2', blocker: 'ERROR_BUDGET_SLOW_BURN', reason: '慢性退化需要明确 owner 和期限，但通常不应在深夜叫醒值班者。', misconception: '误区：不分页就等于可以忽略。', evidence: 'route slice、三天趋势、owner、修复期限、regression case', signalIds: ['metric', 'trace']
      },
      {
        id: 'single-timeout', title: '单次 provider timeout 后 fallback 成功', observation: '一条 span 为 timeout，用户结果正确，当前窗口成功率和 burn rate 未变化。', expected: 'observe', severity: 'P3', blocker: 'NONE', reason: '保留错误 trace 并观察聚合趋势即可，单次可恢复故障不应制造告警疲劳。', misconception: '误区：任何 error span 都必须立即分页。', evidence: 'error.type、fallback span、用户终态、窗口 SLI', signalIds: ['trace', 'metric']
      },
      {
        id: 'cost-drift', title: '质量不变但 cost/success 超预算', observation: '新 prompt 让输出 token 增加 4 倍，成功率不变，cost/success 超过发布预算。', expected: 'ticket', severity: 'P2', blocker: 'COST_PER_SUCCESS_BUDGET_EXCEEDED', reason: '成本是可运营性 SLO，应冻结该候选并定位 token 与工具调用来源。', misconception: '误区：只要答案质量不退化，成本可以上线后再看。', evidence: 'token usage、model route、tool count、candidate version、回退对照', signalIds: ['metric', 'trace', 'replay']
      },
      {
        id: 'external-sampled', title: '外部请求强制 sampled=1', observation: '攻击者持续发送 sampled flag，试图放大存储量和 tracing 账单。', expected: 'ticket', severity: 'P2', blocker: 'EXTERNAL_SAMPLING_OVERRIDE_TRUSTED', reason: '入口应使用内部采样策略，外部 sampled 只能作为不可信信号。', misconception: '误区：W3C header 是标准字段，所以可以无条件信任。', evidence: 'ingress sampling decision、rate/cost trend、caller slice', signalIds: ['trace', 'metric', 'audit']
      },
      {
        id: 'debug-log-gap', title: '非关键 debug log 缺一条', observation: 'trace、audit、终态和 SLO 都完整，仅一个低价值 debug 事件未记录。', expected: 'observe', severity: 'P3', blocker: 'NONE', reason: '进入普通改进队列即可，避免把所有观测差异升级为事故。', misconception: '误区：观测字段越多越工业级。', evidence: '现有 trace coverage、diagnostic gap、backlog owner', signalIds: ['log', 'trace']
      },
    ],
    sources: [
      { name: 'OpenTelemetry GenAI agent spans', focus: 'invoke_agent、execute_tool 与 Development 状态', url: 'https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md' },
      { name: 'OpenTelemetry GenAI events', focus: 'input/output content 为 opt-in，并需过滤与截断', url: 'https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-events.md' },
      { name: 'W3C Trace Context', focus: 'traceparent、tracestate、采样与隐私边界', url: 'https://www.w3.org/TR/trace-context/' },
      { name: 'Google SRE SLO', focus: 'SLI、SLO、分位数与用户影响', url: 'https://sre.google/sre-book/service-level-objectives/' },
      { name: 'Google SRE alerting on SLOs', focus: 'multi-window multi-burn-rate', url: 'https://sre.google/workbook/alerting-on-slos/' },
      { name: 'OpenAI observability integrations', focus: 'model、tool、handoff、guardrail 与 custom spans', url: 'https://developers.openai.com/api/docs/guides/agents/integrations-observability' },
      { name: 'OWASP Logging Cheat Sheet', focus: '禁止直接记录 token、PII、password 与 key', url: 'https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html' },
      { name: 'NIST SP 800-92', focus: '企业日志管理生命周期', url: 'https://csrc.nist.gov/pubs/sp/800/92/final' },
      { name: 'OpenTelemetry Sampling', focus: '头采样、尾采样、可观测成本与遗漏稀有失败的权衡', url: 'https://opentelemetry.io/docs/concepts/sampling/' },
      { name: 'OpenInference Semantic Conventions', focus: 'Agent、Tool、Retriever、Guardrail 与 Evaluator 的可交换 span kind', url: 'https://arize-ai.github.io/openinference/spec/semantic_conventions.html' },
      { name: 'NIST AI RMF Core', focus: '持续监测、响应、恢复、停用和变更管理', url: 'https://airc.nist.gov/airmf-resources/airmf/5-sec-core/' },
      { name: 'OWASP AI Agent Security Cheat Sheet', focus: '重大变更后重跑对抗测试、保留结构化决策元数据', url: 'https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html' },
      { name: 'OWASP Agent Observability Standard', focus: '尚在演进的跨 Agent 可插桩、可追踪和可检查方向', url: 'https://owasp.org/www-project-agent-observability-standard-2/' },
    ],
    future: [
      { kind: 'evidence', title: 'Agent trace 正在覆盖工具与工作流语义', detail: 'OTel 与 Agent SDK 已把模型调用、工具、handoff、guardrail 和 workflow 拆成可关联信号。' },
      { kind: 'evidence', title: '内容采集转向默认关闭', detail: '上游规范把 prompt、system instructions 和 output 视为 opt-in 高风险数据。' },
      { kind: 'evidence', title: 'Eval 与 trace 形成同一改进循环', detail: '运行轨迹开始直接进入 trace grading、回归集与发布门禁。' },
      { kind: 'evidence', title: '采样策略需要作为被监控的系统运营', detail: 'OpenTelemetry 明确区分头采样与尾采样；尾采样能保留错误与高延迟轨迹，但本身是有状态、需容量规划的组件。' },
      { kind: 'evidence', title: 'AI 风险管理延伸到上线后停用与恢复', detail: 'NIST AI RMF 将持续监测、事故响应、恢复、停用和变更管理放在同一 Manage 闭环中。' },
      { kind: 'inference', title: '树状 trace 会扩展为因果图', detail: '多 Agent 与异步工具会需要 causal graph、artifact lineage 和更强根因定位，仍需生产验证。' },
      { kind: 'inference', title: '成本与安全预算会共同驱动采样', detail: 'tail sampling 将同时考虑错误、风险、稀有轨迹、token 成本和租户数据级别。' },
      { kind: 'inference', title: '观测 schema 会成为版本化产品合同', detail: '开发中的 GenAI 语义约定需要内部版本、迁移测试和后端无关的 evidence contract。' },
      { kind: 'inference', title: '跨 Agent 观测将同时承担运行时控制面', detail: 'OWASP AOS 正在推动可插桩、可追踪和可检查的统一方向，但仍应视为演进中的规范而非已稳定合同。' },
    ],
  });
})(globalThis);
