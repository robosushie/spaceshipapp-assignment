"""Smooth demand size and the gap between orders, and divide size by gap."""

from src.agent.forecasting.common import Series, quantities, units

_GRID = [step / 10 for step in range(1, 10)]


def project(history: Series, months: list[str]) -> list[int]:
    return _rate(history, months, correct=False)


def _rate(history: Series, months: list[str], correct: bool) -> list[int]:
    series = quantities(history)
    if not months:
        return []
    if not any(value > 0 for value in series):
        return [0] * len(months)
    best_error: float | None = None
    best_rate = 0.0
    for alpha in _GRID:
        for beta in _GRID:
            error, size, gap = _fit(series, alpha, beta)
            rate = size / gap
            if correct:
                rate *= 1 - beta / 2
            if best_error is None or error < best_error:
                best_error = error
                best_rate = rate
    return [units(best_rate)] * len(months)


def _fit(series: list[int], alpha: float, beta: float) -> tuple[float, float, float]:
    first = next(index for index, value in enumerate(series) if value > 0)
    size = float(series[first])
    gap = float(first + 1)
    since = 0
    error = 0.0
    for index in range(first + 1, len(series)):
        since += 1
        value = series[index]
        error += (value - size / gap) ** 2
        if value > 0:
            size = alpha * value + (1 - alpha) * size
            gap = beta * since + (1 - beta) * gap
            since = 0
    return error, size, gap
