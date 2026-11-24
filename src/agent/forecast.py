"""Project demand from the book. The model never supplies these numbers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func
from sqlmodel import Session, col, select

from src.agent.forecasting import LABELS, choose, complete_through, resolve_span
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
    horizon: int | None = None,
    sku: str | None = None,
    method: str | None = None,
    start_month: str | None = None,
    end_month: str | None = None,
) -> DemandForecast:
    history = complete_through(history)
    span = resolve_span(start_month, end_month, horizon)
    if not history:
        return _blank(
            sku,
            "There is no monthly quantity through December 2025 for "
            f"{_scope(sku)}, so there is no forecast.",
        )
    if span is None:
        return _blank(sku, _inside_book(sku, start_month, end_month))
    path, reported = span
    chosen, projected = choose(history, path, method)
    by_month = dict(zip(path, projected, strict=True))
    monthly = [by_month[month] for month in reported]
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
    rows.extend({"month": month, "history": "", "forecast": str(by_month[month])} for month in path)
    return DemandForecast(
        method=chosen,
        monthly=monthly,
        total=sum(monthly),
        rows=rows,
        answer=_answer(sku, reported, monthly, LABELS[chosen]),
        plot_required=True,
        title=f"Monthly quantity for {sku}" if sku else "Monthly quantity",
        filters=_filters(sku),
    )


def _scope(sku: str | None) -> str:
    return f"SKU {sku}" if sku else "the whole book"


def _blank(sku: str | None, answer: str) -> DemandForecast:
    return DemandForecast(
        method="moving_average",
        monthly=[],
        total=0,
        rows=[],
        answer=answer,
        plot_required=False,
        title=f"Monthly quantity for {sku}" if sku else "Monthly quantity",
        filters=_filters(sku),
    )


def _inside_book(sku: str | None, start: str | None, end: str | None) -> str:
    if start and end and start != end:
        label = f"{start} through {end}"
    else:
        label = start or end or "That month"
    return f"{label} is history for {_scope(sku)}, through December 2025, so there is no forecast."


def _filters(sku: str | None) -> list[str]:
    filters = [f"sku is {sku}"] if sku else ["all orders"]
    filters.append("order date through 2025-12-30")
    return filters


def _answer(
    sku: str | None,
    future: list[str],
    monthly: list[int],
    method: str,
) -> str:
    scope = _scope(sku)
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
