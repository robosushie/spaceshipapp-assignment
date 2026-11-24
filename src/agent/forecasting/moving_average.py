"""Repeat the mean of the last three months."""

from decimal import Decimal

from src.agent.forecasting.common import Series, quantities, units


def project(history: Series, months: list[str]) -> list[int]:
    window = quantities(history)[-3:]
    if not window:
        return [0] * len(months)
    mean = Decimal(sum(window)) / Decimal(len(window))
    return [units(mean)] * len(months)
