from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from src.enums.orders import OrderStatus


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
