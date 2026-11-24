"""Simple exponential smoothing. The forecast is the fitted level."""

from src.agent.forecasting.common import Series, quantities, units

_ALPHAS = [step / 10 for step in range(1, 10)]


def project(history: Series, months: list[str]) -> list[int]:
    series = quantities(history)
    if not series:
        return [0] * len(months)
    return [units(fitted_level(series))] * len(months)


def fitted_level(series: list[int]) -> float:
    if not series:
        return 0.0
    if len(series) == 1:
        return float(series[0])
    return _level(series, _best_alpha(series))


def _best_alpha(series: list[int]) -> float:
    best = _ALPHAS[0]
    best_error = _squared_error(series, best)
    for alpha in _ALPHAS[1:]:
        error = _squared_error(series, alpha)
        if error < best_error:
            best = alpha
            best_error = error
    return best


def _squared_error(series: list[int], alpha: float) -> float:
    level = float(series[0])
    error = 0.0
    for value in series[1:]:
        error += (value - level) ** 2
        level = alpha * value + (1 - alpha) * level
    return error


def _level(series: list[int], alpha: float) -> float:
    level = float(series[0])
    for value in series[1:]:
        level = alpha * value + (1 - alpha) * level
    return level
