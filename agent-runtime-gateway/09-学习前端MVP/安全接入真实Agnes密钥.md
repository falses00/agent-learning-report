# 安全接入真实 Agnes 密钥

本项目支持真实 Agnes API，但密钥只能放在本机或部署平台的服务端环境变量中。

## 禁止

- 不要把真实 API key 写入源码。
- 不要把真实 API key 写入 README、PRD、QA 报告、截图说明或课程文档。
- 不要把真实 API key 放进 `public/`，其中所有文件都可能被浏览器访问。
- 不要把真实 API key 写入 `.env.example` 或 `.env.local.example`。
- 不要创建 `NEXT_PUBLIC_AGNES_API_KEY`。`NEXT_PUBLIC_*` 会进入浏览器包。

## 正确做法

1. 复制示例文件：

```powershell
Copy-Item .env.local.example .env.local
```

2. 只在 `.env.local` 中填写真实值：

```text
AGNES_API_KEY=<只在 .env.local 填写真值>
AGNES_BASE_URL=https://apihub.agnes-ai.com/v1
AGNES_ALLOWED_HOSTS=apihub.agnes-ai.com
AGNES_MODEL=agnes-2.0-flash
AGNES_TUTOR_RATE_LIMIT_PER_MINUTE=30
AGNES_TUTOR_TIMEOUT_MS=12000
```

3. 确认 `.env.local` 已被 `.gitignore` 排除。当前规则会忽略 `.env*`，只放行 `.env.example` 和 `.env.local.example`。

4. 运行密钥扫描：

```powershell
npm run security:scan
```

脚本只报告文件名、行号和问题类型，不会打印疑似密钥值。

## 运行边界

- 浏览器只调用 `/api/agnes/tutor`。
- `/api/agnes/tutor` 在服务端读取 `AGNES_API_KEY`。
- 未配置密钥时，接口返回本地教学反馈。
- 上游请求失败或超时时，接口降级为本地教学反馈，不向浏览器暴露密钥、堆栈或上游内部错误。
- `AGNES_ALLOWED_HOSTS` 默认只允许 `apihub.agnes-ai.com`，避免把 Authorization 转发给非预期主机。
- `AGNES_TUTOR_RATE_LIMIT_PER_MINUTE` 默认限制真实上游调用频率，降低代理滥用和额度消耗风险。
- `AGNES_TUTOR_TIMEOUT_MS` 默认 12000ms，超时后回退本地反馈。

## 泄漏后的处理

如果真实 key 曾经进入源码、聊天记录、截图、公开文档或 git 历史：

1. 立即在 Agnes 控制台轮换或吊销该 key。
2. 删除公开位置的密钥，但不要把“删除了”当作已经安全。
3. 重新运行 `npm run security:scan`。
4. 检查 git 历史、构建产物、部署日志和截图目录。
5. 只把新 key 放进 `.env.local` 或部署平台 secret manager。
