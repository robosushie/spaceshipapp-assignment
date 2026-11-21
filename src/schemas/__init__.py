from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.enums import OrderStatus, UserRole


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=200)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: str
    client_id: str
    order_date: date
    delivery_date: date | None
    carrier: str
    origin_city: str
    destination_city: str
    status: OrderStatus
    sku: str
    product_category: str
    quantity: int
    unit_price_usd: Decimal
    order_value_usd: Decimal
    is_promo: bool
    promo_discount_pct: int
    region: str
    warehouse: str


class OrderPage(BaseModel):
    items: list[OrderRead]
    total: int
    offset: int


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


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class ChatTitleRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)


class ChatTitleResponse(BaseModel):
    title: str


class QuestionChart(BaseModel):
    type: Literal["bar", "line", "area", "pie", "scatter"]
    title: str
    x_key: str
    y_keys: list[str]
    rows: list[dict[str, str]]


class QuestionResponse(BaseModel):
    answer: str
    plot_required: bool
    chart: QuestionChart | None = None


class UserPublic(BaseModel):
    id: int
    email: str
    role: UserRole
