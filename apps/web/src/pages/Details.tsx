import { useEffect, useState } from "react"
import { ChevronLeftIcon, ChevronRightIcon, FunnelIcon, XIcon } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Popover, PopoverAnchor, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { ApiError, api } from "@/lib/api"
import { money, statusLabel } from "@/lib/format"
import { cn } from "@/lib/utils"
import type { OrderPage } from "@/types/desk"

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
const STATUSES = ["delivered", "delayed", "in_transit", "exception", "canceled"]

function columnKind(id: string): FilterKind {
  return COLUMNS.find((column) => column.id === id)?.kind ?? "text"
}

export function Details() {
  const [page, setPage] = useState<OrderPage | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [filters, setFilters] = useState<ColumnFilter[]>([])
  const [openFilterId, setOpenFilterId] = useState<string | null>(null)
  const [offset, setOffset] = useState(0)

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

  const total = page?.total ?? 0
  const pageCount = Math.max(1, Math.ceil(total / PAGE))
  const pageNumber = Math.floor(offset / PAGE) + 1

  return (
    <main className="flex h-full min-w-0 flex-col gap-6 overflow-y-auto px-4 py-6 sm:px-6 sm:py-8">
      <header>
        <h1 className="text-[28px] leading-[1.14] tracking-[-0.022em]">Details</h1>
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
                    <TableCell>{order.is_promo ? `${order.promo_discount_pct}%` : "No"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
        <div className="flex flex-wrap items-center justify-between gap-3">
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
  )
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
            onChange({
              ...filter,
              column: column ?? filter.column,
              op: OPS[nextKind][0].id,
              value: "",
            })
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
        <Select
          value={filter.op}
          onValueChange={(op) => onChange({ ...filter, op: op ?? filter.op, value: "" })}
        >
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
            <Select
              value={filter.value || undefined}
              onValueChange={(value) => onChange({ ...filter, value: value ?? "" })}
            >
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
            <Select
              value={filter.value || undefined}
              onValueChange={(value) => onChange({ ...filter, value: value ?? "" })}
            >
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
