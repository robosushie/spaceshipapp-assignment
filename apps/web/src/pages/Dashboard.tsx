import { useEffect, useState } from "react"

import { Skeleton } from "@/components/ui/skeleton"
import { ApiError, api } from "@/lib/api"
import { money, statusLabel } from "@/lib/format"
import { cn } from "@/lib/utils"
import type { Metrics } from "@/types/desk"

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
          <Skeleton className="h-28 lg:col-span-3" />
          <Skeleton className="h-28 lg:col-span-3" />
          <Skeleton className="h-28 lg:col-span-3" />
          <Skeleton className="h-28 lg:col-span-3" />
        </div>
      ) : null}
      {metrics ? <Bento metrics={metrics} /> : null}
    </main>
  )
}

function Bento({ metrics }: { metrics: Metrics }) {
  const { totals } = metrics
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-12">
      <Tile
        className="sm:col-span-2 lg:col-span-8"
        label="Orders"
        value={formatCount(totals.orders)}
        detail={money(totals.revenue_usd)}
      />
      <Tile
        className="lg:col-span-4"
        label="December deliveries"
        value={formatCount(metrics.deliveries_last_month)}
        detail="Delivered 1–30 Dec 2025"
      />
      <Tile className="lg:col-span-3" label="Carriers" value={formatCount(metrics.carriers)} />
      <Tile className="lg:col-span-3" label="Warehouses" value={formatCount(metrics.warehouses)} />
      <Tile className="lg:col-span-3" label="Clients" value={formatCount(metrics.clients)} />
      <Tile className="lg:col-span-3" label="Products" value={formatCount(metrics.products)} />
      <Tile className="lg:col-span-4" label="In transit" value={formatCount(totals.in_transit)} />
      <Tile className="lg:col-span-4" label="Delayed" value={formatCount(totals.delayed)} />
      <Tile className="lg:col-span-4" label="Exceptions" value={formatCount(totals.exceptions)} />
      <section className="flex flex-col gap-4 rounded-2xl border bg-card p-5 sm:col-span-2 lg:col-span-8">
        <h2 className="text-muted-foreground">Regions</h2>
        <ul className="flex flex-col gap-2">
          {metrics.by_region.map((region) => (
            <li key={region.region} className="flex items-baseline justify-between gap-4">
              <span>{region.region}</span>
              <span className="text-muted-foreground">
                {formatCount(region.orders)} · {money(region.revenue_usd)}
              </span>
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
              <span className="text-muted-foreground">{formatCount(item.count)}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

function Tile({
  label,
  value,
  detail,
  className,
}: {
  label: string
  value: string
  detail?: string
  className?: string
}) {
  return (
    <article className={cn("flex flex-col justify-between gap-6 rounded-2xl border bg-card p-5", className)}>
      <h2 className="text-muted-foreground">{label}</h2>
      <p className="text-4xl tracking-tight">{value}</p>
      {detail ? <p className="text-sm text-muted-foreground">{detail}</p> : <span className="h-5" />}
    </article>
  )
}

function formatCount(value: number): string {
  return new Intl.NumberFormat("en-US").format(value)
}
