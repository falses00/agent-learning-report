import { NextResponse } from "next/server";
import { learningCases } from "@/data/learningCases";

export const runtime = "nodejs";

const baseUrl = process.env.AGNES_BASE_URL || "https://apihub.agnes-ai.com/v1";
const model = process.env.AGNES_MODEL || "agnes-2.0-flash";
const maxAnswerChars = 1600;
const upstreamTimeoutMs = readBoundedInt(process.env.AGNES_TUTOR_TIMEOUT_MS, 12000, 1000, 30000);
const rateLimitPerMinute = readBoundedInt(process.env.AGNES_TUTOR_RATE_LIMIT_PER_MINUTE, 30, 1, 120);
const rateWindowMs = 60_000;
const rateBuckets = new Map<string, { startedAt: number; count: number }>();

type Body = {
  caseId?: string;
  answer?: string;
  stage?: "before" | "after" | "bad_design";
};

export async function POST(request: Request) {
  let body: Body;
  try {
    body = (await request.json()) as Body;
  } catch {
    return json({ error: "请求格式不是 JSON。" }, 400);
  }

  const item = learningCases.find((entry) => entry.id === body.caseId);
  if (!item) {
    return json({ error: "未知学习题目。" }, 404);
  }

  if (!isValidStage(body.stage)) {
    return json({ error: "未知反馈阶段。" }, 422);
  }

  const answer = String(body.answer || "").slice(0, maxAnswerChars);
  if (!answer.trim()) {
    return json({ feedback: "先写下你的理解，我再帮你判断缺了事故、负责层还是证据。", mode: "local" });
  }

  if (!process.env.AGNES_API_KEY) {
    return json({
      feedback: localFeedback(item.topic, answer),
      mode: "local",
    });
  }

  if (!consumeRateLimit(getClientKey(request))) {
    return json({ feedback: "导师代理请求过于频繁，请稍后再试。", mode: "local" }, 429);
  }

  const upstreamUrl = getUpstreamUrl();
  if (!upstreamUrl) {
    return json({ feedback: localFeedback(item.topic, answer), mode: "local" });
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), upstreamTimeoutMs);

  try {
    const upstream = await fetch(upstreamUrl, {
      method: "POST",
      signal: controller.signal,
      headers: {
        Authorization: `Bearer ${process.env.AGNES_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model,
        temperature: 0.2,
        max_tokens: 420,
        messages: [
          {
            role: "system",
            content:
              "你是工业级 Agent/RAG 学习导师。只根据学习目标反馈，不要写代码。用中文指出学习者答案是否包含事故、负责层、最小证据。不要声称这是生产系统。",
          },
          {
            role: "user",
            content: `主题：${item.topic}\n事故：${item.accident}\n负责层：${item.responsibleLayer}\n最小证据：${item.evidence}\n学习者回答：${answer}\n请给出不超过 120 字的反馈，并给一个下一句复述建议。`,
          },
        ],
      }),
    });

    if (!upstream.ok) {
      return json({ feedback: localFeedback(item.topic, answer), mode: "local" });
    }

    const data = (await upstream.json()) as { choices?: Array<{ message?: { content?: string } }> };
    const feedback = data.choices?.[0]?.message?.content || localFeedback(item.topic, answer);
    return json({ feedback, mode: "agnes" });
  } catch {
    return json({ feedback: localFeedback(item.topic, answer), mode: "local" });
  } finally {
    clearTimeout(timeout);
  }
}

function localFeedback(topic: string, answer: string) {
  const short = answer.length > 80 ? `${answer.slice(0, 80)}...` : answer;
  return `本地反馈：你已经围绕“${topic}”作答。下一步请补齐三件事：现实事故、负责层、最小证据。你的原回答片段：“${short}”。`;
}

function isValidStage(stage: Body["stage"]) {
  return stage === "before" || stage === "after" || stage === "bad_design";
}

function getUpstreamUrl() {
  try {
    const url = new URL("/v1/chat/completions", ensureTrailingSlash(baseUrl));
    if (url.protocol !== "https:" && url.protocol !== "http:") return null;
    if (!getAllowedHosts().has(url.hostname)) return null;
    return url.toString();
  } catch {
    return null;
  }
}

function ensureTrailingSlash(value: string) {
  return value.endsWith("/") ? value : `${value}/`;
}

function getAllowedHosts() {
  const hosts = process.env.AGNES_ALLOWED_HOSTS || "apihub.agnes-ai.com";
  return new Set(
    hosts
      .split(",")
      .map((host) => host.trim().toLowerCase())
      .filter(Boolean),
  );
}

function getClientKey(request: Request) {
  const forwarded = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim();
  const realIp = request.headers.get("x-real-ip")?.trim();
  return forwarded || realIp || "local";
}

function consumeRateLimit(clientKey: string) {
  const now = Date.now();
  const bucket = rateBuckets.get(clientKey);

  if (!bucket || now - bucket.startedAt >= rateWindowMs) {
    rateBuckets.set(clientKey, { startedAt: now, count: 1 });
    return true;
  }

  if (bucket.count >= rateLimitPerMinute) return false;
  bucket.count += 1;
  return true;
}

function readBoundedInt(value: string | undefined, fallback: number, min: number, max: number) {
  const parsed = Number.parseInt(value || "", 10);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(max, Math.max(min, parsed));
}

function json(data: unknown, status = 200) {
  return NextResponse.json(data, {
    status,
    headers: {
      "Cache-Control": "no-store",
    },
  });
}
