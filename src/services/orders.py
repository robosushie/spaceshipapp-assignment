from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlmodel import Session, col, func, select

from src.enums import OrderStatus
from src.models import Order, Product, Warehouse
from src.schemas import OrderPage, OrderRead

_TEXT: dict[str, Any] = {
    "order_id": Order.order_id,
    "client_id": Order.client_id,
    "carrier": Order.carrier_name,
    "warehouse": Warehouse.code,
    "region": Warehouse.region,
    "origin_city": Warehouse.origin_city,
    "destination_city": Order.destination_city,
    "sku": Order.sku,
    "category": Product.category,
}
_DATES: dict[str, Any] = {
    "order_date": Order.order_date,
    "delivery_date": Order.delivery_date,
}
_NUMBERS: dict[str, Any] = {
    "quantity": Order.quantity,
    "unit_price_usd": Order.unit_price_usd,
    "order_value_usd": Order.order_value_usd,
}
_OPS = {
    "text": {"contains", "equals"},
    "date": {"on", "before", "after", "empty"},
    "number": {"equals", "gt", "lt"},
    "status": {"is"},
    "bool": {"is"},
}


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


class OrderFilterError(ValueError):
    pass


def parse_filters(raw: list[str]) -> list[tuple[str, str, str]]:
    if len(raw) > 8:
        raise OrderFilterError("Use at most 8 filters.")
    parsed: list[tuple[str, str, str]] = []
    for item in raw:
        parts = item.split(":", 2)
        if len(parts) < 2 or not parts[0] or not parts[1]:
            raise OrderFilterError("A filter needs a column and an operator.")
        field, op = parts[0], parts[1]
        value = parts[2] if len(parts) == 3 else ""
        kind = _kind(field)
        if kind is None or op not in _OPS[kind]:
            raise OrderFilterError("That column or operator is not a filter.")
        if op != "empty" and not value.strip():
            raise OrderFilterError("That filter needs a value.")
        if len(value) > 128:
            raise OrderFilterError("A filter value is too long.")
        parsed.append((field, op, value.strip()))
    return parsed


def _kind(field: str) -> str | None:
    if field in _TEXT:
        return "text"
    if field in _DATES:
        return "date"
    if field in _NUMBERS:
        return "number"
    if field == "status":
        return "status"
    if field == "promo":
        return "bool"
    return None


def _clause(field: str, op: str, value: str) -> Any:
    if field in _TEXT:
        column = _TEXT[field]
        pattern = _like(value, contains=op == "contains")
        return column.ilike(pattern, escape="\\")
    if field in _DATES:
        column = _DATES[field]
        if op == "empty":
            return column.is_(None)
        try:
            day = date.fromisoformat(value)
        except ValueError as exc:
            raise OrderFilterError("A date filter uses YYYY-MM-DD.") from exc
        if op == "before":
            return column < day
        if op == "after":
            return column > day
        return column == day
    if field in _NUMBERS:
        column = _NUMBERS[field]
        try:
            number = int(value) if field == "quantity" else Decimal(value)
        except (InvalidOperation, ValueError) as exc:
            raise OrderFilterError("That filter needs a number.") from exc
        if op == "gt":
            return column > number
        if op == "lt":
            return column < number
        return column == number
    if field == "status":
        try:
            status = OrderStatus(value)
        except ValueError as exc:
            raise OrderFilterError("That status is not in the book.") from exc
        return Order.status == status
    flag = value.lower() in {"yes", "true", "1"}
    if value.lower() not in {"yes", "no", "true", "false", "1", "0"}:
        raise OrderFilterError("Promo is yes or no.")
    return Order.is_promo == flag


def _like(value: str, *, contains: bool) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%" if contains else escaped


def _filtered(
    status: OrderStatus | None,
    region: str | None,
    carrier: str | None,
    client_id: str | None,
    filters: list[tuple[str, str, str]] | None = None,
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
    for field, op, value in filters or []:
        statement = statement.where(_clause(field, op, value))
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
    filters: list[tuple[str, str, str]] | None = None,
) -> OrderPage:
    filtered = _filtered(status, region, carrier, client_id, filters)
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
