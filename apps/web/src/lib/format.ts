export function statusLabel(status: string): string {
  if (status === "in_transit") {
    return "in transit"
  }
  return status
}

export function money(value: string): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(Number(value))
}

export function statusColor(status: string): string {
  if (status === "delivered") {
    return "var(--arrived)"
  }
  if (status === "delayed" || status === "exception") {
    return "var(--delay)"
  }
  if (status === "canceled") {
    return "var(--muted-foreground)"
  }
  return "var(--foreground)"
}
