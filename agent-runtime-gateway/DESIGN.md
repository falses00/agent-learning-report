# Design

## Intent

这是长时间使用的学习控制台，不是营销页。用户通常坐在桌面电脑前，一边阅读课程，一边在终端运行命令；移动端主要用于复习、查看路线和自测。

## Information Architecture

```text
Top bar: 总览 / 阶段学习 / 故障演练 / 资料库
Left rail: 搜索、整体进度、分组资料导航、导出/重置
Main workspace: 当前任务、阶段证据、命令或正文
Mobile: 顶部菜单 + 底部四视图导航
```

默认第一屏直接显示“继续学习”和当前阶段，不使用 hero、宣传大字或指标卡墙。

## Tokens

```css
:root {
  --bg: oklch(0.982 0.006 190);
  --surface: oklch(0.995 0.003 190);
  --surface-muted: oklch(0.958 0.009 195);
  --ink: oklch(0.225 0.025 210);
  --ink-muted: oklch(0.455 0.026 210);
  --line: oklch(0.875 0.012 205);
  --accent: oklch(0.52 0.105 172);
  --accent-soft: oklch(0.925 0.04 172);
  --info: oklch(0.55 0.13 245);
  --success: oklch(0.52 0.12 145);
  --warning: oklch(0.66 0.14 78);
  --danger: oklch(0.54 0.16 28);
}
```

色彩只表达当前选择和状态。通过、警告、阻塞必须同时有文字，不能只靠颜色。

## Typography

- 单一系统无衬线字体栈。
- 正文 15-16px，行高 1.65，长文最大 72ch。
- 页面标题 28-32px，面板标题 17-20px。
- 代码使用系统等宽字体。
- 字间距为 0，不使用流体字号。

## Components

- `ViewNav`：切换总览、阶段学习、故障演练和资料库。
- `CourseRail`：搜索、分组章节和整体进度。
- `ContinuePanel`：当前阶段、唯一下一步和运行基线命令。
- `PathSelector`：选择 F0 基础补齐或 S0 工程主线。
- `StageRail`：F0、S0-S10 有序阶段，显示未开始、学习中、已通过。
- `EvidenceChecklist`：理解、实现、正常测试、失败测试、证据五项。
- `CommandBlock`：复制命令并显示预期结果。
- `FailureSimulator`：前端教学模拟，始终显示 Mock 边界。
- `DocumentReader`：单篇阅读、来源路径、上一/下一篇和本地链接路由。
- `ProgressTools`：导出和重置本地学习记录。

所有交互组件必须具备 hover、focus-visible、active、disabled 状态。加载时使用稳定占位，不改变布局。

## Layout

- 桌面左栏 288px，顶部栏 58px，主工作区最大 1180px。
- 900px 以下左栏变为 drawer。
- 720px 以下阶段轨道横向滚动，双栏内容改为单栏，底部显示四项视图导航。
- 固定工具栏必须为正文预留空间，不能覆盖内容。

## Radius And Depth

- 控件 radius 6px，面板 radius 8px。
- 主要依靠分隔线、背景层和间距，不使用大范围阴影。
- 卡片只用于独立对象，不允许卡片嵌套卡片。

## Motion

- 150-220ms，只用于视图切换、状态更新和模拟执行。
- 不做页面加载编舞。
- `prefers-reduced-motion` 下取消平滑滚动和动画延迟。

## Copy

- 按“动作 + 对象”命名按钮，如“运行教学基线”“打开阶段教材”“导出学习进度”。
- 固定边界文案：`本地进度`、`教学模拟`、`不执行真实操作`。
- 不使用“完美通关”，改用“本地标记通过”。
- 不使用 emoji 作为唯一图标或状态信号。

## Accessibility And Safety

- 正文对比度至少 4.5:1。
- 支持键盘导航、跳过导航、清晰焦点和语义化按钮。
- Markdown 渲染禁止脚本、iframe、事件属性和 `javascript:` URL。
- Mermaid 使用严格安全模式；图形失败不阻塞正文。
- 外部 CDN 失败时退回纯文本 Markdown。
