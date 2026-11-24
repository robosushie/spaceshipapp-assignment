"""Holt's linear trend. Future month h is level plus h times trend."""

from src.agent.forecasting.common import Series, quantities, units

_GRID = [step / 10 for step in range(1, 10)]


def project(history: Series, months: list[str]) -> list[int]:
    series = quantities(history)
    if not series:
        return [0] * len(months)
    if len(series) == 1:
        return [series[0]] * len(months)
    alpha, beta = _best_weights(series)
    level, trend = _state(series, alpha, beta)
    return [units(level + step * trend) for step in range(1, len(months) + 1)]


def _best_weights(series: list[int]) -> tuple[float, float]:
    best = (_GRID[0], _GRID[0])
    best_error = _squared_error(series, best[0], best[1])
    for alpha in _GRID:
        for beta in _GRID:
            error = _squared_error(series, alpha, beta)
            if error < best_error:
                best = (alpha, beta)
                best_error = error
    return best


def _squared_error(series: list[int], alpha: float, beta: float) -> float:
    level = float(series[0])
    trend = float(series[1] - series[0])
    error = 0.0
    for value in series[1:]:
        forecast = level + trend
        error += (value - forecast) ** 2
        previous = level
        level = alpha * value + (1 - alpha) * (level + trend)
        trend = beta * (level - previous) + (1 - beta) * trend
    return error


def _state(series: list[int], alpha: float, beta: float) -> tuple[float, float]:
    level = float(series[0])
    trend = float(series[1] - series[0])
    for value in series[1:]:
        previous = level
        level = alpha * value + (1 - alpha) * (level + trend)
        trend = beta * (level - previous) + (1 - beta) * trend
    return level, trend
