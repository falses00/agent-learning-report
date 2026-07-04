"use client";

import type { AnswerRecord } from "@/lib/score";

const key = "agent-learning-mvp-records";

export function loadRecords(): AnswerRecord[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as AnswerRecord[]) : [];
  } catch {
    return [];
  }
}

export function saveRecords(records: AnswerRecord[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(key, JSON.stringify(records));
}
