export type Order = {
  order_id: string
  client_id: string
  order_date: string
  delivery_date: string | null
  carrier: string
  origin_city: string
  destination_city: string
  status: string
  sku: string
  product_category: string
  quantity: number
  unit_price_usd: string
  order_value_usd: string
  is_promo: boolean
  promo_discount_pct: number
  region: string
  warehouse: string
}

export type OrderPage = {
  items: Order[]
  total: number
  offset: number
}

export type Metrics = {
  totals: {
    orders: number
    revenue_usd: string
    delayed: number
    exceptions: number
    in_transit: number
  }
  carriers: number
  warehouses: number
  clients: number
  products: number
  deliveries_last_month: number
  by_status: { status: string; count: number }[]
  by_region: { region: string; orders: number; revenue_usd: string }[]
  by_carrier: { carrier: string; orders: number; delayed: number; exceptions: number }[]
}

export type QuestionChart = {
  type: "bar" | "line" | "area" | "pie" | "scatter"
  title: string
  x_key: string
  y_keys: string[]
  rows: Record<string, string>[]
}

export type QuestionResult = {
  answer: string
  plot_required: boolean
  chart: QuestionChart | null
}
