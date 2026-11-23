"""Pick a named method, or the one with the lowest error on the last three months."""

from collections.abc import Callable

from src.agent.forecasting.common import Series
from src.agent.forecasting.exponential_smoothing import project as exponential_smoothing
from src.agent.forecasting.holt import project as holt_trend
from src.agent.forecasting.linear_trend import project as linear_trend
from src.agent.forecasting.moving_average import project as moving_average
from src.agent.forecasting.seasonal_naive import project as seasonal_naive

Method = Callable[[Series, int], list[int]]
_HOLDOUT = 3
_METHODS: list[tuple[str, Method]] = [
    ("moving_average", moving_average),
    ("exponential_smoothing", exponential_smoothing),
    ("holt_trend", holt_trend),
    ("seasonal_naive", seasonal_naive),
    ("linear_trend", linear_trend),
]
_BY_NAME = dict(_METHODS)
LABELS = {
    "moving_average": "three-month moving average",
    "exponential_smoothing": "exponential smoothing",
    "holt_trend": "Holt's linear trend",
    "seasonal_naive": "seasonal naive",
    "linear_trend": "linear trend",
}


def choose(history: Series, horizon: int, method: str | None) -> tuple[str, list[int]]:
    name = method if method in _BY_NAME else None
    if name is None and len(history) < _HOLDOUT * 2:
        name = "moving_average"
    if name is None:
        name = _lowest_holdout(history)
    return name, _BY_NAME[name](history, horizon)


def _lowest_holdout(history: Series) -> str:
    train = history[:-_HOLDOUT]
    actual = [quantity for _, quantity in history[-_HOLDOUT:]]
    best = _METHODS[0][0]
    best_error: float | None = None
    for name, method in _METHODS:
        projected = method(train, _HOLDOUT)
        error = sum(abs(left - right) for left, right in zip(projected, actual, strict=True))
        if best_error is None or error < best_error:
            best = name
            best_error = error
    return best
