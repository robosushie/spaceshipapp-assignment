from datetime import date
from decimal import Decimal

from sqlmodel import Session

from src.enums import OrderStatus, UserRole
from src.lib.db import engine
from src.lib.security import hash_password
from src.models import Carrier, Client, Order, Product, User, Warehouse


def add_user(email: str = "analyst@spaceship.local", password: str = "correct-password") -> None:
    with Session(engine) as session:
        session.add(
            User(
                email=email,
                password_hash=hash_password(password),
                role=UserRole.analyst,
            )
        )
        session.commit()


def add_order(order_id: str = "ORD-1", order_date: date = date(2025, 10, 19)) -> None:
    with Session(engine) as session:
        if session.get(Client, "CL-1001") is None:
            session.add(Client(client_id="CL-1001"))
        if session.get(Warehouse, "LON-FC1") is None:
            session.add(Warehouse(code="LON-FC1", region="UK", origin_city="London, UK"))
        if session.get(Carrier, "DHL") is None:
            session.add(Carrier(name="DHL"))
        if session.get(Product, "PAPER-1") is None:
            session.add(Product(sku="PAPER-1", category="PAPER"))
        session.flush()
        session.add(
            Order(
                order_id=order_id,
                client_id="CL-1001",
                warehouse_code="LON-FC1",
                carrier_name="DHL",
                sku="PAPER-1",
                destination_city="Leeds, UK",
                status=OrderStatus.delivered,
                order_date=order_date,
                delivery_date=order_date,
                quantity=2,
                unit_price_usd=Decimal("13.11"),
                order_value_usd=Decimal("26.22"),
                is_promo=False,
                promo_discount_pct=0,
            )
        )
        session.commit()
