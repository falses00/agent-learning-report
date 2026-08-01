(() => {
  'use strict';

  window.EVAL_LAB = {
    updatedAt: '2026-07-31',
    evidenceNotice: '教学模拟只复现门禁逻辑；公开 holdout、本地延迟和零模型成本都不是生产证明。',
    baseline: [
      { label: 'Agent cases', value: '35', detail: 'S1-S5 source suites' },
      { label: 'Assertions', value: '183', detail: 'deterministic controls' },
      { label: 'Gate attacks', value: '16 / 16', detail: '34 gate assertions' },
    ],
    pipeline: [
      { id: 'manifest', label: 'Version manifest', detail: '固定 agent、prompt、model、tool、policy、memory、KB、eval 与 grader。' },
      { id: 'trial', label: 'Clean trials', detail: '每个 task 独立 setup/run/teardown，禁止历史状态帮助“通过”。' },
      { id: 'deterministic', label: 'Rule graders', detail: 'schema、权限、工具次数、引用与终态优先用代码判定。' },
      { id: 'trajectory', label: 'Trajectory + outcome', detail: '同时核验工具路径、审批、audit 与环境终态。' },
      { id: 'judge', label: 'Judge calibration', detail: '主观 grader 对齐独立人工标签，检查 Unknown 与 critical false pass。' },
      { id: 'holdout', label: 'Split integrity', detail: 'golden、regression、red-team、holdout 去重并隔离。' },
      { id: 'decision', label: 'Release decision', detail: '安全、质量、可靠性、延迟和成本共同决定 pass 或 block。' },
    ],
    rules: [
      { id: 'critical', signal: '任一 critical case 失败', decision: 'BLOCK', reason: '不能被平均分抵消', evidence: 'case + trajectory + terminal state' },
      { id: 'judge-override', signal: 'judge pass / rule fail', decision: 'BLOCK', reason: '裁判不能覆盖确定性控制', evidence: 'grader version + rule reason' },
      { id: 'trajectory', signal: 'critical 轨迹或终态缺失', decision: 'BLOCK', reason: '只看回复无法证明真实行为', evidence: 'trace + DB/API outcome' },
      { id: 'calibration', signal: 'judge agreement 低或 critical false pass', decision: 'BLOCK', reason: 'grader 尚不可信', evidence: 'independent labels' },
      { id: 'holdout', signal: 'holdout fingerprint 重叠', decision: 'BLOCK', reason: '评测数据可能被污染', evidence: 'split fingerprint report' },
      { id: 'private', signal: 'production 无 private holdout', decision: 'BLOCK', reason: '公开题不能证明泛化', evidence: 'ACL + aggregate result' },
      { id: 'coverage', signal: '红队族或 regression owner 缺失', decision: 'BLOCK', reason: '风险或责任静默消失', evidence: 'family + owner + source' },
      { id: 'ops', signal: 'p95 / cost / flake 超预算', decision: 'BLOCK', reason: '不可运营也不能发布', evidence: '真实 telemetry source' },
      { id: 'noncritical', signal: '非关键措辞偏差，仍高于阈值', decision: 'PASS / WARN', reason: '避免把所有差异都升级为事故', evidence: 'slice + backlog owner' },
    ],
    decisions: [
      { id: 'pass', label: '允许发布' },
      { id: 'block', label: '阻塞发布' },
    ],
    scenarios: [
      {
        id: 'critical-average', title: '34/35，但跨租户 case 失败', profile: 'teaching', score: '97.1%', expected: 'block', blocker: 'CRITICAL_CASE_FAILED',
        prompt: '其余 case 全通过，单个 critical authorization case 的 deterministic result 为 fail。',
        reason: '安全边界属于零容忍约束，不能用普通质量平均值稀释。', misconception: '误区：总分超过阈值就能发布。',
        evidence: '失败 case ID、完整 trajectory、terminal state 与 policy audit。', pipeline: ['deterministic', 'trajectory', 'decision'],
      },
      {
        id: 'public-teaching', title: '教学候选全通过，但只有公开 holdout', profile: 'teaching', score: '35/35', expected: 'pass', blocker: 'PUBLIC_HOLDOUT_ONLY',
        prompt: '所有本地 case 通过，holdout 已提交在公开仓库，profile 为 teaching。',
        reason: '教学 profile 可以通过，但必须保留公开留出集不能证明抗污染的警告。', misconception: '误区：任何 warning 都等于 blocker，或公开题等于生产私有题。',
        evidence: 'pass decision、warning、manifest/evidence/decision hash。', pipeline: ['manifest', 'holdout', 'decision'],
      },
      {
        id: 'judge-overrule', title: '模型裁判说通过，权限规则失败', profile: 'teaching', score: 'judge=pass', expected: 'block', blocker: 'MODEL_JUDGE_CANNOT_OVERRIDE_RULE',
        prompt: '回答措辞看似合理，但 deterministic authorization assertion 为 fail。',
        reason: '权限、金额、schema、工具次数和环境终态是客观事实，模型裁判没有覆盖权。', misconception: '误区：更强的 judge 能替代代码和策略引擎。',
        evidence: 'deterministic reason code 与 grader verdict 并列保存。', pipeline: ['deterministic', 'judge', 'decision'],
      },
      {
        id: 'missing-outcome', title: '回复正确，但没有终态证据', profile: 'teaching', score: 'answer=pass', expected: 'block', blocker: 'TERMINAL_STATE_EVIDENCE_MISSING',
        prompt: 'Agent 回复“退款完成”，trace 没有 provider result，数据库也没有可核验 operation state。',
        reason: 'Agent 的陈述不是环境事实；高风险动作必须核验真实副作用和幂等终态。', misconception: '误区：最终答案正确就代表任务成功。',
        evidence: 'provider lookup、operation ledger、audit 与 execution count。', pipeline: ['trajectory', 'decision'],
      },
      {
        id: 'production-public', title: '生产候选只使用公开 holdout', profile: 'production', score: '35/35', expected: 'block', blocker: 'PRIVATE_HOLDOUT_REQUIRED',
        prompt: 'profile 改为 production，但 holdout visibility 仍为 public。',
        reason: '公开数据可被看见、记忆或用于调参，不能作为生产泛化的唯一证据。', misconception: '误区：把文件命名为 holdout 就自动防污染。',
        evidence: '私有数据版本、ACL、轮换记录和聚合结果，不暴露样本。', pipeline: ['holdout', 'decision'],
      },
      {
        id: 'judge-drift', title: 'Judge 与人工标签一致率下降', profile: 'teaching', score: 'agreement=70%', expected: 'block', blocker: 'JUDGE_CALIBRATION_BELOW_THRESHOLD',
        prompt: '新 grader 在独立标注集上的一致率从 100% 降到 70%。',
        reason: '未经校准的 grader 会产生系统性 false pass/false fail，不能参与发布决策。', misconception: '误区：grader 只是一段 prompt，不需要自己的 eval。',
        evidence: '人工标签、grader version、agreement、critical false-pass 与 Unknown rate。', pipeline: ['judge', 'decision'],
      },
      {
        id: 'latency-budget', title: '质量通过，但 p95 超预算', profile: 'production', score: 'p95=4200ms', expected: 'block', blocker: 'P95_LATENCY_BUDGET_EXCEEDED',
        prompt: '能力和安全 case 全通过，但真实 canary 的 p95 超过 2000ms 预算。',
        reason: '无法满足交互或任务 SLO 的候选不具备生产可用性。', misconception: '误区：只要答案好，延迟和成本以后再处理。',
        evidence: '真实 telemetry query、流量切片、时间窗和候选版本。', pipeline: ['trial', 'decision'],
      },
      {
        id: 'minor-wording', title: '一个非关键措辞偏差', profile: 'teaching', score: '98.5%', expected: 'pass', blocker: 'NON_BLOCKING_BACKLOG',
        prompt: '帮助度 rubric 有一个非关键措辞失败，critical、trajectory、outcome 和全部预算通过。',
        reason: '发布规则要区分事故与普通质量差异；在阈值内可通过并进入有 owner 的 backlog。', misconception: '误区：安全门禁越严，就应该拒绝所有不完美输出。',
        evidence: '失败 slice、阈值依据、backlog owner 和后续观察指标。', pipeline: ['judge', 'decision'],
      },
    ],
    sources: [
      { name: 'OpenAI Agent evals', focus: 'trace、datasets、eval runs', url: 'https://developers.openai.com/api/docs/guides/agent-evals' },
      { name: 'OpenAI Graders', focus: 'grader 校准与 reward hacking', url: 'https://developers.openai.com/api/docs/guides/graders' },
      { name: 'OpenAI Eval best practices', focus: 'eval-driven development 与持续评测', url: 'https://developers.openai.com/api/docs/guides/evaluation-best-practices' },
      { name: 'Anthropic Agent evals', focus: 'task/trial/grader、pass@k 与 pass^k', url: 'https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents' },
      { name: 'Anthropic Injection defenses', focus: '自动化间接注入评测', url: 'https://www.anthropic.com/research/prompt-injection-defenses' },
      { name: 'NIST AI 600-1', focus: '生成式 AI 风险管理', url: 'https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf' },
      { name: 'OWASP Excessive Agency', focus: '最小权限与过度代理权', url: 'https://genai.owasp.org/llmrisk/llm062025-excessive-agency/' },
    ],
    future: [
      { kind: 'evidence', title: 'Trace 与 outcome 共同评分', detail: '主流一手实践都在从只看答案转向工具轨迹、guardrail 与环境结果。' },
      { kind: 'evidence', title: '自动红队进入持续评测', detail: '攻击模型和 mutation family 用来发现并固化间接注入与策略绕过。' },
      { kind: 'evidence', title: 'Eval 资产需要可移植', detail: '旧平台会迁移或关停，task、dataset、grader 与证据契约不能只存在单一厂商 API。' },
      { kind: 'inference', title: '动态私有 holdout 将成为核心资产', detail: '企业会轮换访问受控样本，只向开发者返回分层聚合结果和失败类别。' },
      { kind: 'inference', title: 'Gate 会连接 shadow、canary 与 rollback', detail: '离线能力、安全和线上 SLO 将组成同一候选决策，而不是三个独立报表。' },
      { kind: 'inference', title: 'Grader 也会有监控与事故复盘', detail: 'Judge drift、bias 和 reward hacking 会像模型回归一样被版本化和持续审计。' },
    ],
  };
})();
