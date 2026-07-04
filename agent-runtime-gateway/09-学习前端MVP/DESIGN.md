# Design

## Design Intent

这是一个学习型 product UI，不是营销页，也不是生产后台。设计目标是让用户在安静可信的控制台里，看见工业级 Agent 教学过程如何一步步推进。

物理使用场景：用户坐在桌面电脑前，左侧看课程阶段，中心完成题目和对照图，右侧检查事故、证据和评分；他会长时间阅读、点选、追问和复盘，所以界面要克制、稳定、可扫描。

## Surface Strategy

- 默认 register：product。
- 视觉策略：restrained product UI。
- 第一屏直接进入学习控制台，不做 hero。
- 页面结构使用 app shell、侧边导航、顶部状态条、主工作区、右侧证据面板。
- 卡片只用于独立对象，例如复述题、证据、评分、导师反馈。
- 所有模型反馈必须通过服务端代理，浏览器不接触 API Key。

## Color Tokens

使用 OKLCH。颜色要有语义，不做单一蓝紫主题，不做米色纸感主题。

```css
:root {
  --bg: oklch(0.985 0.006 190);
  --surface: oklch(0.965 0.008 190);
  --surface-raised: oklch(0.995 0.003 190);
  --ink: oklch(0.225 0.025 210);
  --ink-muted: oklch(0.455 0.026 210);
  --line: oklch(0.875 0.012 205);
  --accent: oklch(0.55 0.105 172);
  --accent-strong: oklch(0.43 0.11 172);
  --accent-soft: oklch(0.925 0.04 172);
  --success: oklch(0.56 0.12 145);
  --warning: oklch(0.69 0.14 78);
  --danger: oklch(0.57 0.16 28);
  --blocked: oklch(0.5 0.11 330);
  --focus: oklch(0.62 0.13 172);
}
```

## Typography

- 中文优先使用 `system-ui`、`Microsoft YaHei UI`、`PingFang SC`、`Noto Sans CJK SC`。
- 不使用 display font。
- 正文字号 14-16px，UI 标签 12-13px，页面标题 24-28px。
- 行高 1.45-1.65。
- 字间距保持 0，不使用负 letter spacing。

## Language And Localization

默认中文优先双语。导航、按钮、教学问题、复述卡、错误提示使用中文；关键工业术语保留英文括注，例如运行时 Runtime、网关 Gateway、策略 Policy、检索增强 RAG、轨迹 Trace、审计 Audit、评测 Eval、发布门禁 Release Gate。

按钮按“动作 + 对象”写，例如“记录本题评分”“进入下一题”“请导师反馈”。不得使用“生产已就绪”等会让用户误读的文案。

## Layout System

桌面默认布局：

```text
Top status bar
Left phase rail | Main learning workspace | Right evidence panel
```

移动端：

- 顶部状态条换行展示。
- 左侧阶段栏变成纵向列表。
- 右侧证据面板下移。
- 不允许横向滚动和按钮文字溢出。

## Components

- PhaseRail：13 个 P0 学习题、完成状态、当前题。
- LearningModeBadge：学习模式 / 模拟数据 / 不执行真实操作 / 来源文件。
- RestatementCard：看图前理解、看图后复述、坏设计判断、本地评分。
- EvidencePanel：事故、负责层、最小证据、source files。
- TutorProxyPanel：Agnes 导师代理或本地反馈，明确服务端环境变量边界。
- LearningRecordExport：导出本地学习记录，不上传真实数据。
- GateDecision：低于 3 分停下重讲，达到门槛才进入下一题。

## Premium Craft Standard

高级感来自信息秩序和产品成熟度，不来自装饰。必须检查：

- 当前 Phase 是否可见。
- 当前学习问题是否可见。
- 事故和负责层是否可见。
- mock 边界是否可见。
- 复述评分和低分回流是否可见。
- 是否没有真实生产操作暗示。
- 桌面和移动端是否没有横向滚动、遮挡和文本溢出。

## Radius, Borders, Shadows

- 默认 radius：8px。
- 小控件 radius：6px。
- 不使用 24px 以上大圆角。
- 默认分隔优先用线和间距，不依赖阴影。
- 不在同一元素上同时使用 1px 边框和大模糊阴影。

## Motion

只用于状态变化：题目切换、评分提交、门禁状态变化。默认 150-220ms，并支持 `prefers-reduced-motion: reduce`。不做页面加载编舞，不做装饰性运动。

## Sustainable Learning Iteration

每一轮学习都要留下可迭代证据：用户复述原文、0-5 评分、卡点标签、误解类型、对应 Phase、对应系统层、回流动作。低分复述要推动术语解释、失败案例、RAG 评测样例、知识卡、复述卡和页面交互的下一轮更新。
