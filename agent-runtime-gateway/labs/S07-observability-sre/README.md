# S07 Observability 与 SRE 实验

## 目标

把现有 OpsPilot Runtime 的 run 与 audit 证据转换为可关联、可脱敏、可聚合、可阻塞发布并能回流事故的观测合同。

## 工程产物

- `agent_course/observability.py`：trace、audit chain、replay、SLO、alert 与 incident。
- `agent_course/observability_evals.py`：对观测门禁执行 mutation。
- `22-评测集/s7-observability-manifest.json`：6 个真实 Runtime 场景与 SLO policy。
- `22-评测集/s7-observability-adversarial.json`：14 个门禁攻击。
- `21-测试/test_observability.py`：正常、失败、对抗回归。

## 快速开始

```powershell
cd "agent-runtime-gateway\20-源码"
python -m pytest ..\21-测试\test_observability.py -q
python -m agent_course.cli observability ..\22-评测集\s7-observability-manifest.json
python -m agent_course.cli observability-eval ..\22-评测集\s7-observability-adversarial.json
```

## 你应该看到

```text
Runtime cases       6 / 6
Assertions          36 / 36
Trace coverage      1.0
Audit coverage      1.0
Replay coverage     1.0
Sensitive exposure  0
P95 fixture         640 ms
Gate attacks        14 / 14
Gate assertions     46 / 46
```

## 实验步骤

1. 读取一个 case 的 W3C `traceparent`、root span 与 child spans。
2. 对照 SQLite audit，确认 export 只保留 hash 和责任字段。
3. 验证 audit chain head 与 replay packet 的版本谱系。
4. 解释 success、P95、cost/success、coverage 和 burn rate 的分母。
5. 运行 adversarial suite，检查每个 blocker 是否产生 alert、incident 和 regression owner。
6. 选择一个攻击，在本地删除对应规则，证明测试会先失败，再恢复规则。

## 三类验证

正常路径：6 个 Runtime case 终态符合预期，观测和 replay 完整。

失败路径：删除 span、audit 或版本字段，门禁必须 block。

对抗路径：将 secret 写进 span、篡改 hash chain、信任外部 sampled flag 或提交未知 mutation，全部 fail closed。

## 边界

本实验不安装真实 OTel SDK 和 Collector。Span 是从真实 Runtime audit 生成的课程适配证据，latency/token/cost 是确定性夹具。生产实现必须替换 exporter 和数据源，但保留相同门禁合同。

## Definition of Done

- 专项测试、baseline 和 adversarial 命令全部通过。
- 能解释至少一个 P0、一个 P1 和一个不应 page 的 P3 场景。
- 证据中不存在 secret canary 和用户身份明文。
- 能指出 hash-chained export 与 WORM 审计存储的差异。
- 事故产物包含 regression case 和 owner。
