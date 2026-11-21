import { useEffect, useRef, useState, type CSSProperties, type KeyboardEvent as ReactKeyboardEvent, type PointerEvent as ReactPointerEvent, type Ref } from "react"
import { ChevronLeftIcon, ChevronRightIcon, FunnelIcon, LayoutDashboardIcon, LogOutIcon, PlusIcon, RocketIcon, SendIcon, SettingsIcon, XIcon } from "lucide-react"
import { Link } from "react-router"
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
import { Badge } from "@/components/ui/badge"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Popover, PopoverAnchor, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Message, MessageContent } from "@/components/ui/message"
import {
  MessageScroller,
  MessageScrollerButton,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerProvider,
  MessageScrollerViewport,
} from "@/components/ui/message-scroller"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
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
import { useAuth } from "@/lib/auth"
import {
  emptyThread,
  loadChats,
  saveChats,
  type ChatDesk,
  type ChatMessage,
  type ChatThread,
} from "@/lib/chats"
import { money, statusLabel } from "@/lib/format"
import { cn } from "@/lib/utils"
import type { OrderPage, QuestionChart, QuestionResult } from "@/types/desk"

type FilterKind = "text" | "date" | "number" | "status" | "bool"
type ColumnFilter = { id: string; column: string; op: string; value: string }

const COLUMNS: { id: string; label: string; kind: FilterKind }[] = [
  { id: "order_id", label: "Order", kind: "text" },
  { id: "client_id", label: "Client", kind: "text" },
  { id: "order_date", label: "Order date", kind: "date" },
  { id: "delivery_date", label: "Delivery", kind: "date" },
  { id: "carrier", label: "Carrier", kind: "text" },
  { id: "warehouse", label: "Warehouse", kind: "text" },
  { id: "region", label: "Region", kind: "text" },
  { id: "origin_city", label: "Origin", kind: "text" },
  { id: "destination_city", label: "Destination", kind: "text" },
  { id: "status", label: "Status", kind: "status" },
  { id: "sku", label: "SKU", kind: "text" },
  { id: "category", label: "Category", kind: "text" },
  { id: "quantity", label: "Qty", kind: "number" },
  { id: "unit_price_usd", label: "Unit price", kind: "number" },
  { id: "order_value_usd", label: "Value", kind: "number" },
  { id: "promo", label: "Promo", kind: "bool" },
]

const OPS: Record<FilterKind, { id: string; label: string }[]> = {
  text: [
    { id: "contains", label: "contains" },
    { id: "equals", label: "equals" },
  ],
  date: [
    { id: "on", label: "on" },
    { id: "before", label: "before" },
    { id: "after", label: "after" },
    { id: "empty", label: "is empty" },
  ],
  number: [
    { id: "equals", label: "equals" },
    { id: "gt", label: "greater than" },
    { id: "lt", label: "less than" },
  ],
  status: [{ id: "is", label: "is" }],
  bool: [{ id: "is", label: "is" }],
}

const PAGE = 40
const CHAT_WIDTH_KEY = "spaceship-chat-width"
const CHAT_DEFAULT = 320
const CHAT_MIN = 220
const CHAT_MAX = 720
const STATUSES = ["delivered", "delayed", "in_transit", "exception", "canceled"]

function columnKind(id: string): FilterKind {
  return COLUMNS.find((column) => column.id === id)?.kind ?? "text"
}

function clampChatWidth(value: number, viewport: number): number {
  const max = Math.min(CHAT_MAX, Math.round(viewport * 0.7))
  return Math.min(Math.max(value, CHAT_MIN), Math.max(max, CHAT_MIN))
}

function loadChatWidth(): number {
  if (typeof localStorage === "undefined") {
    return CHAT_DEFAULT
  }
  const stored = Number(localStorage.getItem(CHAT_WIDTH_KEY))
  if (!Number.isFinite(stored)) {
    return CHAT_DEFAULT
  }
  return clampChatWidth(stored, window.innerWidth)
}

function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "exception"
      ? "h-auto rounded-full border border-primary bg-transparent px-2.5 py-0.5 text-sm text-primary"
      : status === "delivered"
        ? "h-auto rounded-full border border-foreground bg-foreground px-2.5 py-0.5 text-sm text-card"
        : "h-auto rounded-full border border-foreground bg-transparent px-2.5 py-0.5 text-sm text-foreground"
  return <Badge className={tone}>{statusLabel(status)}</Badge>
}

const PIE_FILLS = [
  "var(--foreground)",
  "var(--primary)",
  "var(--muted-foreground)",
  "var(--muted)",
  "var(--foreground)",
]

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
  const data = chart.rows.map((row) => {
    const point: Record<string, string | number> = { ...row }
    for (const key of chart.y_keys) {
      point[key] = Number(row[key] ?? 0)
    }
    return point
  })
  const config = Object.fromEntries(
    chart.y_keys.map((key) => [key, { label: columnLabel(key), color: "var(--foreground)" }]),
  )
  const interval = chart.rows.length > 8 ? "preserveStartEnd" : 0
  if (chart.type === "line") {
    return (
      <ChartContainer config={config} className={frame}>
        <LineChart data={data}>
          <XAxis dataKey={chart.x_key} interval={interval} />
          <YAxis domain={[0, "auto"]} width={32} />
          <ChartTooltip content={<ChartTooltipContent />} />
          {chart.y_keys.map((key) => (
            <Line key={key} dataKey={key} stroke="var(--foreground)" dot={false} />
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
        {chart.rows.map((row, index) => (
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

export function Desk() {
  const { signOut } = useAuth()
  const [page, setPage] = useState<OrderPage | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [filters, setFilters] = useState<ColumnFilter[]>([])
  const [openFilterId, setOpenFilterId] = useState<string | null>(null)
  const [offset, setOffset] = useState(0)
  const [question, setQuestion] = useState("")
  const [askingThreadId, setAskingThreadId] = useState<string | null>(null)
  const [desk, setDesk] = useState<ChatDesk>(loadChats)
  const [chatWidth, setChatWidth] = useState(loadChatWidth)
  const activeTabRef = useRef<HTMLDivElement>(null)
  const chatDrag = useRef<{ startX: number; startWidth: number } | null>(null)
  const titling = useRef(new Set<string>())
  const activeThread = desk.threads.find((thread) => thread.id === desk.activeId) ?? desk.threads[0]
  const messages = activeThread?.messages ?? []

  useEffect(() => {
    const params = new URLSearchParams({ limit: String(PAGE), offset: String(offset) })
    for (const filter of filters) {
      if (filter.op !== "empty" && filter.value.trim().length === 0) {
        continue
      }
      params.append("filter", `${filter.column}:${filter.op}:${filter.value.trim()}`)
    }
    let cancelled = false
    api<OrderPage>(`/v1/orders?${params.toString()}`)
      .then((body) => {
        if (!cancelled) {
          setPage(body)
          setLoadError(null)
        }
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setLoadError(caught instanceof ApiError ? caught.message : "Orders could not be loaded.")
        }
      })
    return () => {
      cancelled = true
    }
  }, [filters, offset])

  useEffect(() => {
    saveChats(desk)
  }, [desk])

  useEffect(() => {
    localStorage.setItem(CHAT_WIDTH_KEY, String(chatWidth))
  }, [chatWidth])

  function onResizePointerDown(event: ReactPointerEvent<HTMLDivElement>) {
    if (event.button !== 0) {
      return
    }
    event.preventDefault()
    event.currentTarget.setPointerCapture(event.pointerId)
    chatDrag.current = { startX: event.clientX, startWidth: chatWidth }
  }

  function onResizePointerMove(event: ReactPointerEvent<HTMLDivElement>) {
    const session = chatDrag.current
    if (!session) {
      return
    }
    setChatWidth(clampChatWidth(session.startWidth + (session.startX - event.clientX), window.innerWidth))
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
      setChatWidth((current) => clampChatWidth(current + step, window.innerWidth))
    }
    if (event.key === "ArrowRight") {
      event.preventDefault()
      setChatWidth((current) => clampChatWidth(current - step, window.innerWidth))
    }
  }

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
  }, [desk.threads])

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

  const total = page?.total ?? 0
  const pageCount = Math.max(1, Math.ceil(total / PAGE))
  const pageNumber = Math.floor(offset / PAGE) + 1

  return (
    <div className="flex h-svh overflow-hidden">
      <nav
        aria-label="Desk"
        className="flex h-full w-16 shrink-0 flex-col items-center gap-1 border-e bg-card py-3"
      >
        <div className="mb-3 flex size-10 items-center justify-center text-foreground">
          <RocketIcon className="size-6" aria-hidden />
          <span className="sr-only">Spaceship</span>
        </div>
        <Button variant="ghost" size="icon-lg" asChild>
          <Link to="/dashboard" aria-label="Dashboard" aria-current="page" className="bg-accent text-foreground">
            <LayoutDashboardIcon className="size-5" />
          </Link>
        </Button>
        <div className="mt-auto flex flex-col items-center gap-1">
          <Button variant="ghost" size="icon-lg" type="button" aria-label="Settings">
            <SettingsIcon className="size-5" />
          </Button>
          <Button
            variant="ghost"
            size="icon-lg"
            type="button"
            aria-label="Sign out"
            onClick={() => void signOut()}
          >
            <LogOutIcon className="size-5" />
          </Button>
        </div>
      </nav>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col lg:flex-row">
      <main className="flex min-h-0 min-w-0 flex-1 flex-col gap-8 overflow-y-auto px-6 py-8">
        <header>
          <h1 className="text-[28px]">Spaceship</h1>
        </header>

        {loadError ? <p role="alert">{loadError}</p> : null}

        <section className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-2">
            {filters.map((filter) => (
              <FilterChip
                key={filter.id}
                filter={filter}
                open={openFilterId === filter.id}
                onOpenChange={(next) => setOpenFilterId(next ? filter.id : null)}
                onChange={(next) => {
                  setFilters((current) => current.map((item) => (item.id === next.id ? next : item)))
                  setOffset(0)
                }}
                onRemove={() => {
                  setFilters((current) => current.filter((item) => item.id !== filter.id))
                  setOpenFilterId((current) => (current === filter.id ? null : current))
                  setOffset(0)
                }}
              />
            ))}
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                const id = crypto.randomUUID()
                setFilters((current) => [
                  ...current,
                  { id, column: "order_id", op: "contains", value: "" },
                ])
                setOpenFilterId(id)
              }}
            >
              <FunnelIcon data-icon="inline-start" />
              Filter
            </Button>
          </div>
          {page && page.items.length === 0 ? (
            <Empty>
              <EmptyHeader>
                <EmptyTitle>No orders match these filters.</EmptyTitle>
                <EmptyDescription>Change a filter to see other rows.</EmptyDescription>
              </EmptyHeader>
            </Empty>
          ) : (
            <div className="overflow-x-auto">
              <Table className="text-sm">
                <TableHeader>
                  <TableRow>
                    <TableHead>Order</TableHead>
                    <TableHead>Client</TableHead>
                    <TableHead>Order date</TableHead>
                    <TableHead>Delivery</TableHead>
                    <TableHead>Carrier</TableHead>
                    <TableHead>Warehouse</TableHead>
                    <TableHead>Region</TableHead>
                    <TableHead>Origin</TableHead>
                    <TableHead>Destination</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>SKU</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Qty</TableHead>
                    <TableHead>Unit price</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Promo</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {page?.items.map((order) => (
                    <TableRow key={order.order_id}>
                      <TableCell>{order.order_id}</TableCell>
                      <TableCell>{order.client_id}</TableCell>
                      <TableCell>{order.order_date}</TableCell>
                      <TableCell>{order.delivery_date ?? "—"}</TableCell>
                      <TableCell>{order.carrier}</TableCell>
                      <TableCell>{order.warehouse}</TableCell>
                      <TableCell>{order.region}</TableCell>
                      <TableCell>{order.origin_city}</TableCell>
                      <TableCell>{order.destination_city}</TableCell>
                      <TableCell>
                        <StatusBadge status={order.status} />
                      </TableCell>
                      <TableCell>{order.sku}</TableCell>
                      <TableCell>{order.product_category}</TableCell>
                      <TableCell>{order.quantity}</TableCell>
                      <TableCell>{money(order.unit_price_usd)}</TableCell>
                      <TableCell>{money(order.order_value_usd)}</TableCell>
                      <TableCell>
                        {order.is_promo ? `${order.promo_discount_pct}%` : "No"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
          <div className="flex items-center justify-between gap-3">
            <p className="text-muted-foreground">
              {total} orders · page {pageNumber} of {pageCount}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                disabled={offset === 0}
                onClick={() => setOffset((current) => Math.max(0, current - PAGE))}
              >
                <ChevronLeftIcon data-icon="inline-start" />
                Previous
              </Button>
              <Button
                variant="outline"
                disabled={offset + PAGE >= total}
                onClick={() => setOffset((current) => current + PAGE)}
              >
                Next
                <ChevronRightIcon data-icon="inline-end" />
              </Button>
            </div>
          </div>
        </section>
      </main>

      <aside
        className="relative flex h-72 w-full shrink-0 flex-col border-t bg-card text-base lg:h-full lg:w-(--chat-width) lg:max-w-none lg:border-s lg:border-t-0"
        style={{ "--chat-width": `${chatWidth}px` } as CSSProperties}
      >
        <div
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize chat"
          aria-valuemin={CHAT_MIN}
          aria-valuemax={CHAT_MAX}
          aria-valuenow={Math.round(chatWidth)}
          tabIndex={0}
          className="group absolute inset-y-0 left-0 z-10 hidden w-3 -translate-x-1/2 cursor-col-resize touch-none items-center justify-center lg:flex"
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
          <div
            role="tablist"
            aria-label="Chats"
            className="flex min-w-0 flex-1 items-end overflow-x-auto"
          >
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
          <Button
            type="button"
            variant="ghost"
            size="icon-xs"
            aria-label="New chat"
            className="mb-1 mr-1 shrink-0"
            onClick={openThread}
          >
            <PlusIcon />
          </Button>
        </div>
        <div className="flex min-h-0 flex-1 flex-col">
          <MessageScrollerProvider autoScroll>
            <MessageScroller>
              <MessageScrollerViewport>
                <MessageScrollerContent className="px-4 py-4">
                  {messages.length === 0 ? (
                    <MessageScrollerItem messageId="empty">
                      <p className="text-muted-foreground">One question about this book</p>
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
                              {message.text}
                            </BubbleContent>
                          </Bubble>
                          {message.charts.length > 0 ? <PlotDialog charts={message.charts} /> : null}
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
          className="border-t p-4"
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
      </div>
    </div>
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

function filterSentence(filter: ColumnFilter): string {
  const column = COLUMNS.find((item) => item.id === filter.column)?.label ?? filter.column
  const op = OPS[columnKind(filter.column)].find((item) => item.id === filter.op)?.label ?? filter.op
  if (filter.op === "empty") {
    return `${column} ${op}`
  }
  if (filter.value.trim().length === 0) {
    return `${column} ${op}…`
  }
  const value = filter.column === "status" ? statusLabel(filter.value) : filter.value
  return `${column} ${op} ${value}`
}

function keepPopoverOpen(event: { target: EventTarget | null; preventDefault: () => void }) {
  if (event.target instanceof Element && event.target.closest("[data-slot=select-content]")) {
    event.preventDefault()
  }
}

function FilterChip({
  filter,
  open,
  onOpenChange,
  onChange,
  onRemove,
}: {
  filter: ColumnFilter
  open: boolean
  onOpenChange: (open: boolean) => void
  onChange: (filter: ColumnFilter) => void
  onRemove: () => void
}) {
  const sentence = filterSentence(filter)
  return (
    <Popover open={open} onOpenChange={onOpenChange}>
      <PopoverAnchor asChild>
        <div
          className={cn(
            "inline-flex max-w-full items-center rounded-full border bg-background",
            open ? "border-foreground bg-accent" : "border-foreground bg-card",
          )}
        >
          <PopoverTrigger asChild>
            <button type="button" className="max-w-56 truncate px-3 py-1 text-sm">
              {sentence}
            </button>
          </PopoverTrigger>
          <button
            type="button"
            aria-label={`Remove ${sentence}`}
            className="pe-2 text-foreground"
            onClick={onRemove}
          >
            <XIcon className="size-3" />
          </button>
        </div>
      </PopoverAnchor>
      <PopoverContent
        aria-label="Edit filter"
        onInteractOutside={keepPopoverOpen}
        onFocusOutside={keepPopoverOpen}
      >
        <FilterEditor filter={filter} onChange={onChange} />
      </PopoverContent>
    </Popover>
  )
}

function FilterEditor({
  filter,
  onChange,
}: {
  filter: ColumnFilter
  onChange: (filter: ColumnFilter) => void
}) {
  const kind = columnKind(filter.column)
  const ops = OPS[kind]
  return (
    <FieldGroup className="gap-3">
      <Field>
        <FieldLabel>Column</FieldLabel>
        <Select
          value={filter.column}
          onValueChange={(column) => {
            const nextKind = columnKind(column ?? filter.column)
            onChange({ ...filter, column: column ?? filter.column, op: OPS[nextKind][0].id, value: "" })
          }}
        >
          <SelectTrigger className="w-full" aria-label="Filter column">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              {COLUMNS.map((column) => (
                <SelectItem key={column.id} value={column.id}>
                  {column.label}
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
      </Field>
      <Field>
        <FieldLabel>Operator</FieldLabel>
        <Select value={filter.op} onValueChange={(op) => onChange({ ...filter, op: op ?? filter.op, value: "" })}>
          <SelectTrigger className="w-full" aria-label="Filter operator">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              {ops.map((op) => (
                <SelectItem key={op.id} value={op.id}>
                  {op.label}
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
      </Field>
      {filter.op === "empty" ? null : (
        <Field>
          <FieldLabel>Value</FieldLabel>
          {kind === "status" ? (
            <Select value={filter.value || undefined} onValueChange={(value) => onChange({ ...filter, value: value ?? "" })}>
              <SelectTrigger className="w-full" aria-label="Filter value">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {STATUSES.map((status) => (
                    <SelectItem key={status} value={status}>
                      {statusLabel(status)}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          ) : kind === "bool" ? (
            <Select value={filter.value || undefined} onValueChange={(value) => onChange({ ...filter, value: value ?? "" })}>
              <SelectTrigger className="w-full" aria-label="Filter value">
                <SelectValue placeholder="Yes or no" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectItem value="yes">Yes</SelectItem>
                  <SelectItem value="no">No</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          ) : (
            <Input
              aria-label="Filter value"
              type={kind === "date" ? "date" : "text"}
              inputMode={kind === "number" ? "decimal" : undefined}
              value={filter.value}
              onChange={(event) => onChange({ ...filter, value: event.target.value })}
            />
          )}
        </Field>
      )}
    </FieldGroup>
  )
}
