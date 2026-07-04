# v0.4 静态原型设计 QA 报告

日期：2026-07-02  
状态：静态目标 QA 通过，Chrome 浏览器渲染 QA 通过  
对象：`v0.4-低保真可点击原型`

## 1. 结论

当前静态原型已通过结构、内容、边界、安全误读、桌面/移动真实渲染和点击流程检查，满足本阶段“无需构建工具的静态 HTML/CSS/JS 教学原型”目标。

```text
final result: passed for static prototype and browser rendering objective
```

说明：浏览器 QA 使用本机 Chrome 进行，临时 HTTP 服务仅用于验证静态文件渲染，不代表项目需要前端构建工具或开发服务器。

## 2. 已通过检查

| 检查项 | 结果 |
|---|---|
| 原型目录存在 | 通过 |
| 仅包含静态文件 | 通过 |
| 未创建 `package.json` | 通过 |
| 未创建 `node_modules` | 通过 |
| 未创建 `.next` | 通过 |
| `node --check app.js` | 通过 |
| 6 个核心页面 | 通过 |
| 13 个 P0 验证主题 | 通过 |
| 每页必备字段 | 通过 |
| RAG 三类问题 | 通过 |
| LLM-Wiki 四步 | 通过 |
| source_files 全部存在 | 通过 |
| 三张视觉方向图自包含加载 | 通过 |
| Markdown 内链 | 通过 |
| JSON 代码块 | 通过 |
| 真实生产按钮 | 未发现 |
| `fetch` / `XMLHttpRequest` / `WebSocket` | 未发现 |
| 表单提交 | 未发现 |
| Chrome 桌面 1440px 渲染 | 通过 |
| Chrome 移动 390px 渲染 | 通过 |
| 6 页导航点击 | 通过 |
| RAG 三类 tab 点击 | 通过 |
| LLM-Wiki 四层 tab 点击 | 通过 |
| 坏设计 / 低分回流状态切换 | 通过 |
| 横向滚动 / 元素溢出 | 未发现 |
| console error / failed request | 未发现 |

## 3. 文件边界

原型交付包允许包含：

```text
index.html
styles.css
app.js
README.md
设计QA报告.md
图像素材/
浏览器QA截图/
```

不允许出现：

```text
package.json
node_modules
.next
dist
build
vite.config.js
next.config.js
tsconfig.json
```

## 4. 内容覆盖

首轮 6 页：

1. C 首页 / 学习路线地图。
2. A 全链路分层控制台。
3. B 事故推演工作台。
4. RAG 问题诊断器。
5. LLM-Wiki 知识层。
6. 证据与门禁页。

13 个 P0 验证主题均已覆盖：

- 建议与执行分离。
- Runtime 状态。
- Tool Gateway。
- 长线任务。
- RAG 找不到。
- RAG 找错租户。
- RAG 引用可信。
- 记忆污染。
- Eval 门禁。
- Trace/Audit。
- 沙箱风险。
- 多 Agent 协同。
- LLM-Wiki 知识层。

## 5. 安全边界

每页必须保持可见：

```text
学习模式 Learning mode
模拟数据 Mock data
不执行真实操作 No real execution
来源文件 Source files
```

静态检查未发现真实生产动作入口。以下词如出现，只允许处于“坏设计”“事故”“不代表什么”语境中：

- 退款。
- 发布。
- 审批。
- 生产。
- 凭据。
- 工具调用。

## 6. 浏览器 QA 证据

本轮已用本机 Chrome 验证：

| 浏览器 QA | 结果 |
|---|---|
| 桌面截图 | 1440px 视口无重叠、无溢出、图片加载正常 |
| 移动截图 | 390px 视口导航折叠、证据面板下移、文字可读 |
| 点击流程 | 6 页导航、状态切换、RAG tab、LLM-Wiki tab、评分按钮均通过 |
| 视觉风险 | 未发现真实生产动作可点击入口 |
| 可访问性 | 保留 skip link、focus ring、按钮类型、减少动画规则 |
| 网络与控制台 | `0` failed request，`0` console error |

证据文件：

```text
浏览器QA截图/browser-qa-report-standalone.json
浏览器QA截图/desktop-home-standalone.png
浏览器QA截图/desktop-rag-standalone.png
浏览器QA截图/desktop-wiki-standalone.png
浏览器QA截图/mobile-home-standalone.png
浏览器QA截图/mobile-rag-standalone.png
浏览器QA截图/mobile-wiki-standalone.png
```

已修复项：

- 将三张视觉方向图复制到 `图像素材/`，避免单独托管原型目录时图片 404。
- 增加空 favicon，避免浏览器默认请求 `favicon.ico` 造成无关 404。
