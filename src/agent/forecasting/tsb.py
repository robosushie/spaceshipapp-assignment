"""Chance of an order, updated every month, times the size of an order."""

from src.agent.forecasting.common import Series, quantities, units

_GRID = [step / 10 for step in range(1, 10)]


def project(history: Series, months: list[str]) -> list[int]:
    series = quantities(history)
    if not months:
        return []
    if not any(value > 0 for value in series):
        return [0] * len(months)
    best_error: float | None = None
    best_rate = 0.0
    for alpha in _GRID:
        for beta in _GRID:
            error, rate = _fit(series, alpha, beta)
            if best_error is None or error < best_error:
                best_error = error
                best_rate = rate
    return [units(best_rate)] * len(months)


def _fit(series: list[int], alpha: float, beta: float) -> tuple[float, float]:
    positives = [value for value in series if value > 0]
    size = float(positives[0])
    probability = 1.0 if series[0] > 0 else 0.0
    error = 0.0
    for value in series[1:]:
        error += (value - probability * size) ** 2
        occurred = 1.0 if value > 0 else 0.0
        probability = beta * occurred + (1 - beta) * probability
        if value > 0:
            size = alpha * value + (1 - alpha) * size
    return error, probability * size
