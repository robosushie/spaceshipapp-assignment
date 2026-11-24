import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type Dispatch,
  type KeyboardEvent as ReactKeyboardEvent,
  type PointerEvent as ReactPointerEvent,
  type Ref,
  type SetStateAction,
} from "react"
import { PlusIcon, SendIcon, XIcon } from "lucide-react"
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  Scatter,
  ScatterChart,
  XAxis,
  YAxis,
} from "recharts"

import { Bubble, BubbleContent } from "@/components/ui/bubble"
import { Button } from "@/components/ui/button"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Message, MessageContent } from "@/components/ui/message"
import {
  MessageScroller,
  MessageScrollerButton,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerProvider,
  MessageScrollerViewport,
} from "@/components/ui/message-scroller"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ApiError, api } from "@/lib/api"
import { chatText, emptyThread, type ChatDesk, type ChatMessage, type ChatThread } from "@/lib/chats"
import { cn } from "@/lib/utils"
import type { QuestionChart, QuestionExplanation, QuestionResult } from "@/types/desk"

const CHAT_MIN = 220
const CHAT_MAX = 720

function clampChatWidth(value: number, viewport: number): number {
  const max = Math.min(CHAT_MAX, Math.round(viewport * 0.7))
  return Math.min(Math.max(value, CHAT_MIN), Math.max(max, CHAT_MIN))
}

export function AgentPanel({
  width,
  onWidth,
  onClose,
  desk,
  setDesk,
}: {
  width: number
  onWidth: (width: number) => void
  onClose: () => void
  desk: ChatDesk
  setDesk: Dispatch<SetStateAction<ChatDesk>>
}) {
  const [question, setQuestion] = useState("")
  const [askingThreadId, setAskingThreadId] = useState<string | null>(null)
  const activeTabRef = useRef<HTMLDivElement>(null)
  const chatDrag = useRef<{ startX: number; startWidth: number } | null>(null)
  const titling = useRef(new Set<string>())
  const composerRef = useRef<HTMLTextAreaElement>(null)
  const activeThread = desk.threads.find((thread) => thread.id === desk.activeId) ?? desk.threads[0]
  const messages = activeThread?.messages ?? []

  useEffect(() => {
    composerRef.current?.focus()
  }, [])

  useEffect(() => {
    activeTabRef.current?.scrollIntoView({ inline: "nearest", block: "nearest" })
  }, [desk.activeId])

  useEffect(() => {
    for (const thread of desk.threads) {
      const first = thread.messages.find((message) => message.role === "user")
      if (!first || thread.title !== first.text || titling.current.has(thread.id)) {
        continue
      }
      titling.current.add(thread.id)
      const threadId = thread.id
      void api<{ title: string }>("/v1/chat-titles", {
        method: "POST",
        body: JSON.stringify({ message: first.text }),
      })
        .then((result) => {
          const title = result.title.trim()
          if (!title) {
            titling.current.delete(threadId)
            return
          }
          setDesk((current) => ({
            ...current,
            threads: current.threads.map((item) =>
              item.id === threadId ? { ...item, title } : item,
            ),
          }))
        })
        .catch(() => {
          titling.current.delete(threadId)
        })
    }
  }, [desk.threads, setDesk])

  function onResizePointerDown(event: ReactPointerEvent<HTMLDivElement>) {
    if (event.button !== 0) {
      return
    }
    event.preventDefault()
    event.currentTarget.setPointerCapture(event.pointerId)
    chatDrag.current = { startX: event.clientX, startWidth: width }
  }

  function onResizePointerMove(event: ReactPointerEvent<HTMLDivElement>) {
    const session = chatDrag.current
    if (!session) {
      return
    }
    onWidth(clampChatWidth(session.startWidth + (session.startX - event.clientX), window.innerWidth))
  }

  function onResizePointerUp(event: ReactPointerEvent<HTMLDivElement>) {
    chatDrag.current = null
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId)
    }
  }

  function onResizeKeyDown(event: ReactKeyboardEvent<HTMLDivElement>) {
    const step = event.shiftKey ? 48 : 16
    if (event.key === "ArrowLeft") {
      event.preventDefault()
      onWidth(clampChatWidth(width + step, window.innerWidth))
    }
    if (event.key === "ArrowRight") {
      event.preventDefault()
      onWidth(clampChatWidth(width - step, window.innerWidth))
    }
  }

  function appendMessage(threadId: string, message: ChatMessage, title?: string) {
    setDesk((current) => ({
      ...current,
      threads: current.threads.map((thread) => {
        if (thread.id !== threadId) {
          return thread
        }
        return {
          ...thread,
          title: title ?? thread.title,
          messages: [...thread.messages, message],
        }
      }),
    }))
  }

  function openThread() {
    const thread = emptyThread()
    setDesk((current) => ({
      activeId: thread.id,
      threads: [...current.threads, thread],
    }))
  }

  function closeThread(threadId: string) {
    setDesk((current) => {
      const index = current.threads.findIndex((thread) => thread.id === threadId)
      const threads = current.threads.filter((thread) => thread.id !== threadId)
      if (threads.length === 0) {
        const thread = emptyThread()
        return { activeId: thread.id, threads: [thread] }
      }
      const activeId =
        current.activeId === threadId
          ? threads[Math.min(index, threads.length - 1)].id
          : current.activeId
      return { activeId, threads }
    })
  }

  async function onAsk() {
    const asked = question.trim()
    const threadId = activeThread?.id
    if (asked.length === 0 || !threadId || askingThreadId) {
      return
    }
    const titled = activeThread.messages.some((message) => message.role === "user")
    appendMessage(
      threadId,
      { id: crypto.randomUUID(), role: "user", text: asked, charts: [] },
      titled ? undefined : asked,
    )
    setQuestion("")
    setAskingThreadId(threadId)
    try {
      const result = await api<QuestionResult>("/v1/questions", {
        method: "POST",
        body: JSON.stringify({ question: asked }),
      })
      appendMessage(threadId, {
        id: crypto.randomUUID(),
        role: "assistant",
        text: result.answer,
        charts: result.plot_required && result.chart ? [result.chart] : [],
        explanation: result.explanation,
      })
    } catch (caught) {
      const unavailable = caught instanceof ApiError && caught.status === 503
      appendMessage(threadId, {
        id: crypto.randomUUID(),
        role: "assistant",
        text: unavailable
          ? "Questions are unavailable until an Anthropic key is configured."
          : caught instanceof ApiError
            ? caught.message
            : "The question could not be answered.",
        charts: [],
      })
    } finally {
      setAskingThreadId(null)
    }
  }

  return (
    <aside
      id="agent-panel"
      aria-label="Agent"
      className="fixed inset-0 z-50 flex flex-col bg-card md:inset-y-0 md:left-auto md:border-s md:shadow-lg md:w-(--chat-width)"
      style={{ "--chat-width": `${width}px` } as CSSProperties}
    >
      <div
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize chat"
        aria-valuemin={CHAT_MIN}
        aria-valuemax={CHAT_MAX}
        aria-valuenow={Math.round(width)}
        tabIndex={0}
        className="group absolute inset-y-0 left-0 z-10 hidden w-3 -translate-x-1/2 cursor-col-resize touch-none items-center justify-center md:flex"
        onPointerDown={onResizePointerDown}
        onPointerMove={onResizePointerMove}
        onPointerUp={onResizePointerUp}
        onPointerCancel={onResizePointerUp}
        onKeyDown={onResizeKeyDown}
      >
        <span
          aria-hidden
          className="h-8 w-1 rounded-full bg-foreground/35 group-hover:bg-foreground group-focus-visible:bg-foreground"
        />
      </div>
      <div className="flex shrink-0 items-end border-b border-border bg-background pt-1.5">
        <div role="tablist" aria-label="Chats" className="flex min-w-0 flex-1 items-end overflow-x-auto">
          {desk.threads.map((thread) => (
            <ChatTab
              key={thread.id}
              thread={thread}
              active={thread.id === desk.activeId}
              tabRef={thread.id === desk.activeId ? activeTabRef : undefined}
              onSelect={() => setDesk((current) => ({ ...current, activeId: thread.id }))}
              onClose={() => closeThread(thread.id)}
            />
          ))}
        </div>
        <div className="mb-1 mr-1 flex shrink-0 items-center">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label="New chat"
            onClick={openThread}
          >
            <PlusIcon />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label="Close agent"
            onClick={onClose}
          >
            <XIcon />
          </Button>
        </div>
      </div>
      <div className="flex min-h-0 flex-1 flex-col">
        <MessageScrollerProvider autoScroll>
          <MessageScroller>
            <MessageScrollerViewport>
              <MessageScrollerContent className="px-4 py-4">
                {messages.length === 0 ? (
                  <MessageScrollerItem messageId="empty">
                    <p className="text-muted-foreground">Ask questions about this book</p>
                  </MessageScrollerItem>
                ) : null}
                {messages.map((message) => (
                  <MessageScrollerItem
                    key={message.id}
                    messageId={message.id}
                    scrollAnchor={message.role === "user"}
                  >
                    <Message align={message.role === "user" ? "end" : "start"}>
                      <MessageContent>
                        <Bubble
                          variant={message.role === "user" ? "default" : "muted"}
                          align={message.role === "user" ? "end" : "start"}
                          className="max-w-[85%]"
                        >
                          <BubbleContent className="rounded-2xl px-3 py-2 text-sm">
                            {chatText(message.text)}
                          </BubbleContent>
                        </Bubble>
                        {message.charts.length > 0 ? <PlotDialog charts={message.charts} /> : null}
                        {message.explanation ? <ExplanationBlock explanation={message.explanation} /> : null}
                      </MessageContent>
                    </Message>
                  </MessageScrollerItem>
                ))}
                {askingThreadId === activeThread?.id ? (
                  <MessageScrollerItem messageId="pending">
                    <Skeleton className="h-24 w-full" />
                  </MessageScrollerItem>
                ) : null}
              </MessageScrollerContent>
            </MessageScrollerViewport>
            <MessageScrollerButton />
          </MessageScroller>
        </MessageScrollerProvider>
      </div>
      <form
        className="border-t p-4 pb-[max(1rem,env(safe-area-inset-bottom))]"
        onSubmit={(event) => {
          event.preventDefault()
          void onAsk()
        }}
      >
        <div className="relative">
          <label htmlFor="question" className="sr-only">
            Question
          </label>
          <textarea
            ref={composerRef}
            id="question"
            rows={3}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault()
                event.currentTarget.form?.requestSubmit()
              }
            }}
            className="block min-h-24 w-full resize-none rounded-lg border border-input bg-transparent px-3 py-2.5 pr-12 pb-10 text-base outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
          />
          <Button
            type="submit"
            variant="ghost"
            size="icon"
            aria-label="Send"
            disabled={askingThreadId !== null || question.trim().length === 0}
            className="absolute right-2 bottom-2 bg-transparent text-primary hover:bg-transparent"
          >
            <SendIcon />
          </Button>
        </div>
      </form>
    </aside>
  )
}

function ChatTab({
  thread,
  active,
  tabRef,
  onSelect,
  onClose,
}: {
  thread: ChatThread
  active: boolean
  tabRef?: Ref<HTMLDivElement>
  onSelect: () => void
  onClose: () => void
}) {
  return (
    <div
      ref={tabRef}
      className={cn(
        "group/tab relative flex shrink-0 items-center",
        active
          ? "z-10 -mb-px rounded-t-[8px] border border-b-0 border-border bg-card text-foreground"
          : "text-muted-foreground hover:text-foreground",
      )}
    >
      <button
        type="button"
        role="tab"
        aria-selected={active}
        className="max-w-36 truncate px-3 py-1.5 text-sm"
        onClick={onSelect}
      >
        {thread.title}
      </button>
      <button
        type="button"
        aria-label={`Close ${thread.title}`}
        className={cn(
          "me-1.5 rounded-[2px] p-0.5 hover:bg-muted",
          active ? "opacity-100" : "opacity-0 group-hover/tab:opacity-100 group-focus-within/tab:opacity-100",
        )}
        onClick={onClose}
      >
        <XIcon className="size-3" />
      </button>
    </div>
  )
}

const PIE_FILLS = [
  "var(--foreground)",
  "var(--primary)",
  "var(--muted-foreground)",
  "var(--muted)",
  "var(--foreground)",
]

const MONTH = /^(\d{4})-(\d{2})$/

function nextMonth(label: string): string {
  const match = MONTH.exec(label)
  if (!match) {
    return label
  }
  const year = Number(match[1])
  const month = Number(match[2])
  if (month === 12) {
    return `${year + 1}-01`
  }
  return `${year}-${String(month + 1).padStart(2, "0")}`
}

function completeChartRows(chart: QuestionChart): Record<string, string>[] {
  const rows = chart.rows.map((row) => ({ ...row }))
  if (chart.type !== "line" || rows.length === 0) {
    return rows
  }
  if (!rows.every((row) => MONTH.test(row[chart.x_key] ?? ""))) {
    return rows
  }
  const byMonth = new Map(rows.map((row) => [row[chart.x_key], row]))
  const labels = [...byMonth.keys()].toSorted()
  const filled: Record<string, string>[] = []
  let cursor = labels[0]
  const end = labels[labels.length - 1]
  const forecast = chart.y_keys.includes("forecast")
  const historyEnd = forecast
    ? rows.reduce<string | null>((latest, row) => {
        const value = row.history
        return value !== undefined && value !== "" ? row[chart.x_key] : latest
      }, null)
    : null
  while (filled.length < 240) {
    const existing = byMonth.get(cursor)
    if (existing) {
      filled.push(existing)
    } else if (forecast && historyEnd !== null && cursor <= historyEnd) {
      filled.push({ [chart.x_key]: cursor, history: "0", forecast: "" })
    } else if (forecast) {
      filled.push({ [chart.x_key]: cursor, history: "", forecast: "" })
    } else {
      const blank: Record<string, string> = { [chart.x_key]: cursor }
      for (const key of chart.y_keys) {
        blank[key] = "0"
      }
      filled.push(blank)
    }
    if (cursor === end) {
      break
    }
    cursor = nextMonth(cursor)
  }
  if (!forecast || historyEnd === null) {
    return filled
  }
  const joined = filled.find((row) => row[chart.x_key] === historyEnd)
  if (joined && (joined.forecast === undefined || joined.forecast === "")) {
    joined.forecast = joined.history
  }
  return filled
}

function Plot({ chart, className }: { chart: QuestionChart; className?: string }) {
  const frame = cn("aspect-auto w-full", className)
  if (chart.type === "pie") {
    const measure = chart.y_keys[0] ?? "value"
    const slices = chart.rows.map((row, index) => ({
      name: row[chart.x_key] ?? String(index),
      value: Number(row[measure] ?? 0),
    }))
    const config = Object.fromEntries(
      slices.map((slice, index) => [
        slice.name,
        { label: slice.name, color: PIE_FILLS[index % PIE_FILLS.length] },
      ]),
    )
    return (
      <ChartContainer config={config} className={frame}>
        <PieChart>
          <ChartTooltip content={<ChartTooltipContent nameKey="name" />} />
          <Pie data={slices} dataKey="value" nameKey="name">
            {slices.map((slice, index) => (
              <Cell key={`${slice.name}-${index}`} fill={PIE_FILLS[index % PIE_FILLS.length]} />
            ))}
          </Pie>
        </PieChart>
      </ChartContainer>
    )
  }
  if (chart.type === "scatter") {
    const series = chart.y_keys.map((key) => ({
      key,
      data: chart.rows.map((row) => ({
        x: Number(row[chart.x_key] ?? 0),
        y: Number(row[key] ?? 0),
      })),
    }))
    const config = Object.fromEntries(
      chart.y_keys.map((key) => [key, { label: columnLabel(key), color: "var(--foreground)" }]),
    )
    return (
      <ChartContainer config={config} className={frame}>
        <ScatterChart>
          <XAxis dataKey="x" type="number" name={columnLabel(chart.x_key)} />
          <YAxis dataKey="y" type="number" width={32} />
          <ChartTooltip content={<ChartTooltipContent />} />
          {series.map((item) => (
            <Scatter
              key={item.key}
              name={columnLabel(item.key)}
              data={item.data}
              fill="var(--foreground)"
            />
          ))}
        </ScatterChart>
      </ChartContainer>
    )
  }
  const rows = completeChartRows(chart)
  const data = rows.map((row) => {
    const point: Record<string, string | number | null> = { ...row }
    for (const key of chart.y_keys) {
      const raw = row[key]
      const missing = raw === undefined || raw === ""
      point[key] = chart.type === "line" && missing ? null : Number(raw ?? 0)
    }
    return point
  })
  const config = Object.fromEntries(
    chart.y_keys.map((key) => [key, { label: columnLabel(key), color: lineColor(key) }]),
  )
  const interval = rows.length > 8 ? "preserveStartEnd" : 0
  if (chart.type === "line") {
    return (
      <ChartContainer config={config} className={frame}>
        <LineChart data={data}>
          <XAxis dataKey={chart.x_key} interval={interval} />
          <YAxis domain={[0, "auto"]} width={32} />
          <ChartTooltip content={<ChartTooltipContent />} />
          {chart.y_keys.map((key) => (
            <Line
              key={key}
              dataKey={key}
              stroke={lineColor(key)}
              strokeWidth={2}
              dot={false}
              connectNulls={chart.y_keys.includes("forecast")}
            />
          ))}
        </LineChart>
      </ChartContainer>
    )
  }
  if (chart.type === "area") {
    return (
      <ChartContainer config={config} className={frame}>
        <AreaChart data={data}>
          <XAxis dataKey={chart.x_key} interval={interval} />
          <YAxis domain={[0, "auto"]} width={32} />
          <ChartTooltip content={<ChartTooltipContent />} />
          {chart.y_keys.map((key) => (
            <Area
              key={key}
              dataKey={key}
              stroke="var(--foreground)"
              fill="var(--foreground)"
              fillOpacity={0.2}
            />
          ))}
        </AreaChart>
      </ChartContainer>
    )
  }
  return (
    <ChartContainer config={config} className={frame}>
      <BarChart data={data}>
        <XAxis dataKey={chart.x_key} interval={interval} />
        <YAxis domain={[0, "auto"]} width={32} />
        <ChartTooltip content={<ChartTooltipContent />} />
        {chart.y_keys.map((key) => (
          <Bar key={key} dataKey={key} fill="var(--foreground)" />
        ))}
      </BarChart>
    </ChartContainer>
  )
}

function lineColor(key: string): string {
  if (key === "forecast") {
    return "var(--chart-2)"
  }
  return "var(--chart-1)"
}

function chartColumns(chart: QuestionChart): string[] {
  const extras = Object.keys(chart.rows[0] ?? {}).filter(
    (key) => key !== chart.x_key && !chart.y_keys.includes(key),
  )
  return [chart.x_key, ...chart.y_keys, ...extras]
}

function columnLabel(key: string): string {
  return key.replaceAll("_", " ")
}

function DataTable({ chart }: { chart: QuestionChart }) {
  const columns = chartColumns(chart)
  const rows = chart.type === "line" ? completeChartRows(chart) : chart.rows
  return (
    <Table>
      <TableHeader>
        <TableRow>
          {columns.map((column) => (
            <TableHead key={column}>{columnLabel(column)}</TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row, index) => (
          <TableRow key={`${row[chart.x_key]}-${index}`}>
            {columns.map((column) => (
              <TableCell key={column}>{row[column] ?? ""}</TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

function PlotPlaceholder() {
  return (
    <svg viewBox="0 0 320 108" className="text-foreground" aria-hidden>
      <line x1="16" y1="22" x2="304" y2="22" stroke="currentColor" strokeOpacity="0.18" />
      <line x1="16" y1="46" x2="304" y2="46" stroke="currentColor" strokeOpacity="0.18" />
      <line x1="16" y1="70" x2="304" y2="70" stroke="currentColor" strokeOpacity="0.18" />
      <path
        d="M16 74 L44 58 L72 64 L100 42 L128 50 L156 30 L184 48 L212 36 L240 56 L268 40 L304 52 L304 86 L16 86 Z"
        fill="currentColor"
        fillOpacity="0.12"
      />
      <path
        d="M16 74 L44 58 L72 64 L100 42 L128 50 L156 30 L184 48 L212 36 L240 56 L268 40 L304 52"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <line x1="16" y1="86" x2="304" y2="86" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}

function ExplanationBlock({ explanation }: { explanation: QuestionExplanation }) {
  const labels = [
    { title: "Tool", values: [explanation.tool === "forecast" ? "Forecast" : "Query"] },
    { title: "Filters", values: explanation.filters },
    { title: "Metrics", values: explanation.metrics },
    { title: "Dimensions", values: explanation.dimensions },
  ]
  return (
    <div className="mt-2 w-full max-w-[85%] rounded-2xl border border-border bg-background p-3 text-sm">
      <p className="text-muted-foreground">How this was computed</p>
      <dl className="mt-3 flex flex-col gap-3">
        {labels.map((item) => (
          <div key={item.title}>
            <dt className="text-muted-foreground">{item.title}</dt>
            <dd className="mt-1">
              {item.values.length > 0 ? item.values.join(" · ") : "None"}
            </dd>
          </div>
        ))}
        {explanation.plan ? (
          <div>
            <dt className="text-muted-foreground">Plan</dt>
            <dd className="mt-1 whitespace-pre-wrap break-words font-mono text-xs">{explanation.plan}</dd>
          </div>
        ) : null}
      </dl>
      {explanation.rows.length > 0 ? (
        <div className="mt-4 max-h-48 overflow-auto">
          <RowsTable rows={explanation.rows} />
        </div>
      ) : null}
    </div>
  )
}

function RowsTable({ rows }: { rows: Record<string, string>[] }) {
  const columns = Object.keys(rows[0] ?? {})
  if (columns.length === 0) {
    return null
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          {columns.map((column) => (
            <TableHead key={column}>{columnLabel(column)}</TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row, index) => (
          <TableRow key={`${columns.map((column) => row[column]).join("|")}-${index}`}>
            {columns.map((column) => (
              <TableCell key={column}>{row[column] ?? ""}</TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

function PlotDialog({ charts }: { charts: QuestionChart[] }) {
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState("plot-0")
  const many = charts.length > 1
  return (
    <div className="flex w-full max-w-full flex-col gap-2">
      {charts.map((chart, index) => (
        <Button
          key={`${chart.title}-${index}`}
          type="button"
          variant="outline"
          className="group relative h-auto w-full max-w-56 self-start rounded-[1rem] p-2 [&_svg]:!h-16 [&_svg]:!w-full [&_svg]:!max-w-none"
          onClick={() => {
            setTab(`plot-${index}`)
            setOpen(true)
          }}
        >
          <span className="sr-only">Open {chart.title}</span>
          <PlotPlaceholder />
          <span className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-0 transition-opacity group-hover:opacity-100">
            <span className="rounded-full bg-foreground px-2 py-0.5 text-xs text-primary-foreground">
              Click me
            </span>
          </span>
        </Button>
      ))}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-h-[calc(100svh-2rem)] overflow-y-auto sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>{many ? "Plots" : charts[0]?.title}</DialogTitle>
            <DialogDescription>The series Postgres counted for this question.</DialogDescription>
          </DialogHeader>
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList>
              {charts.map((chart, index) => (
                <TabsTrigger key={`plot-${index}`} value={`plot-${index}`}>
                  {many ? chart.title : "Plot"}
                </TabsTrigger>
              ))}
              {charts.map((chart, index) => (
                <TabsTrigger key={`data-${index}`} value={`data-${index}`}>
                  {many ? `${chart.title} data` : "Data"}
                </TabsTrigger>
              ))}
            </TabsList>
            {charts.map((chart, index) => (
              <TabsContent key={`plot-panel-${index}`} value={`plot-${index}`}>
                <Plot chart={chart} className="h-48 sm:h-72" />
              </TabsContent>
            ))}
            {charts.map((chart, index) => (
              <TabsContent key={`data-panel-${index}`} value={`data-${index}`}>
                <div className="max-h-[min(24rem,50svh)] overflow-auto">
                  <DataTable chart={chart} />
                </div>
              </TabsContent>
            ))}
          </Tabs>
        </DialogContent>
      </Dialog>
    </div>
  )
}
