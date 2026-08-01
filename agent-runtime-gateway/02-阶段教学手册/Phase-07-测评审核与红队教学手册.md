# Phase 07 - 测评审核与红队教学手册

更新日期：2026-07-31
学习模式：Implementation + Evidence
一句话定义：测评审核是用分层数据集、可校准 grader、真实轨迹与环境终态证据决定 Agent 候选能否发布，并把每次事故固化为回归门禁。

## 1. 本阶段在主线中的位置

```text
S1 contract/tool
  -> S2 approval/policy
  -> S3 RAG/citation
  -> S4 durable execution
  -> S5 governed memory
  -> S6 eval/red-team/release gate
  -> S7 observability/replay
```

S6 不再新加 Agent 能力，而是回答三个招聘和生产都会追问的问题：

1. 你如何证明现有能力真的工作？
2. 你如何证明危险失败一定阻塞发布？
3. 线上事故如何变成下一次发布永远不能再犯的 case？

## 2. 可执行产物

| 产物 | 用途 | 验收命令 |
|---|---|---|
| `s6-release-manifest.json` | 固定版本、数据切分、阈值、红队和回归责任 | `python -m agent_course.cli release-gate ...` |
| `s6-holdout-public-example.json` | 演示留出集职责与污染检测 | `python -m agent_course.cli eval ...` |
| `s6-release-gate-adversarial.json` | 用 16 种 mutation 测门禁本身 | `python -m agent_course.cli release-gate-eval ...` |
| `release_gate.py` | 汇总 source suite 并作出 pass/block 判定 | `test_release_gate.py` |
| evidence hash | 固定 manifest、证据与最终决策 | 查看 gate JSON 输出 |

完整命令、失败注入、自测和清单见[S6 实验](../labs/S06-eval-red-team/README.md)。

## 3. 课时与教学闭环

| 课时 | 核心问题 | 动手任务 | 常见失败 | 通过证据 |
|---|---|---|---|---|
| 7.1 Taxonomy | 测答案、轨迹还是终态 | 把业务需求拆成 7 类 eval | 只测文本 | case matrix |
| 7.2 Dataset | golden/regression/red-team/holdout 如何分工 | 给现有 case 分 split、owner、risk | holdout 被调参污染 | fingerprint + visibility |
| 7.3 Deterministic grader | 哪些结果必须由代码判定 | 写 schema/tool/audit/state assertion | LLM judge 覆盖客观失败 | reproducible reason code |
| 7.4 Judge calibration | 主观维度如何稳定评分 | 人工标注 pass/fail/Unknown 并对比 judge | grader hacking、立场偏差 | agreement + false-pass |
| 7.5 Trajectory/outcome | 为什么答案正确仍可能失败 | 断言审批、工具次数、DB 终态 | 越权或重复副作用 | trace + terminal evidence |
| 7.6 Red team | 如何系统生成攻击 | 设计 mutation families | 只列几条固定 prompt | family coverage |
| 7.7 Reliability/ops | 能力和稳定性如何分开 | 比较 pass@k、pass^k、flake、p95、cost | 只报平均准确率 | slice + budget report |
| 7.8 Release gate | 什么失败必须 block | 攻击候选与门禁本身 | 高总分掩盖 critical | signed/hashable decision |

每课按 `定义 -> 失败 -> 实现 -> 对抗 -> 证据 -> 复盘` 学习，不以“读完文档”作为完成。

## 4. 分层评测矩阵

| 评测层 | 评测对象 | 代表 assertion | 典型 blocker |
|---|---|---|---|
| Contract | 输入输出 schema、错误契约 | 字段、状态、错误码 | schema 不兼容 |
| Tool | 工具选择、参数、次数、审批 | required/forbidden call | 越权或重复副作用 |
| RAG | recall、citation、freshness、ACL | document/chunk/quote provenance | 无证据回答、跨租户召回 |
| Memory | provenance、TTL、污染、删除 | deny/write/search/tombstone | Secret 落盘、删除后可达 |
| Trajectory | plan、gateway、retry、handoff | sequence/required step | 绕过策略层 |
| Outcome | 外部系统真实终态 | DB/API/file/audit | 声称成功但未生效 |
| Security | injection、exfiltration、excessive agency | attack family + critical result | 泄密、越权、沙箱逃逸 |
| Reliability | 单次与连续成功 | pass@1、pass^k、flake | 重试才能偶然成功 |
| Operations | latency、cost、timeout、overrefusal | p95/cost per success | 不可运营或拒绝过多 |

## 5. 发布判定规则

```text
先检查 schema 与版本完整性
  -> 再运行 clean trials
  -> 再验证 deterministic controls
  -> 再检查 trajectory + terminal outcome
  -> 再检查 judge calibration
  -> 再检查 split / holdout contamination
  -> 再检查 red-team / regression coverage
  -> 最后检查 quality / latency / cost / flake budgets
  -> 任一 blocker => block；否则 pass + warnings
```

五条不可放宽的原则：

- critical failure 不参与平均，单条即可阻塞。
- 模型 grader 不能覆盖确定性规则失败。
- 生产 profile 必须使用访问受控的私有 holdout。
- 每个 regression 有 owner、事故来源与证据。
- 评测器无法理解输入时 fail closed，不能静默忽略。

## 6. 真实运行

```powershell
cd "agent-runtime-gateway\20-源码"
python -m pytest ..\21-测试\test_release_gate.py -q
python -m agent_course.cli release-gate ..\22-评测集\s6-release-manifest.json
python -m agent_course.cli release-gate-eval ..\22-评测集\s6-release-gate-adversarial.json
```

当前教学基线应得到：35 个 Agent case、183 条 assertion、0 个 critical failure；16 个 gate adversarial case、34 条 gate assertion 全部通过。公开 holdout 必须产生 `PUBLIC_HOLDOUT_ONLY`，这是正确边界，不是待隐藏的警告。

## 7. 工业化升级路径

| 当前教学基线 | 生产升级 | 何时需要 |
|---|---|---|
| 本地 JSON/JSONL | 数据仓库 + access-controlled holdout | 多团队、敏感或频繁轮换数据 |
| deterministic local runner | ephemeral environment + parallel trial workers | 有外部 API、容器或并发状态 |
| 静态 latency/cost fixture | trace/telemetry 聚合 + canary budget | 接入真实模型和线上流量 |
| 手工 judge calibration | 双人标注、分层抽样、偏差/漂移监控 | model grader 进入发布决策 |
| 固定 mutation cases | 自动攻击生成 + human red team | 工具面、数据面和模型版本扩张 |
| CLI gate | CI check + release approval + rollback | 有独立 staging/production 流程 |
| evidence hash | artifact signing + immutable audit store | 合规、供应链或多方审批 |

具体框架如 Promptfoo、Inspect AI、Langfuse、Phoenix 或厂商 eval API 都应通过 adapter 接入同一任务与证据契约。不要让平台迁移导致历史评测资产失效。

## 8. 五道自测

1. 为什么 task success 必须同时看 transcript/trajectory 和 environment outcome？
2. critical failure 与普通 quality threshold 为什么要分开判定？
3. model grader 在进入发布 gate 前至少要经过哪些校准？
4. public holdout 为什么不能证明生产抗污染？
5. pass@k、pass^k 和 flake rate 分别描述什么？

答错后运行对应 `gate-*` adversarial case，用实际 blocker 解释误区，再补一条最小 regression。答案没有进入测试与证据前，不算掌握。

## 9. 过关与岗位证据

- [ ] 能把一个真实需求写成 task、trial、grader、trajectory、outcome。
- [ ] 能设计 golden、regression、red-team、holdout 并解释 split 泄漏。
- [ ] 能为客观结果写 deterministic assertion。
- [ ] 能构造并校准 model judge，分析 false pass/false fail。
- [ ] 能现场证明高平均分不能掩盖 critical failure。
- [ ] 能把事故变成有 owner 的回归 case。
- [ ] 能解释版本 manifest、evidence hash 和 decision hash。
- [ ] 能明确当前本地 fixture 未证明真实 SLO 与生产安全。

面试作品应展示：一份 release manifest、一条真实 blocked report、一组门禁 adversarial 结果、一个事故到 regression 的闭环、一次阈值决策 ADR，以及完整复现命令。只展示排行榜分数不满足本阶段要求。

## 10. 下一阶段

进入 S7 前，任选一个 blocker，列出定位它所需的 trace、span、tool arguments、policy decision、model/prompt/tool version、token/latency、audit 和 replay 信息。S7 将实现“从发布失败快速定位到责任环节”的可观测性主线。
