"""Last value plus the average change from the first month to the last."""

from src.agent.forecasting.common import Series, quantities, units


def project(history: Series, months: list[str]) -> list[int]:
    series = quantities(history)
    if not series:
        return [0] * len(months)
    if len(series) == 1:
        return [series[0]] * len(months)
    step = (series[-1] - series[0]) / (len(series) - 1)
    return [units(series[-1] + ahead * step) for ahead in range(1, len(months) + 1)]
