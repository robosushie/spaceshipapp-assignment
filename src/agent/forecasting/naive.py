"""Repeat the last observed month."""

from src.agent.forecasting.common import Series, quantities


def project(history: Series, months: list[str]) -> list[int]:
    series = quantities(history)
    last = series[-1] if series else 0
    return [last] * len(months)
