"""Holt's trend with a damping factor so the slope flattens."""

from src.agent.forecasting.common import Series, quantities, units

_GRID = [step / 10 for step in range(1, 10)]
_PHI = (0.8, 0.9, 0.95)


def project(history: Series, months: list[str]) -> list[int]:
    series = quantities(history)
    if not series:
        return [0] * len(months)
    if len(series) == 1:
        return [series[0]] * len(months)
    alpha, beta, phi = _best_weights(series)
    level, trend = _state(series, alpha, beta, phi)
    return _ahead(level, trend, phi, len(months))


def _ahead(level: float, trend: float, phi: float, horizon: int) -> list[int]:
    forecasts: list[int] = []
    weight = 0.0
    factor = phi
    for _ in range(horizon):
        weight += factor
        forecasts.append(units(level + weight * trend))
        factor *= phi
    return forecasts


def _best_weights(series: list[int]) -> tuple[float, float, float]:
    best = (_GRID[0], _GRID[0], _PHI[0])
    best_error = _squared_error(series, *best)
    for alpha in _GRID:
        for beta in _GRID:
            for phi in _PHI:
                error = _squared_error(series, alpha, beta, phi)
                if error < best_error:
                    best = (alpha, beta, phi)
                    best_error = error
    return best


def _squared_error(series: list[int], alpha: float, beta: float, phi: float) -> float:
    level = float(series[0])
    trend = float(series[1] - series[0])
    error = 0.0
    for value in series[1:]:
        forecast = level + phi * trend
        error += (value - forecast) ** 2
        previous = level
        level = alpha * value + (1 - alpha) * (level + phi * trend)
        trend = beta * (level - previous) + (1 - beta) * phi * trend
    return error


def _state(series: list[int], alpha: float, beta: float, phi: float) -> tuple[float, float]:
    level = float(series[0])
    trend = float(series[1] - series[0])
    for value in series[1:]:
        previous = level
        level = alpha * value + (1 - alpha) * (level + phi * trend)
        trend = beta * (level - previous) + (1 - beta) * phi * trend
    return level, trend
