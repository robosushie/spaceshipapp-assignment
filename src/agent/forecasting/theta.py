"""Average of a straight line and exponential smoothing on the steepened series.

Hyndman and Billah showed this is the level from simple exponential smoothing
plus half the ordinary-least-squares slope.
"""

from src.agent.forecasting.common import Series, quantities, units
from src.agent.forecasting.exponential_smoothing import fitted_level


def project(history: Series, months: list[str]) -> list[int]:
    series = quantities(history)
    if not series:
        return [0] * len(months)
    if len(series) == 1:
        return [series[0]] * len(months)
    level = fitted_level(series)
    slope = _slope(series) / 2
    return [units(level + step * slope) for step in range(1, len(months) + 1)]


def _slope(series: list[int]) -> float:
    count = len(series)
    mean_index = (count - 1) / 2
    mean_value = sum(series) / count
    variance = sum((index - mean_index) ** 2 for index in range(count))
    covariance = sum(
        (index - mean_index) * (value - mean_value) for index, value in enumerate(series)
    )
    return covariance / variance
