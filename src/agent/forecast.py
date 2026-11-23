"""Project demand from the book. The model never supplies these numbers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func
from sqlmodel import Session, col, select

from src.agent.forecasting import LABELS, choose, complete_months, future_months
from src.models.orders.order import Order

BOOK_END = date(2025, 12, 30)


@dataclass(frozen=True)
class DemandForecast:
    method: str
    monthly: list[int]
    total: int
    rows: list[dict[str, str]]
    answer: str
    plot_required: bool
    title: str
    filters: list[str]


def monthly_quantities(session: Session, sku: str | None) -> list[tuple[str, int]]:
    label = func.to_char(Order.order_date, "YYYY-MM")
    statement = (
        select(label, func.coalesce(func.sum(Order.quantity), 0))
        .where(col(Order.order_date) <= BOOK_END)
        .group_by(label)
        .order_by(label)
    )
    if sku:
        statement = statement.where(Order.sku == sku)
    return [(str(month), int(quantity)) for month, quantity in session.exec(statement).all()]


def build_forecast(
    history: list[tuple[str, int]],
    horizon: int,
    sku: str | None,
    method: str | None = None,
) -> DemandForecast:
    months = max(1, min(horizon, 12))
    history = complete_months(history)
    chosen, monthly = choose(history, months, method)
    future = future_months(history, months) if history else []
    rows: list[dict[str, str]] = []
    last = len(history) - 1
    for index, (month, quantity) in enumerate(history):
        rows.append(
            {
                "month": month,
                "history": str(quantity),
                "forecast": str(quantity) if index == last else "",
            }
        )
    if history:
        rows.extend(
            {"month": month, "history": "", "forecast": str(quantity)}
            for month, quantity in zip(future, monthly, strict=True)
        )
    return DemandForecast(
        method=chosen,
        monthly=monthly,
        total=sum(monthly),
        rows=rows if history else [],
        answer=_answer(sku, future, monthly, LABELS[chosen], bool(history)),
        plot_required=bool(history),
        title=f"Monthly quantity for {sku}" if sku else "Monthly quantity",
        filters=_filters(sku),
    )


def _filters(sku: str | None) -> list[str]:
    filters = [f"sku is {sku}"] if sku else ["all orders"]
    filters.append("order date through 2025-12-30")
    return filters


def _answer(
    sku: str | None,
    future: list[str],
    monthly: list[int],
    method: str,
    has_history: bool,
) -> str:
    scope = f"SKU {sku}" if sku else "the whole book"
    if not has_history:
        return (
            f"There is no monthly quantity through December 2025 for {scope}, "
            "so there is no forecast."
        )
    span = future[0] if len(future) == 1 else f"{future[0]} through {future[-1]}"
    total = sum(monthly)
    return (
        f"Demand for {scope} is projected for {span} at {_listed(monthly)} units, "
        f"{total} in total, using {method}. Plan inventory for {total} units."
    )


def _listed(values: list[int]) -> str:
    labels = [str(value) for value in values]
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return f"{', '.join(labels[:-1])}, and {labels[-1]}"
