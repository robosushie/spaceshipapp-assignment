from src.agent.forecast import build_forecast
from src.agent.forecasting.exponential_smoothing import project as exponential_smoothing
from src.agent.forecasting.holt import project as holt_trend
from src.agent.forecasting.linear_trend import project as linear_trend
from src.agent.forecasting.moving_average import project as moving_average
from src.agent.forecasting.seasonal_naive import project as seasonal_naive
from src.agent.forecasting.select import choose

_YEAR = [(f"2025-{month:02d}", value) for month, value in enumerate(range(1, 13), start=1)]


def test_moving_average_repeats_the_three_month_mean() -> None:
    history = [("2025-10", 10), ("2025-11", 20), ("2025-12", 30)]
    assert moving_average(history, 4) == [20, 20, 20, 20]
    forecast = build_forecast(history, horizon=2, sku=None, method="moving_average")
    assert forecast.monthly == [20, 20]
    assert forecast.total == 40
    assert "using three-month moving average" in forecast.answer
    assert forecast.rows[-1] == {"month": "2026-02", "history": "", "forecast": "20"}
    assert forecast.rows[-3] == {"month": "2025-12", "history": "30", "forecast": "30"}


def test_forecast_plot_fills_a_missing_month_and_joins_the_line() -> None:
    forecast = build_forecast(
        [("2025-10", 10), ("2025-12", 30)],
        horizon=1,
        sku=None,
        method="moving_average",
    )
    assert [row["month"] for row in forecast.rows] == [
        "2025-10",
        "2025-11",
        "2025-12",
        "2026-01",
    ]
    assert forecast.rows[1] == {"month": "2025-11", "history": "0", "forecast": ""}
    assert forecast.rows[2]["forecast"] == "30"
    assert forecast.rows[-1]["history"] == ""
    assert forecast.monthly == [13]


def test_moving_average_rounds_half_up() -> None:
    assert moving_average([("2025-10", 10), ("2025-11", 10), ("2025-12", 11)], 1) == [10]
    assert moving_average([("2025-10", 10), ("2025-11", 10), ("2025-12", 12)], 1) == [11]


def test_exponential_smoothing_is_a_fitted_level() -> None:
    assert exponential_smoothing([("2025-11", 5), ("2025-12", 15)], 2) == [6, 6]


def test_holt_projects_the_step() -> None:
    assert holt_trend([("2025-11", 0), ("2025-12", 10)], 2) == [20, 30]


def test_seasonal_naive_uses_the_same_month_last_year() -> None:
    history = [
        ("2025-01", 4),
        ("2025-02", 5),
        ("2025-03", 6),
        ("2025-12", 9),
    ]
    assert seasonal_naive(history, 3) == [4, 5, 6]


def test_linear_trend_continues_the_line() -> None:
    history = [("2025-10", 0), ("2025-11", 10), ("2025-12", 20)]
    assert linear_trend(history, 2) == [30, 40]


def test_a_rising_series_prefers_a_trend_over_the_flat_average() -> None:
    method, monthly = choose(_YEAR, horizon=3, method=None)
    assert method in {"holt_trend", "linear_trend"}
    assert monthly[0] > 12
    flat = choose(_YEAR, horizon=3, method="moving_average")
    assert flat[0] == "moving_average"
    assert flat[1] == [11, 11, 11]
