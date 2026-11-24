"""Shared month labels and rounding for the forecast pack."""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal

BOOK_END_MONTH = "2025-12"
MAX_SPAN = 60
Series = list[tuple[str, int]]
_MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def quantities(history: Series) -> list[int]:
    return [quantity for _, quantity in history]


def units(value: Decimal | float) -> int:
    number = value if isinstance(value, Decimal) else Decimal(str(value))
    rounded = int(number.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return max(0, rounded)


def valid_month(label: str | None) -> str | None:
    if label and _MONTH.match(label):
        return label
    return None


def next_month(label: str) -> str:
    year, month = (int(part) for part in label.split("-"))
    if month == 12:
        return f"{year + 1:04d}-01"
    return f"{year:04d}-{month + 1:02d}"


def add_months(label: str, count: int) -> str:
    year, month = (int(part) for part in label.split("-"))
    index = year * 12 + (month - 1) + count
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def month_span(start: str, end: str) -> list[str]:
    if start > end:
        return []
    months: list[str] = []
    cursor = start
    while cursor <= end and len(months) < MAX_SPAN:
        months.append(cursor)
        cursor = next_month(cursor)
    return months


def origin_month() -> str:
    return next_month(BOOK_END_MONTH)


def complete_through(history: Series, end: str = BOOK_END_MONTH) -> Series:
    observed = {month: quantity for month, quantity in history if month <= end}
    if not observed:
        return []
    cursor = min(observed)
    last = end if end >= max(observed) else max(observed)
    filled: Series = []
    while len(filled) <= 240:
        filled.append((cursor, observed.get(cursor, 0)))
        if cursor == last:
            return filled
        cursor = next_month(cursor)
    return filled


def resolve_span(
    start: str | None,
    end: str | None,
    horizon: int | None,
) -> tuple[list[str], list[str]] | None:
    """Months to plot from the origin, and the months the question asked for.

    None means every asked month is already inside the book.
    """
    start = valid_month(start)
    end = valid_month(end)
    origin = origin_month()
    latest = add_months(origin, MAX_SPAN - 1)
    if start is None and end is None:
        count = 4 if horizon is None else int(horizon)
        count = max(1, min(count, MAX_SPAN))
        reported = month_span(origin, add_months(origin, count - 1))
        return reported, reported
    asked_end = end or start
    asked_start = start or origin
    if asked_end is None or asked_start is None:
        return None
    if asked_end < origin and asked_start < origin:
        return None
    if asked_start < origin:
        asked_start = origin
    if asked_end < asked_start:
        asked_end = asked_start
    if asked_start > latest:
        asked_start = latest
        asked_end = latest
    elif asked_end > latest:
        asked_end = latest
    return month_span(origin, asked_end), month_span(asked_start, asked_end)


def previous_year(label: str) -> str:
    year, month = label.split("-")
    return f"{int(year) - 1:04d}-{month}"
