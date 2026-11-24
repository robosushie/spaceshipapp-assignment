"""Repeat the average of the whole history."""

from decimal import Decimal

from src.agent.forecasting.common import Series, quantities, units


def project(history: Series, months: list[str]) -> list[int]:
    series = quantities(history)
    if not series:
        return [0] * len(months)
    average = Decimal(sum(series)) / Decimal(len(series))
    return [units(average)] * len(months)
