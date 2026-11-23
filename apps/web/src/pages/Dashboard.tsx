import { useEffect, useState, type ReactNode } from "react"
import { motion, useReducedMotion } from "motion/react"
import { Bar, BarChart, Line, LineChart, XAxis, YAxis } from "recharts"

import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Skeleton } from "@/components/ui/skeleton"
import { ApiError, api } from "@/lib/api"
import { money, statusLabel } from "@/lib/format"
import { cn } from "@/lib/utils"
import type { Metrics } from "@/types/desk"

const CATALOG = [
  { key: "carriers", label: "Carriers" },
  { key: "warehouses", label: "Warehouses" },
  { key: "clients", label: "Clients" },
  { key: "products", label: "Products" },
] as const

export function Dashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    api<Metrics>("/v1/metrics")
      .then((body) => {
        if (!cancelled) {
          setMetrics(body)
          setError(null)
        }
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : "The summary could not be loaded.")
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <main className="h-full overflow-y-auto px-4 py-6 sm:px-6 sm:py-8">
      <header className="mb-6">
        <h1 className="text-[28px] leading-[1.14] tracking-[-0.022em]">Spaceship</h1>
      </header>
      {error ? <p role="alert">{error}</p> : null}
      {metrics === null && error === null ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-12">
          <Skeleton className="h-40 sm:col-span-2 lg:col-span-8" />
          <Skeleton className="h-40 lg:col-span-4" />
          <Skeleton className="h-24 sm:col-span-2 lg:col-span-12" />
          <Skeleton className="h-28 lg:col-span-4" />
          <Skeleton className="h-28 lg:col-span-4" />
          <Skeleton className="h-28 lg:col-span-4" />
        </div>
      ) : null}
      {metrics ? <Bento metrics={metrics} /> : null}
    </main>
  )
}

function Bento({ metrics }: { metrics: Metrics }) {
  const reduce = useReducedMotion() === true
  const { totals } = metrics

  return (
    <motion.div
      className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-12"
      initial={reduce ? false : { opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: reduce ? 0 : 0.4, ease: "easeOut" }}
    >
      <CountCell
        className="sm:col-span-2 lg:col-span-8"
        label="Orders"
        value={formatCount(totals.orders)}
        detail={money(totals.revenue_usd)}
        tone="paper"
      />
      <CountCell
        className="lg:col-span-4"
        label="December deliveries"
        value={formatCount(metrics.deliveries_last_month)}
        detail="Delivered 1–30 Dec 2025"
        tone="wine"
      />
      <section className="grid grid-cols-2 divide-x divide-y divide-border rounded-2xl border bg-card sm:col-span-2 sm:grid-cols-4 sm:divide-y-0 lg:col-span-12">
        {CATALOG.map((item) => (
          <div key={item.key} className="flex flex-col gap-2 p-5">
            <h2 className="text-muted-foreground">{item.label}</h2>
            <p className="text-4xl tracking-tight tabular-nums">{formatCount(metrics[item.key])}</p>
          </div>
        ))}
      </section>
      <CountCell className="lg:col-span-4" label="Delivered" value={formatCount(totals.delivered)} tone="paper" />
      <CountCell
        className="lg:col-span-4"
        label="On-time rate"
        value={formatRate(totals.on_time_rate)}
        detail="Delivered of delivered and delayed"
        tone="wine"
      />
      <CountCell
        className="lg:col-span-4"
        label="Average delivery"
        value={formatDays(totals.average_delivery_days)}
        detail="Order date to delivery date"
        tone="paper"
      />
      <CountCell className="lg:col-span-4" label="In transit" value={formatCount(totals.in_transit)} tone="paper" />
      <CountCell className="lg:col-span-4" label="Delayed" value={formatCount(totals.delayed)} tone="lilac" />
      <CountCell className="lg:col-span-4" label="Exceptions" value={formatCount(totals.exceptions)} tone="lilac" />
      <DashboardCharts metrics={metrics} />
      <section className="flex flex-col gap-4 rounded-2xl border bg-card p-5 sm:col-span-2 lg:col-span-8">
        <h2 className="text-muted-foreground">Regions</h2>
        <ul className="flex flex-col gap-4">
          {metrics.by_region.map((region) => (
            <li key={region.region} className="flex flex-col gap-2">
              <div className="flex items-baseline justify-between gap-4">
                <span>{region.region}</span>
                <span className="text-muted-foreground tabular-nums">
                  {formatCount(region.orders)} · {money(region.revenue_usd)}
                </span>
              </div>
              <div className="h-px w-full bg-border">
                <motion.div
                  className="h-px origin-left bg-foreground"
                  style={{ width: `${share(region.orders, totals.orders)}%` }}
                  initial={reduce ? false : { scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ duration: reduce ? 0 : 0.4, ease: "easeOut" }}
                />
              </div>
            </li>
          ))}
        </ul>
      </section>
      <section className="flex flex-col gap-4 rounded-2xl border bg-card p-5 lg:col-span-4">
        <h2 className="text-muted-foreground">Status</h2>
        <ul className="flex flex-col gap-2">
          {metrics.by_status.map((item) => (
            <li key={item.status} className="flex items-baseline justify-between gap-4">
              <span>{statusLabel(item.status)}</span>
              <span className="text-muted-foreground tabular-nums">{formatCount(item.count)}</span>
            </li>
          ))}
        </ul>
      </section>
    </motion.div>
  )
}

function CountCell({
  label,
  value,
  detail,
  tone,
  className,
}: {
  label: string
  value: string
  detail?: string
  tone: "paper" | "wine" | "lilac"
  className?: string
}) {
  const surface = {
    paper: "border bg-card text-card-foreground",
    wine: "bg-primary text-primary-foreground",
    lilac: "bg-secondary text-secondary-foreground",
  }[tone]
  const quiet = tone === "wine" ? "text-primary-foreground/75" : "text-muted-foreground"

  return (
    <article className={cn("flex flex-col justify-between gap-6 rounded-2xl p-5", surface, className)}>
      <h2 className={quiet}>{label}</h2>
      <p className="text-4xl tracking-tight tabular-nums">{value}</p>
      {detail ? <p className={cn("text-sm", quiet)}>{detail}</p> : <span className="h-5" />}
    </article>
  )
}

function DashboardCharts({ metrics }: { metrics: Metrics }) {
  const punctuality = [
    { name: "Delivered", orders: metrics.totals.delivered },
    { name: "Delayed", orders: metrics.totals.delayed },
  ]
  return (
    <>
      <ChartCard title="Orders by month" className="sm:col-span-2 lg:col-span-12">
        <ChartContainer config={{ orders: { label: "Orders", color: "var(--chart-1)" } }} className="aspect-auto h-56 w-full">
          <LineChart data={metrics.by_month}>
            <XAxis dataKey="month" interval={metrics.by_month.length > 8 ? "preserveStartEnd" : 0} />
            <YAxis domain={[0, "auto"]} width={32} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Line dataKey="orders" stroke="var(--chart-1)" strokeWidth={2} dot={false} />
          </LineChart>
        </ChartContainer>
      </ChartCard>
      <ChartCard title="Delivered and delayed" className="lg:col-span-6">
        <ChartContainer config={{ orders: { label: "Orders", color: "var(--chart-2)" } }} className="aspect-auto h-56 w-full">
          <BarChart data={punctuality}>
            <XAxis dataKey="name" />
            <YAxis domain={[0, "auto"]} width={32} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Bar dataKey="orders" fill="var(--chart-2)" />
          </BarChart>
        </ChartContainer>
      </ChartCard>
      <ChartCard title="Orders by carrier" className="lg:col-span-6">
        <ChartContainer config={{ orders: { label: "Orders", color: "var(--chart-1)" } }} className="aspect-auto h-56 w-full">
          <BarChart data={metrics.by_carrier}>
            <XAxis dataKey="carrier" interval={metrics.by_carrier.length > 6 ? "preserveStartEnd" : 0} />
            <YAxis domain={[0, "auto"]} width={32} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Bar dataKey="orders" fill="var(--chart-1)" />
          </BarChart>
        </ChartContainer>
      </ChartCard>
    </>
  )
}

function ChartCard({
  title,
  className,
  children,
}: {
  title: string
  className?: string
  children: ReactNode
}) {
  return (
    <section className={cn("flex flex-col gap-4 rounded-2xl border bg-card p-5", className)}>
      <h2 className="text-muted-foreground">{title}</h2>
      {children}
    </section>
  )
}

function share(part: number, whole: number): number {
  if (whole <= 0) {
    return 0
  }
  return (part / whole) * 100
}

function formatCount(value: number): string {
  return new Intl.NumberFormat("en-US").format(value)
}

function formatRate(value: string): string {
  const rate = Number(value)
  if (!Number.isFinite(rate)) {
    return "—"
  }
  return new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 1 }).format(rate)
}

function formatDays(value: string): string {
  const days = Number(value)
  if (!Number.isFinite(days)) {
    return "—"
  }
  return `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(days)} days`
}
