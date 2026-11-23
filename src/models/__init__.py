from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from src.enums import OrderStatus, UserRole


def _enum_values(enum_cls: type[OrderStatus] | type[UserRole]) -> list[str]:
    return [member.value for member in enum_cls]


class Client(SQLModel, table=True):
    __tablename__ = "clients"

    client_id: str = Field(primary_key=True, max_length=32)


class Warehouse(SQLModel, table=True):
    __tablename__ = "warehouses"

    code: str = Field(primary_key=True, max_length=32)
    region: str = Field(max_length=16, index=True)
    origin_city: str = Field(max_length=128)


class Carrier(SQLModel, table=True):
    __tablename__ = "carriers"

    name: str = Field(primary_key=True, max_length=64)


class Product(SQLModel, table=True):
    __tablename__ = "products"

    sku: str = Field(primary_key=True, max_length=64)
    category: str = Field(max_length=32, index=True)


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
                values_callable=_enum_values,
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


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(sa_column=Column(String(320), unique=True, nullable=False))
    name: str = Field(default="", max_length=120)
    title: str = Field(default="", max_length=120)
    department: str = Field(default="", max_length=120)
    password_hash: str
    role: UserRole = Field(
        sa_column=Column(
            SAEnum(UserRole, name="user_role", values_callable=_enum_values),
            nullable=False,
        )
    )
    invite_token_hash: str | None = Field(default=None, max_length=64, unique=True)
    invite_expires_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    password_reset_token_hash: str | None = Field(default=None, max_length=64, unique=True)
    password_reset_expires_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(sa_column=Column(String(64), unique=True, nullable=False))
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    revoked_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
