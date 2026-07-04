# 学习前端 MVP

这是工业级 Agent + RAG 课程的可运行学习控制台。它承接 `v0.4-低保真可点击原型`，但仍然是学习产品，不是生产控制台。

## 运行

```powershell
npm install
npm run dev
```

默认本地地址：

```text
http://127.0.0.1:3000
```

## Agnes 接入

Agnes API 只能在服务端使用。不要把 API Key 放进浏览器、源码、公开文档或截图。

复制 `.env.example` 为 `.env.local`，只在本机填写：

```text
AGNES_API_KEY=...
AGNES_BASE_URL=https://apihub.agnes-ai.com/v1
AGNES_ALLOWED_HOSTS=apihub.agnes-ai.com
AGNES_MODEL=agnes-2.0-flash
AGNES_TUTOR_RATE_LIMIT_PER_MINUTE=30
AGNES_TUTOR_TIMEOUT_MS=12000
```

浏览器只调用本项目的 `/api/agnes/tutor`。如果没有配置 `AGNES_API_KEY`，界面会使用本地教学反馈，不会请求外部模型。

更详细的安全接入步骤见：

```text
安全接入真实Agnes密钥.md
```

提交或分享前运行：

```powershell
npm run security:scan
```

该扫描只报告疑似问题的位置和类型，不会打印密钥值。

## 学习边界

- 学习模式 Learning mode。
- 模拟数据 Mock data。
- 不执行真实操作 No real execution。
- 来源文件 Source files。

本项目不会连接真实企业系统，不会执行真实退款、审批、发布或工具调用。

## 安全护栏

- `.env*` 默认全部忽略，只放行 `.env.example` 和 `.env.local.example`。
- `AGNES_ALLOWED_HOSTS` 默认只允许 `apihub.agnes-ai.com`，避免把 Authorization 转发到非预期主机。
- `/api/agnes/tutor` 对真实上游调用有轻量限流和超时降级。
- Next.js 响应包含基础安全 headers，包括 `nosniff`、`DENY` frame 防护、`Referrer-Policy` 和学习 MVP 可用的 CSP。
