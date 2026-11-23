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
    delayed: int
    exceptions: int
    in_transit: int


class MetricsResponse(BaseModel):
    totals: MetricTotals
    by_status: list[StatusCount]
    by_region: list[RegionMetric]
    by_carrier: list[CarrierMetric]
