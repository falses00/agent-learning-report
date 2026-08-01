# S6 测试说明

运行：

```powershell
cd "agent-runtime-gateway\20-源码"
python -m pytest ..\21-测试\test_release_gate.py -q
python -m agent_course.cli release-gate ..\22-评测集\s6-release-manifest.json
python -m agent_course.cli release-gate-eval ..\22-评测集\s6-release-gate-adversarial.json
```

测试分三层：

| 层 | 验证 | 失败含义 |
|---|---|---|
| Source suite | S1-S5 的 contract、tool、RAG、durability、memory 行为 | Agent 候选能力或安全回归 |
| Release gate | split、版本、critical、judge、holdout、预算、owner、hash | 发布规则不完整或证据不可信 |
| Gate adversarial | 16 种 mutation 对门禁本身的绕过 | 评测器可能产生 false pass |

至少保留一个反例：34/35 高通过率但单个 critical failure 仍必须 block。路径穿越、未知字段和生产无私有 holdout 也必须失败。
