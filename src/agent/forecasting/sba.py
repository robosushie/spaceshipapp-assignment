"""Croston's rate multiplied by one minus half the interval smoothing weight."""

from src.agent.forecasting.common import Series
from src.agent.forecasting.croston import _rate


def project(history: Series, months: list[str]) -> list[int]:
    return _rate(history, months, correct=True)
