import { useEffect, useState } from "react"
import { LayoutDashboardIcon, LogOutIcon, RocketIcon, SendIcon, SettingsIcon } from "lucide-react"
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
import { Field, FieldLabel } from "@/components/ui/field"
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
import { money, statusLabel } from "@/lib/format"
import { cn } from "@/lib/utils"
import type { Metrics, OrderPage, QuestionChart, QuestionResult } from "@/types/desk"

const PAGE = 40
const STATUSES = ["delivered", "delayed", "in_transit", "exception", "canceled"]
const REGIONS = ["UK", "EU", "US-E", "US-C", "US-W"]
const CARRIERS = ["DHL", "DPD", "FedEx", "GLS", "LaserShip", "OnTrac", "Royal Mail", "UPS", "USPS"]

type ChatMessage = {
  id: string
  role: "user" | "assistant"
  text: string
  charts: QuestionChart[]
}

function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "delivered"
      ? "bg-arrived text-primary-foreground"
      : status === "delayed"
        ? "bg-delayed-wash text-foreground"
        : status === "exception"
          ? "bg-delay text-foreground"
        : "bg-secondary text-foreground"
  return <Badge className={tone}>{statusLabel(status)}</Badge>
}

const PIE_FILLS = [
  "var(--foreground)",
  "var(--arrived)",
  "var(--delay)",
  "var(--delayed-wash)",
  "var(--muted-foreground)",
  "var(--secondary)",
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
          className="group relative h-auto w-full rounded-[1rem] p-2"
          onClick={() => {
            setTab(`plot-${index}`)
            setOpen(true)
          }}
        >
          <span className="sr-only">Open {chart.title}</span>
          <Plot chart={chart} className="pointer-events-none h-24 blur-sm" />
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
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [page, setPage] = useState<OrderPage | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [status, setStatus] = useState("all")
  const [region, setRegion] = useState("all")
  const [carrier, setCarrier] = useState("all")
  const [offset, setOffset] = useState(0)
  const [question, setQuestion] = useState("")
  const [asking, setAsking] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])

  useEffect(() => {
    const params = new URLSearchParams({ limit: String(PAGE), offset: String(offset) })
    if (status !== "all") {
      params.set("status", status)
    }
    if (region !== "all") {
      params.set("region", region)
    }
    if (carrier !== "all") {
      params.set("carrier", carrier)
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
  }, [status, region, carrier, offset])

  useEffect(() => {
    let cancelled = false
    api<Metrics>("/v1/metrics")
      .then((body) => {
        if (!cancelled) {
          setMetrics(body)
        }
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setLoadError(caught instanceof ApiError ? caught.message : "Metrics could not be loaded.")
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function onAsk() {
    const asked = question.trim()
    if (asked.length === 0) {
      return
    }
    const userId = crypto.randomUUID()
    setMessages((current) => [
      ...current,
      { id: userId, role: "user", text: asked, charts: [] },
    ])
    setQuestion("")
    setAsking(true)
    try {
      const result = await api<QuestionResult>("/v1/questions", {
        method: "POST",
        body: JSON.stringify({ question: asked }),
      })
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: result.answer,
          charts: result.plot_required && result.chart ? [result.chart] : [],
        },
      ])
    } catch (caught) {
      const unavailable = caught instanceof ApiError && caught.status === 503
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: unavailable
            ? "Questions are unavailable until an Anthropic key is configured."
            : caught instanceof ApiError
              ? caught.message
              : "The question could not be answered.",
          charts: [],
        },
      ])
    } finally {
      setAsking(false)
    }
  }

  const total = page?.total ?? 0
  const pageCount = Math.max(1, Math.ceil(total / PAGE))
  const pageNumber = Math.floor(offset / PAGE) + 1

  return (
    <div className="flex h-svh overflow-hidden">
      <nav
        aria-label="Desk"
        className="flex h-full w-14 shrink-0 flex-col items-center gap-1 border-e bg-card py-3"
      >
        <div className="mb-3 flex size-9 items-center justify-center text-foreground">
          <RocketIcon className="size-5" aria-hidden />
          <span className="sr-only">Spaceship</span>
        </div>
        <Button variant="secondary" size="icon" asChild>
          <Link to="/dashboard" aria-label="Dashboard" aria-current="page">
            <LayoutDashboardIcon />
          </Link>
        </Button>
        <div className="mt-auto flex flex-col items-center gap-1">
          <Button variant="ghost" size="icon" type="button" aria-label="Settings">
            <SettingsIcon />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            type="button"
            aria-label="Sign out"
            onClick={() => void signOut()}
          >
            <LogOutIcon />
          </Button>
        </div>
      </nav>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col lg:flex-row">
      <main className="flex min-h-0 min-w-0 flex-1 flex-col gap-8 overflow-y-auto px-6 py-8">
        <header className="flex flex-col gap-1">
          <h1 className="text-3xl font-bold">Spaceship</h1>
          <p>The 2025 shipping book</p>
          <p className="text-muted-foreground">1 Jan 2025 – 30 Dec 2025</p>
        </header>

        {loadError ? <p role="alert">{loadError}</p> : null}

        <section className="flex flex-wrap gap-6">
          {(metrics?.by_status ?? STATUSES.map((item) => ({ status: item, count: 0 }))).map(
            (row) => (
              <div key={row.status} className="flex flex-col">
                <span className="text-muted-foreground">{statusLabel(row.status)}</span>
                <span className="text-2xl font-bold tabular-nums">{metrics ? row.count : "–"}</span>
              </div>
            ),
          )}
        </section>

        <section className="flex flex-col gap-4">
          <div className="flex flex-wrap gap-3">
            <FilterSelect
              label="Status"
              value={status}
              options={STATUSES}
              onChange={(value) => {
                setStatus(value)
                setOffset(0)
              }}
            />
            <FilterSelect
              label="Region"
              value={region}
              options={REGIONS}
              onChange={(value) => {
                setRegion(value)
                setOffset(0)
              }}
            />
            <FilterSelect
              label="Carrier"
              value={carrier}
              options={CARRIERS}
              onChange={(value) => {
                setCarrier(value)
                setOffset(0)
              }}
            />
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
              <Table>
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
                Previous
              </Button>
              <Button
                variant="outline"
                disabled={offset + PAGE >= total}
                onClick={() => setOffset((current) => current + PAGE)}
              >
                Next
              </Button>
            </div>
          </div>
        </section>
      </main>

      <aside className="flex h-72 w-full shrink-0 flex-col border-t bg-card lg:h-full lg:w-80 lg:border-s lg:border-t-0">
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
                            <BubbleContent className="rounded-[1.25rem] px-4 py-2.5">
                              {message.text}
                            </BubbleContent>
                          </Bubble>
                          {message.charts.length > 0 ? <PlotDialog charts={message.charts} /> : null}
                        </MessageContent>
                      </Message>
                    </MessageScrollerItem>
                  ))}
                  {asking ? (
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
              className="block min-h-24 w-full resize-none rounded-[12px] border border-input bg-transparent px-3 py-2.5 pr-12 pb-10 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            />
            <Button
              type="submit"
              variant="ghost"
              size="icon"
              aria-label="Send"
              disabled={asking || question.trim().length === 0}
              className="absolute right-2 bottom-2 bg-transparent hover:bg-transparent"
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

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: string[]
  onChange: (value: string) => void
}) {
  return (
    <Field className="w-40">
      <FieldLabel>{label}</FieldLabel>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectItem value="all">Any</SelectItem>
            {options.map((option) => (
              <SelectItem key={option} value={option}>
                {label === "Status" ? statusLabel(option) : option}
              </SelectItem>
            ))}
          </SelectGroup>
        </SelectContent>
      </Select>
    </Field>
  )
}
