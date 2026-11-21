from decimal import Decimal
from typing import Any

from sqlmodel import Session, col, func, select

from src.enums import OrderStatus
from src.models import Order, Product, Warehouse
from src.schemas import OrderPage, OrderRead


def _to_read(order: Order, warehouse: Warehouse, product: Product) -> OrderRead:
    return OrderRead(
        order_id=order.order_id,
        client_id=order.client_id,
        order_date=order.order_date,
        delivery_date=order.delivery_date,
        carrier=order.carrier_name,
        origin_city=warehouse.origin_city,
        destination_city=order.destination_city,
        status=order.status,
        sku=order.sku,
        product_category=product.category,
        quantity=order.quantity,
        unit_price_usd=Decimal(order.unit_price_usd),
        order_value_usd=Decimal(order.order_value_usd),
        is_promo=order.is_promo,
        promo_discount_pct=order.promo_discount_pct,
        region=warehouse.region,
        warehouse=warehouse.code,
    )


def _filtered(
    status: OrderStatus | None,
    region: str | None,
    carrier: str | None,
    client_id: str | None,
) -> Any:
    statement = (
        select(Order, Warehouse, Product)
        .join(Warehouse, col(Order.warehouse_code) == col(Warehouse.code))
        .join(Product, col(Order.sku) == col(Product.sku))
    )
    if status is not None:
        statement = statement.where(Order.status == status)
    if region is not None:
        statement = statement.where(Warehouse.region == region)
    if carrier is not None:
        statement = statement.where(Order.carrier_name == carrier)
    if client_id is not None:
        statement = statement.where(Order.client_id == client_id)
    return statement


def list_orders(
    session: Session,
    *,
    status: OrderStatus | None,
    region: str | None,
    carrier: str | None,
    client_id: str | None,
    limit: int,
    offset: int,
) -> OrderPage:
    filtered = _filtered(status, region, carrier, client_id)
    total = session.exec(select(func.count()).select_from(filtered.subquery())).one()
    rows = session.exec(
        filtered.order_by(col(Order.order_date).desc(), col(Order.order_id).desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return OrderPage(
        items=[_to_read(order, warehouse, product) for order, warehouse, product in rows],
        total=int(total),
        offset=offset,
    )


def get_order(session: Session, order_id: str) -> OrderRead | None:
    row = session.exec(_filtered(None, None, None, None).where(Order.order_id == order_id)).first()
    if row is None:
        return None
    order, warehouse, product = row
    return _to_read(order, warehouse, product)
