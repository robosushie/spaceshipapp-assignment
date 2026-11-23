"""Shared month labels and rounding for the forecast pack."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

FORECAST_START = "2026-01"
Series = list[tuple[str, int]]


def quantities(history: Series) -> list[int]:
    return [quantity for _, quantity in history]


def units(value: Decimal | float) -> int:
    number = value if isinstance(value, Decimal) else Decimal(str(value))
    rounded = int(number.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return max(0, rounded)


def complete_months(history: Series) -> Series:
    if not history:
        return []
    ordered = sorted(dict(history).items())
    observed = dict(ordered)
    cursor = ordered[0][0]
    last = ordered[-1][0]
    filled: Series = []
    while True:
        filled.append((cursor, observed.get(cursor, 0)))
        if cursor == last:
            return filled
        cursor = _next_month(cursor)


def future_months(history: Series, horizon: int) -> list[str]:
    start = _next_month(history[-1][0]) if history else FORECAST_START
    months = [start]
    for _ in range(horizon - 1):
        months.append(_next_month(months[-1]))
    return months


def _next_month(label: str) -> str:
    year, month = (int(part) for part in label.split("-"))
    if month == 12:
        return f"{year + 1:04d}-01"
    return f"{year:04d}-{month + 1:02d}"


def previous_year(label: str) -> str:
    year, month = label.split("-")
    return f"{int(year) - 1:04d}-{month}"
