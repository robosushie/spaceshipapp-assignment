from src.agent.forecast import build_forecast
from src.agent.forecasting.common import add_months, month_span
from src.agent.forecasting.croston import project as croston
from src.agent.forecasting.damped_trend import project as damped_trend
from src.agent.forecasting.drift import project as drift
from src.agent.forecasting.exponential_smoothing import project as exponential_smoothing
from src.agent.forecasting.holt import project as holt_trend
from src.agent.forecasting.linear_trend import project as linear_trend
from src.agent.forecasting.mean import project as mean
from src.agent.forecasting.moving_average import project as moving_average
from src.agent.forecasting.naive import project as naive
from src.agent.forecasting.sba import project as sba
from src.agent.forecasting.seasonal_naive import project as seasonal_naive
from src.agent.forecasting.select import choose
from src.agent.forecasting.theta import project as theta
from src.agent.forecasting.tsb import project as tsb

_YEAR = [(f"2025-{month:02d}", value) for month, value in enumerate(range(1, 13), start=1)]


def _ahead(count: int) -> list[str]:
    return month_span("2026-01", add_months("2026-01", count - 1))


def test_moving_average_repeats_the_three_month_mean() -> None:
    history = [("2025-10", 10), ("2025-11", 20), ("2025-12", 30)]
    assert moving_average(history, _ahead(4)) == [20, 20, 20, 20]
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
    assert moving_average([("2025-10", 10), ("2025-11", 10), ("2025-12", 11)], _ahead(1)) == [10]
    assert moving_average([("2025-10", 10), ("2025-11", 10), ("2025-12", 12)], _ahead(1)) == [11]


def test_exponential_smoothing_is_a_fitted_level() -> None:
    assert exponential_smoothing([("2025-11", 5), ("2025-12", 15)], _ahead(2)) == [6, 6]


def test_holt_projects_the_step() -> None:
    assert holt_trend([("2025-11", 0), ("2025-12", 10)], _ahead(2)) == [20, 30]


def test_seasonal_naive_uses_the_same_month_last_year() -> None:
    history = [
        ("2025-01", 4),
        ("2025-02", 5),
        ("2025-03", 6),
        ("2025-12", 9),
    ]
    assert seasonal_naive(history, _ahead(3)) == [4, 5, 6]


def test_linear_trend_continues_the_line() -> None:
    history = [("2025-10", 0), ("2025-11", 10), ("2025-12", 20)]
    assert linear_trend(history, _ahead(2)) == [30, 40]


def test_a_rising_series_prefers_a_trend_over_the_flat_average() -> None:
    method, monthly = choose(_YEAR, _ahead(3), method=None)
    assert method == "holt_trend"
    assert monthly[0] > 12
    flat = choose(_YEAR, _ahead(3), method="moving_average")
    assert flat[0] == "moving_average"
    assert flat[1] == [11, 11, 11]


def test_forecast_starts_after_the_book_when_orders_stop_early() -> None:
    forecast = build_forecast(
        [("2025-05", 8), ("2025-07", 18)],
        horizon=4,
        sku="STICKER-0063",
        method="moving_average",
    )
    forecast_months = [row["month"] for row in forecast.rows if row["history"] == ""]
    assert forecast_months == ["2026-01", "2026-02", "2026-03", "2026-04"]
    assert forecast.monthly == [0, 0, 0, 0]
    august = next(row for row in forecast.rows if row["month"] == "2025-08")
    assert august == {"month": "2025-08", "history": "0", "forecast": ""}


def test_a_named_month_is_the_only_inventory_total() -> None:
    forecast = build_forecast(
        [("2025-05", 8), ("2025-07", 18)],
        method="mean",
        start_month="2027-06",
        end_month="2027-06",
    )
    assert forecast.monthly == [3]
    assert forecast.total == 3
    assert "2027-06" in forecast.answer
    assert forecast.rows[-1]["month"] == "2027-06"
    january = next(row for row in forecast.rows if row["month"] == "2026-01")
    assert january["forecast"] == "3"


def test_a_named_range_sums_only_those_months() -> None:
    forecast = build_forecast(
        [("2025-10", 10), ("2025-11", 20), ("2025-12", 30)],
        method="moving_average",
        start_month="2026-03",
        end_month="2026-05",
    )
    assert [row["month"] for row in forecast.rows if row["history"] == ""] == [
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
    ]
    assert forecast.monthly == [20, 20, 20]
    assert forecast.total == 60


def test_through_a_month_starts_after_the_book() -> None:
    forecast = build_forecast([("2025-12", 30)], method="naive", end_month="2026-03")
    assert forecast.monthly == [30, 30, 30]
    assert "2026-01 through 2026-03" in forecast.answer


def test_a_month_inside_the_book_is_not_forecast() -> None:
    forecast = build_forecast(
        [("2025-06", 4)],
        method="mean",
        start_month="2025-06",
        end_month="2025-06",
    )
    assert forecast.monthly == []
    assert forecast.plot_required is False
    assert "history" in forecast.answer


def test_level_trend_and_intermittent_methods() -> None:
    ahead = _ahead(2)
    assert mean([("2025-10", 10), ("2025-11", 20), ("2025-12", 30)], ahead) == [20, 20]
    assert naive([("2025-12", 30)], _ahead(3)) == [30, 30, 30]
    assert drift([("2025-10", 0), ("2025-11", 10), ("2025-12", 20)], ahead) == [30, 40]
    assert theta([("2025-11", 0), ("2025-12", 10)], ahead) == [6, 11]
    flat = [("2025-01", 5), ("2025-02", 5), ("2025-03", 5), ("2025-04", 5)]
    assert damped_trend(flat, ahead) == [5, 5]
    assert damped_trend([("2025-11", 0), ("2025-12", 10)], ahead) == [19, 27]
    lumpy = [("2025-09", 10), ("2025-10", 0), ("2025-11", 10), ("2025-12", 0)]
    assert croston(lumpy, _ahead(1)) == [5]
    assert sba(lumpy, _ahead(1)) == [3]
    assert tsb(lumpy, _ahead(1)) == [6]
    dead = [("2025-08", 10), ("2025-09", 0), ("2025-10", 0), ("2025-11", 0), ("2025-12", 0)]
    assert tsb(dead, _ahead(1)) < croston(dead, _ahead(1))
