(function attachVibeCoding(root) {
  'use strict';

  root.VIBE_CODING = Object.freeze({
    version: '2026-08-09',
    definition: 'Vibe Coding 是用自然语言与 Coding Agent 快速迭代软件的协作方式；工程化版本要求人负责目标、边界与验收，Agent 负责受限探索和实现，机器证据负责判断能否交付。',
    principle: '意图由人确认，事实从仓库读取，变更保持小批量，正确性由可重跑证据证明。',
    modes: [
      { id: 'explore', name: '探索模式', fit: '原型、一次性脚本、界面草图、未知方案比较。', autonomy: '可允许较宽探索，但只能使用假数据和隔离环境。', exit: '方向成立后重写任务契约，不能把原型直接升为生产。' },
      { id: 'delivery', name: '交付模式', fit: '已有仓库中的功能、修复、重构和测试。', autonomy: '小批量修改；每批必须测试、审查 diff 并记录假设。', exit: '验收条件、失败路径、回滚和 CI 全部满足后才合并。' },
      { id: 'restricted', name: '高风险受限', fit: '认证、支付、权限、数据迁移、生产基础设施和安全边界。', autonomy: 'Agent 只做调查、候选 patch 和测试建议；关键决定与执行需独立人工审批。', exit: '安全评审、演练、备份/回滚和责任人签字完成。' },
    ],
    loop: [
      { id: 'frame', name: '定义结果', action: '写清用户问题、非目标、风险等级和完成定义。', artifact: '一页 task brief', failure: '只说“做得更好”，Agent 会自行补产品需求。' },
      { id: 'survey', name: '读取现场', action: '先查 AGENTS/README、相关代码、测试、依赖和 git 状态。', artifact: '相关文件与既有模式', failure: '凭通用记忆重造架构，覆盖用户未提交修改。' },
      { id: 'plan', name: '拆成小批', action: '列 3-7 个可独立验证步骤，标出高风险决策和停止条件。', artifact: '有顺序的执行计划', failure: '一次改太多，失败后无法定位是哪项假设错误。' },
      { id: 'contract', name: '先定验收', action: '把正常、失败、边界、安全和视觉结果写成可执行检查。', artifact: 'acceptance checks', failure: '代码看起来合理，却没有客观完成条件。' },
      { id: 'implement', name: '最小实现', action: '沿现有模式修改最小责任面，不顺手重构无关代码。', artifact: '窄而可读的 diff', failure: '生成代码量成为目标，依赖和抽象不断膨胀。' },
      { id: 'verify', name: '对抗验证', action: '运行目标测试、全量门禁和至少一个失败或回归探针。', artifact: '命令与实际输出', failure: 'Agent 自称完成，测试被跳过、删除或只覆盖 happy path。' },
      { id: 'review', name: '审查交付', action: '检查意图、diff、依赖、secret、权限、性能和回滚，再提交。', artifact: 'review 结论与 commit', failure: '只读最终摘要，不看代码和残余风险。' },
    ],
    guardrails: [
      '给 Agent 最小必要的文件、工具、网络和凭据权限。',
      '把仓库规则、常用命令、架构边界和禁区写入版本化指令文件。',
      '任何外部网页、issue、文档和工具输出都按不可信输入处理。',
      '新增依赖必须核对真实包名、维护状态、许可证、来源和锁文件 diff。',
      '禁止通过删除、skip、放宽断言或吞异常来制造绿色测试。',
      '数据库迁移、认证、支付和生产操作必须具备独立审批与回滚演练。',
      '提交前检查 git diff、未跟踪文件、secret 扫描和供应链告警。',
      '把线上事故和 Agent 误判写回 regression、AGENTS 或项目文档。',
    ],
    antiPatterns: [
      { id: 'one-shot', name: '一枪式大提示', symptom: '一个 prompt 同时改产品、架构、依赖、后端和 UI。', repair: '先调查，再按可独立验收的薄切片逐批交付。' },
      { id: 'accept-all', name: 'Accept All', symptom: '只要编译通过就接受全部修改。', repair: '按意图、diff、测试、依赖、安全与回滚六项审查。' },
      { id: 'prompt-only-context', name: '只给聊天描述', symptom: '不让 Agent 读取仓库和现有测试。', repair: '先指定可信文件与相似实现，让事实来自当前代码。' },
      { id: 'green-by-deletion', name: '删测试换绿色', symptom: '失败测试被删除、跳过或断言被放宽。', repair: '锁定测试责任，要求解释每个测试改动和失败根因。' },
      { id: 'dependency-sprawl', name: '依赖膨胀', symptom: '小功能引入多个陌生包或不存在的 API。', repair: '先用现有依赖；新增包逐项核对来源、许可证和维护状态。' },
      { id: 'silent-assumption', name: '隐藏假设', symptom: 'Agent 猜测身份、数据结构或产品行为。', repair: '把假设列入 task brief，关键假设必须由代码、文档或用户确认。' },
      { id: 'unsafe-autonomy', name: '生产环境放权', symptom: 'Agent 持长期凭据、开放网络并可直接部署。', repair: '隔离工作区、短期凭据、egress allowlist、审批和 canary。' },
      { id: 'no-learning-loop', name: '失败不沉淀', symptom: '每次重复解释同一环境问题。', repair: '把稳定教训写入测试、AGENTS、runbook 或可版本化 skill。' },
    ],
    taskContract: `目标：为【用户/场景】实现【可观察结果】。\n非目标：本轮不处理【明确排除项】。\n现状：先读取【规则、相关代码、相似实现、测试】并总结事实。\n约束：保持【架构/依赖/兼容/安全/性能】边界，不改无关文件。\n验收：\n1. 正常路径：【输入 -> 预期】\n2. 失败路径：【错误 -> 明确响应】\n3. 边界/对抗：【极端或攻击输入 -> 阻断】\n4. 质量门禁：【test/lint/type/build/browser/security】\n工作方式：先调查和计划；按最小批次实现；每批运行检查并审查 diff。\n停止条件：遇到【不可逆操作、需求冲突、缺少权威事实】时暂停并说明。\n交付：列出改动、实际命令、结果、残余风险和回滚方式。`,
    sources: [
      { id: 'openai-codex', name: 'OpenAI Codex Use Cases', focus: '理解代码库、构建、测试、审查和迭代工作流', url: 'https://developers.openai.com/codex/use-cases' },
      { id: 'openai-model', name: 'OpenAI Model Guidance', focus: '精简指令、相关工具和代表性 eval', url: 'https://developers.openai.com/api/docs/guides/latest-model' },
      { id: 'anthropic-practice', name: 'Claude Code Best Practices', focus: '仓库指令、TDD、小步提交和可验证循环', url: 'https://www.anthropic.com/engineering/claude-code-best-practices' },
      { id: 'anthropic-expertise', name: 'Agentic Coding and Expertise 2026', focus: '人负责规划决策、领域知识仍影响成功率', url: 'https://www.anthropic.com/research/claude-code-expertise' },
      { id: 'anthropic-containment', name: 'How We Contain Claude 2026', focus: '权限疲劳、沙箱、文件与网络边界', url: 'https://www.anthropic.com/engineering/how-we-contain-claude' },
      { id: 'github-review', name: 'Review AI-generated Code', focus: '功能、意图、质量、依赖和 AI 特有错误审查', url: 'https://docs.github.com/en/copilot/tutorials/review-ai-generated-code' },
      { id: 'github-practice', name: 'GitHub Copilot Best Practices', focus: '明确上下文、测试和自动化检查', url: 'https://docs.github.com/en/copilot/get-started/best-practices' },
      { id: 'github-responsible', name: 'Responsible Use of Coding Agents', focus: '幻觉、不安全建议、命令和人工审查风险', url: 'https://docs.github.com/en/copilot/responsible-use/agents' },
      { id: 'dora-2025', name: 'DORA AI-assisted Development 2025', focus: 'AI 放大既有组织能力，流程与平台决定收益', url: 'https://dora.dev/research/2025/dora-report/' },
      { id: 'nist-devsecops', name: 'NIST DevSecOps and AI', focus: 'AI 产物需要人类监督和可验证流程', url: 'https://pages.nist.gov/nccoe-devsecops/introduction.html' },
    ],
  });
})(globalThis);
