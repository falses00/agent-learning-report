# Open Design 入口

生成日期：2026-07-01  
状态：Design brief gate 已进入，未进入代码实现  
目标：把工业级 Agent 教学过程可视化，形成可持续迭代的学习控制台设计包

## 1. 当前设计方式

本项目采用下面的设计流程：

```text
Product Design get-context brief gate
-> 本地 Open Design 设计包
-> Product Design / ImageGen 生成 3 个视觉方向
-> v0.3 页面流与 LLM-Wiki 知识层
-> v0.4-pre 原型前冻结包
-> Product Design 低保真可点击原型
-> Implementation-later 再进入代码实现
```

当前已经允许做：

- 产品上下文文件：`PRODUCT.md`
- 视觉系统文件：`DESIGN.md`
- Open Design 页面蓝图
- 低保真线框
- Product Design brief 播放稿
- 三个视觉方向的生成准备
- v0.3 低保真页面流
- v0.4-pre 原型前冻结包
- 页面状态矩阵
- Mock 数据字典
- 学习验证脚本
- v0.4 静态低保真可点击原型

当前不允许做：

- 创建 Next.js 源码目录。
- 启动 dev server。
- 接真实后端。
- 做真实生产控制台。
- 做真实发布入口。
- 跳过 v0.4-pre 冻结包直接生成代码原型。

## 2. 一句话 brief

把工业级 Agent 教学过程做成学习可视化控制台，让半懂学习者通过工单故事、链路图、失败推演、trace 回放、eval 门禁和 release 学习模拟，学会设计、追问、评审和验收长线 Agent。

语言策略：

```text
中文优先双语。
中文负责理解，英文负责连接官方资料、GitHub 项目和工程术语。
```

界面默认使用中文标签，例如“学习模式”“模拟数据”“不执行真实操作”“来源文件”。关键术语保留英文括注，例如“运行时 Runtime”“策略 Policy”“检索增强 RAG”“轨迹 Trace”“评测 Eval”。

## 3. 设计对象

本次设计对象是一个产品型工具界面，不是品牌站。

核心界面：

- 学习首页
- 全链路可视化页
- Phase 学习页
- 失败推演页
- RAG 诊断器
- 记忆生命周期页
- 沙箱与工具风险页
- 多 Agent 协同页
- Codex 协作轨道
- LLM-Wiki 知识层页
- Trace 回放页
- Eval 门禁页
- Release 学习模拟页

## 4. 必须显示的学习边界

每个页面都必须显示：

```text
学习模式 Learning mode / 模拟数据 Mock data / 不执行真实操作 No real execution / 来源文件 Source files
```

如果视觉方案无法容纳这些边界提示，不进入原型。

## 5. 视觉方向约束

允许探索：

- 工业控制台。
- 高可读信息图。
- 教学工作台。

不允许：

- 营销 hero。
- 大面积紫蓝渐变。
- 装饰性卡片墙。
- 真实生产操作按钮。
- 真实发布按钮。
- 只靠漂亮图形表达学习路径。

## 6. 下一步 Product Design brief

Product Design brief：

```text
目标界面：工业级 Agent 学习可视化控制台。
目标用户：半懂学习者和未来 AI 产品/架构负责人。
核心任务：看懂 Agent Runtime/Gateway 的长线受控链路，并完成复述验收。
视觉基调：安静、可信、可扫描、教学导向、工业控制台。
交互级别：先做静态到轻交互视觉方向，暂不写代码。
硬边界：学习模式 Learning mode、模拟数据 Mock data、不执行真实操作 No real execution、来源文件 Source files 必须可见。
```

Product Design 规则要求：生成视觉方向前必须确认 brief。当前已采用 C/A/B 组合路线；进入原型前必须先通过 v0.4-pre 冻结包，再进入 Product Design 低保真可点击原型。代码实现只属于学习验证通过后的 Implementation-later。

## 7. v0.4-pre 原型前冻结包

进入 Product Design 低保真可点击原型前，必须先读：

1. [v0.4-pre 原型前冻结包](10-v0.4-pre原型前冻结包.md)
2. [页面状态矩阵与逐页验收脚本](11-页面状态矩阵与逐页验收脚本.md)
3. [Mock 数据字典与样例包](12-Mock数据字典与样例包.md)
4. [学习验证脚本与 Go-No-Go](13-学习验证脚本与Go-No-Go.md)
5. [v0.4 低保真可点击原型 Brief 回放](14-v0.4低保真可点击原型Brief回放.md)
6. [v0.4 首轮原型任务说明与验收清单](15-v0.4首轮原型任务说明与验收清单.md)
7. [v0.4 前置完成审计记录](16-v0.4前置完成审计记录.md)
8. [v0.4 静态低保真可点击原型](v0.4-低保真可点击原型/README.md)

冻结包的作用：

```text
把页面流
-> 变成 Product Design 可执行状态矩阵
-> 变成 mock 数据对象
-> 变成逐页验收脚本
-> 变成看图前后复述验证
```

如果这些资产没有通过，就不能进入可点击原型，更不能进入前端工程实现。

v0.4 首轮原型范围已收敛为 6 个核心页面：C 首页、A 全链路、B 事故推演、RAG 诊断器、LLM-Wiki 知识层、证据与门禁页。其余专题先作为抽屉、卡片或合并模块，不扩成完整页面。

v0.4-pre 的最低门禁：

```text
每个页面必须有事故、负责层、source_files、复述题和低分回流。
任何页面让用户误以为可以真实执行、真实发布或接入生产系统，直接判失败。
```
