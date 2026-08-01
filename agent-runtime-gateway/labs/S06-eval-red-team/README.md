# S6 实验：可阻塞发布的 Agent Eval 与红队门禁

一句话定义：Agent Eval 是对任务结果、工具轨迹、环境终态和风险控制进行版本化验证，并把关键失败转成可复现发布阻塞证据的工程系统。

## 1. 学习主线与真实边界

本实验沿用 OpsPilot 企业工单 Agent，把 S1-S5 的能力装进一条可执行发布链：

```text
release manifest
  -> golden / regression / red-team / holdout suites
  -> deterministic assertions + calibrated judge evidence
  -> trajectory + terminal-state verification
  -> security / quality / latency / cost / reliability gates
  -> pass | block + reason codes + evidence hashes
  -> incident -> owned regression -> next release
```

实现入口：

- `../../20-源码/agent_course/release_gate.py`
- `../../20-源码/agent_course/release_gate_evals.py`
- `../../22-评测集/s6-release-manifest.json`
- `../../22-评测集/s6-release-gate-adversarial.json`
- `../../21-测试/test_release_gate.py`

这是确定性的本地教学基线。它真实运行前序 35 个 Agent case、183 条断言和 16 个门禁攻击 case，证明 critical failure 独立阻塞、模型裁判不能覆盖确定性失败、公开留出集不能冒充生产证据、门禁输入 fail closed；它没有证明真实模型质量、线上 p95、token 成本、私有 holdout 保密性、分布式 trace 完整性或组织审批流程。

## 2. 八个关键概念

| 概念 | 原理 | 缺少时的问题 | 本实验的验收 |
|---|---|---|---|
| Task / trial | task 定义目标和成功条件，trial 是一次独立执行 | 把重试结果混成一次“成功” | 每个 case 独立执行并保留 case result |
| Outcome | 验证 Agent 造成的环境终态，不只读回答文本 | 回答说“已退款”，工具其实没执行或执行两次 | tool count、SQLite 状态和 audit assertion |
| Trajectory | 验证工具、参数、审批、恢复和拒绝的路径 | 最终答案正确但过程越权 | critical suite 声明 trajectory evidence |
| Deterministic grader | schema、权限、金额、引用、状态等客观事实用代码判定 | 模型裁判被措辞骗过 | `MODEL_JUDGE_CANNOT_OVERRIDE_RULE` |
| Calibrated judge | 主观 rubric 的模型裁判先与独立人工标签对齐 | grader 偏置或 reward hacking | agreement 阈值与 critical false-pass 零容忍 |
| Split / holdout | smoke、golden、regression、red-team、holdout 职责分离 | 在公开题上调参后误称泛化 | fingerprint 去重；production 要 private holdout |
| Critical gate | 严重安全/副作用失败不参与平均 | 34/35 的高分掩盖一次跨租户泄漏 | 单条 critical fail 直接 `block` |
| Evidence lineage | Agent、prompt、model、tool、policy、memory、KB、eval、grader 全部固定版本 | 无法复现“为什么这次通过” | manifest、evidence、decision 三个 SHA-256 |

## 3. 先运行候选版本

```powershell
cd "agent-runtime-gateway\20-源码"
python -m agent_course.cli release-gate ..\22-评测集\s6-release-manifest.json
```

必须看到：

- `release_decision == "pass"`，35/35 case 与 183/183 assertion 通过。
- `critical_failures == 0`，judge agreement 为 1.0。
- 结果含 release version manifest 与三个 evidence hash。
- 出现 `PUBLIC_HOLDOUT_ONLY` 警告：公开教学数据不能证明生产抗污染。

不要把本地 `p95_latency_ms=90` 和 `cost_per_success=0` 当成线上数据；manifest 已用 `deterministic-local-fixture:not-a-production-slo` 标明证据边界。

## 4. 再攻击门禁本身

```powershell
python -m agent_course.cli release-gate-eval ..\22-评测集\s6-release-gate-adversarial.json
```

16 个攻击至少覆盖：

| 攻击 | 错误门禁会怎样 | 正确结果 |
|---|---|---|
| 关键失败平均化 | 34/35 仍发布 | `CRITICAL_CASE_FAILED` |
| 模型裁判覆盖规则 | judge 说 pass 就放行越权 | `MODEL_JUDGE_CANNOT_OVERRIDE_RULE` |
| 删除轨迹或终态证据 | 只凭回答文本通过 | `TRAJECTORY_EVIDENCE_MISSING` / `TERMINAL_STATE_EVIDENCE_MISSING` |
| 污染 holdout | 调参题与留出题重复 | `HOLDOUT_CONTAMINATION_DETECTED` |
| 降低 grader 一致率 | 不校准的 judge 决定发布 | `JUDGE_CALIBRATION_BELOW_THRESHOLD` |
| 删除红队族或 owner | 风险覆盖和回归责任静默消失 | `RED_TEAM_COVERAGE_MISSING` / `REGRESSION_OWNERSHIP_INCOMPLETE` |
| 超出延迟/成本/flake 预算 | 质量分数掩盖不可运营性 | 对应预算 blocker |
| 未知 mutation | 测试器忽略不理解的攻击 | `GATE_EVAL_FAILED_CLOSED` |

阅读[失败注入](failure.md)，任选一个 case 先让测试失败，再修复并把证据写入[证据清单](evidence/README.md)。

## 5. 从需求到发布门禁

对“Agent 可以判断退款并在审批后执行”按固定顺序设计：

1. 写 task spec：输入、可用工具、允许的有效路径、终态和禁区。
2. 写 golden case：正常查询、引用政策、等待审批、幂等执行。
3. 写 hard/deny case：无证据拒答、跨租户、伪造角色、工具异常。
4. 将历史事故写成 regression，登记 owner、source 和 evidence。
5. 用 mutation family 生成间接注入、编码变体、工具结果注入和重复副作用攻击。
6. 客观结果先用代码 grader；只有风格、帮助度等主观维度才用模型 grader。
7. 用独立人工标签校准 grader，保留 `unknown`，检查 critical false pass。
8. 候选版本与 eval 数据、grader、policy 一同固定版本后运行门禁。

## 6. 指标不要混成一个分数

| 维度 | 推荐统计 | 发布解释 |
|---|---|---|
| Capability | task success、assertion pass、分层 slice | 看是否真的会做目标任务 |
| Reliability | pass@1、pass^k、flake rate | pass@1 看单次可用；pass^k 看连续成功可靠性 |
| Security | critical failure count、attack family coverage | critical 通常零容忍，不与帮助度平均 |
| Trajectory | required/forbidden tool、审批、retry、handoff | 允许多条合理路径，但硬约束必须满足 |
| Outcome | DB/API/文件/审计终态 | 防止 Agent 声称成功而环境未改变 |
| Operations | p50/p95/p99、cost per success、timeout | 用真实 telemetry，不用本地 fixture 冒充 |
| Judge quality | agreement、false pass/false fail、Unknown rate | grader 也必须被评测和版本化 |

`pass@k` 表示 k 次尝试中至少一次成功，适合看能力上限；`pass^k` 表示 k 次全部成功，更接近生产可靠性。招聘答辩中必须说明采用哪一个，不能只报“跑了 k 次”。

## 7. 常见易错点与修复

| 易错点 | 为什么错 | 修复与回归 |
|---|---|---|
| 只测最终答案 | 工具可能越权或重复执行 | 同时断言 trajectory、audit 与 terminal state |
| 用一个总分决定发布 | 严重泄漏会被大量简单题稀释 | critical blocker 独立于平均指标 |
| 所有 grader 都用 LLM | 客观字段变得不稳定、可被诱导 | 能写 code assertion 的先写 code assertion |
| judge prompt 写好就直接用 | 没有独立真值，不知道偏差方向 | 人工双标样本、agreement、false-pass 与版本 |
| holdout 提交进仓库仍称私有 | 团队可见后可被调参污染 | 生产 holdout 独立 ACL、轮换、只返回聚合结果 |
| 红队只列几条攻击语句 | 对改写、编码和工具注入脆弱 | 按 mutation family 生成并把事故回流 regression |
| 只固定 model version | prompt、tool、policy、memory、KB 变化也会回归 | release manifest 固定完整依赖图 |
| 测试环境有历史残留 | Agent 可能靠旧状态“通过” | 每 trial clean setup/teardown，记录环境版本 |
| 把本地延迟当 SLO | fixture 不含网络、模型和并发 | 线上 telemetry + 分位数 + 流量切片再决策 |

## 8. 五道自测

1. 为什么一个 critical 跨租户失败不能被 99% 的总通过率抵消？
2. 什么结果必须用 deterministic grader，什么结果才适合 model grader？
3. 最终回复正确时，为什么还要验证 trajectory 与 terminal state？
4. 公开 holdout、私有 holdout 和 regression set 的职责有什么不同？
5. `pass@3` 与 `pass^3` 分别回答什么工程问题？

答错后先把误区归类为“目标、轨迹、终态、裁判、数据切分、风险或运营指标”，再运行对应 adversarial case，阅读 blocker reason code，并补一条能让错误门禁稳定失败的 assertion。不要只背术语。

## 9. 一页速记清单

```text
定义：Eval = task + trial + grader + trajectory + outcome + evidence + gate。
数据：smoke 快反馈；golden 基本能力；regression 锁事故；red-team 找绕过；holdout 防过拟合。
判定：客观结果用代码；主观结果才用模型；模型裁判先用人工真值校准。
证据：输入、trace、工具参数、policy decision、终态、版本、owner、hash。
风险：critical failure 零容忍，不能和普通质量平均。
可靠性：pass@k 看至少一次；pass^k 看每次都成功；同时报 flake。
污染：data / environment / grader 三层隔离；公开样例不等于私有留出。
运营：质量、安全、延迟、成本、稳定性、过度拒绝共同进 gate。
回流：incident -> minimal reproducer -> owned regression -> fix -> replay -> release。
边界：本地 deterministic fixture 不是线上模型、私有数据或生产 SLO 证明。
```

## 10. 通过与预习核对

- [ ] 能从一个岗位场景写出 task spec、允许路径、禁区和终态。
- [ ] 能解释 35 个 Agent case、183 条断言来自哪些前序阶段。
- [ ] 基础 release gate 为 pass，门禁 adversarial suite 16/16 通过。
- [ ] 能现场制造一次高平均分 critical failure，并解释 blocker。
- [ ] 能证明 model judge 不可覆盖权限、金额、工具次数等确定性规则。
- [ ] 能设计独立人工校准集，并说明 Unknown 和 false-pass 的用途。
- [ ] 能区分公开教学 holdout 与生产私有 holdout，不夸大证据。
- [ ] 能把一次事故转成有 owner、source、evidence 的 regression case。
- [ ] 能陈述当前基线没有证明的生产能力。
- [ ] 证据不含真实凭据、用户数据或内部日志。

岗位映射：Agent Evaluation、AI QA、LLMOps、可靠性工程、安全红队、数据集治理、CI/CD 发布门禁、事故回归、模型升级评审。

下一阶段预习：选一个被 gate 阻塞的 case，列出定位所需的 trace/span、prompt/model/tool/policy 版本、latency/token、audit 和 replay 信息；S7 将把“为什么失败”变成可观测证据。

## 11. 一手资料与未来走向

- [OpenAI Agent evals](https://developers.openai.com/api/docs/guides/agent-evals)、[Graders](https://developers.openai.com/api/docs/guides/graders)、[Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)：trace eval、grader 校准、持续评测与 eval-driven development。
- [OpenAI Red teaming](https://developers.openai.com/api/docs/guides/red-teaming)、[GPT-Red](https://openai.com/index/unlocking-self-improvement-gpt-red/)：人工与自动红队、攻击发现到防御回流。
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)：task/trial/grader、transcript/outcome、clean environment、pass@k 与 pass^k。
- [Anthropic: Prompt injection defenses](https://www.anthropic.com/research/prompt-injection-defenses)：间接注入与自动化安全评测。
- [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)、[OWASP Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)：风险管理、最小权限和过度代理权。

未来走向不是“让一个更强模型给所有输出打分”，而是混合 grader、可验证环境、自动攻击生成、私有动态 holdout、线上 shadow/canary、事故自动回放与完整证据谱系。OpenAI 现行文档已给出旧 Evals 平台在 2026 年迁移/关停时间，因此课程只依赖可移植 manifest、JSON/JSONL 和本地 runner；具体平台应作为 adapter，而不是评测资产的唯一存储。
