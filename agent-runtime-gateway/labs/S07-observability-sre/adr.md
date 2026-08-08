# ADR：内部观测合同与可替换 exporter

## 决策

课程使用版本化内部合同 `opspilot.observability.v1`，把现有 Runtime audit 转换为 W3C trace context 和 GenAI operation spans；上游 OTel GenAI 约定固定到具体 commit。

## 原因

- 无 API key、无 Collector 的干净环境仍能运行。
- 先教学 trace、audit、SLO 与事故闭环，不把后端产品操作混入核心原理。
- OTel GenAI agent spans 当前是 Development，直接追踪 `main` 会破坏可复现性。
- 生产可替换 exporter，同时保留测试和门禁合同。

## 未选择

- 直接把 Langfuse、Phoenix 或某个云 APM 作为课程核心：产品 API 会遮蔽信号边界。
- 记录完整 prompt/output：调试便利不足以抵消敏感数据风险。
- 把 hash chain 宣称为 WORM：它能检测导出篡改，不能阻止 SQLite 原始记录被改写。

## 撤销条件

当 OTel GenAI 形成稳定 release，且课程提供真实 Collector 集成实验后，可用 SDK exporter 替代课程适配器；内部 schema、脱敏、SLO 和事故门禁仍需保留。
