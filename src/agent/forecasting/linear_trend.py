"""Ordinary least squares of quantity on the month index."""

from src.agent.forecasting.common import Series, quantities, units


def project(history: Series, months: list[str]) -> list[int]:
    series = quantities(history)
    if not series:
        return [0] * len(months)
    if len(series) == 1:
        return [series[0]] * len(months)
    slope, intercept = _fit(series)
    start = len(series)
    return [units(intercept + slope * (start + step)) for step in range(len(months))]


def _fit(series: list[int]) -> tuple[float, float]:
    count = len(series)
    mean_index = (count - 1) / 2
    mean_value = sum(series) / count
    variance = sum((index - mean_index) ** 2 for index in range(count))
    covariance = sum(
        (index - mean_index) * (value - mean_value) for index, value in enumerate(series)
    )
    slope = covariance / variance
    intercept = mean_value - slope * mean_index
    return slope, intercept
