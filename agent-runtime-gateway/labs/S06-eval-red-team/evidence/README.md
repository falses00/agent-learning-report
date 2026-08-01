# S6 证据清单

每次候选发布登记以下最小证据：

| 字段 | 内容 |
|---|---|
| Candidate | commit/build ID 与时间 |
| Versions | agent、prompt、model、tool、policy、memory、knowledge、eval、grader |
| Commands | source suite、release gate、gate adversarial 的完整命令 |
| Outcome | case/assertion 数、critical failure、blocker/warning |
| Operations | latency/cost/flake 的真实来源；fixture 必须显式标记 |
| Lineage | manifest/evidence/decision SHA-256 |
| Review | reviewer、risk owner、例外与到期时间 |
| Regression | 事故 source、owner、case ID、修复和重放结果 |

合格证据必须能回答：测了什么、在哪个环境、使用哪些版本、谁判定、为什么通过/阻塞、如何复现、哪些能力仍未证明。

禁止提交真实用户输入、凭据、内部 trace、私有 holdout 内容或可逆匿名化数据。生产 holdout 只记录访问控制位置、版本和聚合结果。
