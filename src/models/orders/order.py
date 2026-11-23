from datetime import date
from decimal import Decimal

from sqlalchemy import Column, Numeric
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from src.enums.orders import OrderStatus
from src.models.columns import enum_values


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    order_id: str = Field(primary_key=True, max_length=64)
    client_id: str = Field(foreign_key="clients.client_id", index=True, max_length=32)
    warehouse_code: str = Field(foreign_key="warehouses.code", index=True, max_length=32)
    carrier_name: str = Field(foreign_key="carriers.name", index=True, max_length=64)
    sku: str = Field(foreign_key="products.sku", index=True, max_length=64)
    destination_city: str = Field(max_length=128)
    status: OrderStatus = Field(
        sa_column=Column(
            SAEnum(
                OrderStatus,
                name="order_status",
                values_callable=enum_values,
            ),
            nullable=False,
            index=True,
        )
    )
    order_date: date = Field(index=True)
    delivery_date: date | None = None
    quantity: int
    unit_price_usd: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    order_value_usd: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    is_promo: bool
    promo_discount_pct: int
