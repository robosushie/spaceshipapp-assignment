from datetime import date
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import Date, case
from sqlalchemy import cast as sa_cast
from sqlmodel import Session, col, func, select

from src.enums.orders import OrderStatus
from src.models.catalog.carrier import Carrier
from src.models.catalog.client import Client
from src.models.catalog.product import Product
from src.models.catalog.warehouse import Warehouse
from src.models.orders.order import Order
from src.schemas.orders.metrics import (
    CarrierMetric,
    MetricsResponse,
    MetricTotals,
    MonthVolume,
    RegionMetric,
    StatusCount,
)

_REGIONS = ("UK", "EU", "US-E", "US-C", "US-W")
_LAST_MONTH_START = date(2025, 12, 1)
_LAST_MONTH_END = date(2025, 12, 30)


def _days(value: object) -> Decimal:
    if value is None:
        return Decimal("0.0")
    return Decimal(str(value)).quantize(Decimal("0.1"))


def _money(value: object) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(Decimal("0.01"))


def get_metrics(session: Session) -> MetricsResponse:
    status_rows = session.exec(select(Order.status, func.count()).group_by(Order.status)).all()
    status_counts = {status: int(count) for status, count in status_rows}
    by_status = [
        StatusCount(status=status, count=status_counts.get(status, 0)) for status in OrderStatus
    ]

    region_rows = session.exec(
        select(
            Warehouse.region,
            func.count(),
            func.coalesce(func.sum(Order.order_value_usd), 0),
        )
        .join(Warehouse, col(Order.warehouse_code) == col(Warehouse.code))
        .group_by(Warehouse.region)
    ).all()
    region_map = {region: (int(count), _money(revenue)) for region, count, revenue in region_rows}
    by_region = [
        RegionMetric(
            region=region,
            orders=region_map.get(region, (0, Decimal("0.00")))[0],
            revenue_usd=region_map.get(region, (0, Decimal("0.00")))[1],
        )
        for region in _REGIONS
        if region in region_map
    ]

    delayed_match = cast(Any, Order.status == OrderStatus.delayed)
    exception_match = cast(Any, Order.status == OrderStatus.exception)
    delayed = case((delayed_match, 1), else_=0)
    exception = case((exception_match, 1), else_=0)
    carrier_rows = session.exec(
        select(
            Order.carrier_name,
            func.count(),
            func.coalesce(func.sum(delayed), 0),
            func.coalesce(func.sum(exception), 0),
        ).group_by(Order.carrier_name)
    ).all()
    by_carrier = sorted(
        (
            CarrierMetric(
                carrier=name,
                orders=int(orders),
                delayed=int(delayed),
                exceptions=int(exceptions),
            )
            for name, orders, delayed, exceptions in carrier_rows
        ),
        key=lambda item: item.carrier,
    )

    revenue = session.exec(select(func.coalesce(func.sum(Order.order_value_usd), 0))).one()
    order_count = session.exec(select(func.count()).select_from(Order)).one()
    delivered = status_counts.get(OrderStatus.delivered, 0)
    delayed_count = status_counts.get(OrderStatus.delayed, 0)
    rated = delivered + delayed_count
    on_time_rate = (Decimal(delivered) / Decimal(rated) if rated else Decimal("0")).quantize(
        Decimal("0.0001")
    )
    average_days = session.exec(
        select(func.avg(sa_cast(Order.delivery_date, Date) - Order.order_date)).where(
            col(Order.delivery_date).is_not(None)
        )
    ).one()
    month = func.to_char(Order.order_date, "YYYY-MM")
    month_rows = session.exec(select(month, func.count()).group_by(month).order_by(month)).all()
    deliveries_last_month = session.exec(
        select(func.count())
        .select_from(Order)
        .where(
            Order.status == OrderStatus.delivered,
            col(Order.delivery_date) >= _LAST_MONTH_START,
            col(Order.delivery_date) <= _LAST_MONTH_END,
        )
    ).one()
    totals = MetricTotals(
        orders=int(order_count),
        revenue_usd=_money(revenue),
        delivered=delivered,
        delayed=delayed_count,
        exceptions=status_counts.get(OrderStatus.exception, 0),
        in_transit=status_counts.get(OrderStatus.in_transit, 0),
        on_time_rate=on_time_rate,
        average_delivery_days=_days(average_days),
    )
    return MetricsResponse(
        totals=totals,
        carriers=_count(session, Carrier),
        warehouses=_count(session, Warehouse),
        clients=_count(session, Client),
        products=_count(session, Product),
        deliveries_last_month=int(deliveries_last_month),
        by_status=by_status,
        by_region=by_region,
        by_carrier=by_carrier,
        by_month=[MonthVolume(month=str(label), orders=int(count)) for label, count in month_rows],
    )


def _count(
    session: Session,
    model: type[Carrier] | type[Warehouse] | type[Client] | type[Product],
) -> int:
    return int(session.exec(select(func.count()).select_from(model)).one())
