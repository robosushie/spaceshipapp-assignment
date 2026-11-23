"""Repeat the same calendar month from the previous year."""

from src.agent.forecasting.common import Series, future_months, previous_year


def project(history: Series, horizon: int) -> list[int]:
    observed = {month: quantity for month, quantity in history}
    forecasts: list[int] = []
    for month in future_months(history, horizon):
        quantity = 0
        earlier = month
        for _ in range(3):
            earlier = previous_year(earlier)
            if earlier in observed:
                quantity = observed[earlier]
                break
        forecasts.append(max(0, quantity))
    return forecasts
