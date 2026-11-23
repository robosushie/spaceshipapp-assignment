import type { QuestionChart } from "@/types/desk"

const STORAGE_KEY = "spaceship-chats:v1"
const CHART_TYPES = new Set(["bar", "line", "area", "pie", "scatter"])
const RETIRED_METHOD_NOTE =
  "A three-month moving average of monthly quantity, projected forward, with the recommended units equal to the forecast total."

export type ChatMessage = {
  id: string
  role: "user" | "assistant"
  text: string
  charts: QuestionChart[]
}

export type ChatThread = {
  id: string
  title: string
  messages: ChatMessage[]
}

export type ChatDesk = {
  activeId: string
  threads: ChatThread[]
}

export function emptyThread(): ChatThread {
  return { id: crypto.randomUUID(), title: "New chat", messages: [] }
}

export function loadChats(): ChatDesk {
  if (typeof localStorage === "undefined") {
    return freshDesk()
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return freshDesk()
    }
    const parsed: unknown = JSON.parse(raw)
    const desk = parseDesk(parsed)
    return desk ?? freshDesk()
  } catch {
    return freshDesk()
  }
}

export function saveChats(desk: ChatDesk): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(desk))
  } catch {
    // The transcript stays in memory when the browser refuses the write.
  }
}

function freshDesk(): ChatDesk {
  const thread = emptyThread()
  return { activeId: thread.id, threads: [thread] }
}

function parseDesk(value: unknown): ChatDesk | null {
  if (!value || typeof value !== "object") {
    return null
  }
  const record = value as { activeId?: unknown; threads?: unknown }
  if (!Array.isArray(record.threads) || record.threads.length === 0) {
    return null
  }
  const threads = record.threads.flatMap((thread) => {
    const parsed = parseThread(thread)
    return parsed ? [parsed] : []
  })
  if (threads.length === 0) {
    return null
  }
  const activeId =
    typeof record.activeId === "string" && threads.some((thread) => thread.id === record.activeId)
      ? record.activeId
      : threads[0].id
  return { activeId, threads }
}

function parseThread(value: unknown): ChatThread | null {
  if (!value || typeof value !== "object") {
    return null
  }
  const record = value as { id?: unknown; title?: unknown; messages?: unknown }
  if (typeof record.id !== "string" || typeof record.title !== "string" || !Array.isArray(record.messages)) {
    return null
  }
  const messages = record.messages.flatMap((message) => {
    const parsed = parseMessage(message)
    return parsed ? [parsed] : []
  })
  return { id: record.id, title: record.title, messages }
}

function parseMessage(value: unknown): ChatMessage | null {
  if (!value || typeof value !== "object") {
    return null
  }
  const record = value as {
    id?: unknown
    role?: unknown
    text?: unknown
    charts?: unknown
  }
  if (typeof record.id !== "string" || typeof record.text !== "string") {
    return null
  }
  if (record.role !== "user" && record.role !== "assistant") {
    return null
  }
  const charts = Array.isArray(record.charts) ? record.charts.filter(isChart) : []
  return { id: record.id, role: record.role, text: chatText(record.text), charts }
}

export function chatText(text: string): string {
  return text
    .split(RETIRED_METHOD_NOTE)
    .join("")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim()
}

function isChart(value: unknown): value is QuestionChart {
  if (!value || typeof value !== "object") {
    return false
  }
  const chart = value as QuestionChart
  return (
    CHART_TYPES.has(chart.type) &&
    typeof chart.title === "string" &&
    typeof chart.x_key === "string" &&
    Array.isArray(chart.y_keys) &&
    chart.y_keys.every((key) => typeof key === "string") &&
    Array.isArray(chart.rows) &&
    chart.rows.every((row) => row !== null && typeof row === "object")
  )
}
