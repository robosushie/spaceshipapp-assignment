from decimal import Decimal

from pydantic import BaseModel

from src.enums.orders import OrderStatus


class StatusCount(BaseModel):
    status: OrderStatus
    count: int


class RegionMetric(BaseModel):
    region: str
    orders: int
    revenue_usd: Decimal


class CarrierMetric(BaseModel):
    carrier: str
    orders: int
    delayed: int
    exceptions: int


class MetricTotals(BaseModel):
    orders: int
    revenue_usd: Decimal
    delivered: int
    delayed: int
    exceptions: int
    in_transit: int
    on_time_rate: Decimal
    average_delivery_days: Decimal


class MonthVolume(BaseModel):
    month: str
    orders: int


class MetricsResponse(BaseModel):
    totals: MetricTotals
    carriers: int
    warehouses: int
    clients: int
    products: int
    deliveries_last_month: int
    by_status: list[StatusCount]
    by_region: list[RegionMetric]
    by_carrier: list[CarrierMetric]
    by_month: list[MonthVolume]
