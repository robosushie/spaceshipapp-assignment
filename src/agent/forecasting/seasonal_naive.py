"""Repeat the same calendar month from the previous year."""

from src.agent.forecasting.common import Series, previous_year


def project(history: Series, months: list[str]) -> list[int]:
    observed = {month: quantity for month, quantity in history}
    forecasts: list[int] = []
    for month in months:
        quantity = 0
        earlier = month
        for _ in range(3):
            earlier = previous_year(earlier)
            if earlier in observed:
                quantity = observed[earlier]
                break
        forecasts.append(max(0, quantity))
    return forecasts
