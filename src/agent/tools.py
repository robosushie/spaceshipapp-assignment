"""LangGraph tools for question routing, SQL, forecast, and BAML steps."""

from __future__ import annotations

import json
from typing import Annotated, Any

from langchain_core.tools import InjectedToolArg, tool
from sqlmodel import Session

from src.agent.baml_client import b
from src.agent.baml_client import types as baml_types
from src.agent.forecast import build_forecast, monthly_quantities
from src.agent.forecasting import LABELS
from src.agent.forecasting.common import valid_month
from src.agent.schema import BOOK_AS_OF
from src.agent.sql_guard import SqlRejected, run_select

_CHART_TYPES = {
    baml_types.ChartType.Bar: "bar",
    baml_types.ChartType.Line: "line",
    baml_types.ChartType.Area: "area",
    baml_types.ChartType.Pie: "pie",
    baml_types.ChartType.Scatter: "scatter",
}
_FORECAST_METHODS = {
    baml_types.ForecastMethod.Auto: "auto",
    baml_types.ForecastMethod.MovingAverage: "moving_average",
    baml_types.ForecastMethod.ExponentialSmoothing: "exponential_smoothing",
    baml_types.ForecastMethod.HoltTrend: "holt_trend",
    baml_types.ForecastMethod.SeasonalNaive: "seasonal_naive",
    baml_types.ForecastMethod.LinearTrend: "linear_trend",
    baml_types.ForecastMethod.Mean: "mean",
    baml_types.ForecastMethod.Naive: "naive",
    baml_types.ForecastMethod.Drift: "drift",
    baml_types.ForecastMethod.DampedTrend: "damped_trend",
    baml_types.ForecastMethod.Theta: "theta",
    baml_types.ForecastMethod.Croston: "croston",
    baml_types.ForecastMethod.Sba: "sba",
    baml_types.ForecastMethod.Tsb: "tsb",
}


@tool("choose_tool")
def choose_tool(question: str, as_of: str) -> dict[str, Any]:
    """Interpret the question and select the query or forecast tool."""
    choice = b.ChooseTool(question=question, as_of=as_of or BOOK_AS_OF)
    sku = choice.sku.strip() if isinstance(choice.sku, str) else ""
    method = "auto"
    if choice.method is not None:
        method = _FORECAST_METHODS.get(choice.method, "auto")
    return {
        "tool": "forecast" if choice.tool == baml_types.ToolName.Forecast else "query",
        "sku": sku or None,
        "horizon_months": choice.horizon_months if choice.horizon_months is not None else 4,
        "start_month": valid_month(choice.start_month),
        "end_month": valid_month(choice.end_month),
        "forecast_method": method,
    }


@tool("write_query")
def write_query(
    question: str,
    schema_ddl: str,
    as_of: str,
    previous_sql: str = "",
    error: str = "",
) -> dict[str, Any]:
    """Write one validated SELECT plan with BAML WriteQuery."""
    plan = b.WriteQuery(
        question=question,
        schema=schema_ddl,
        as_of=as_of or BOOK_AS_OF,
        previous_sql=previous_sql,
        error=error,
    )
    chart_type = _CHART_TYPES[plan.chart_type] if plan.chart_type is not None else None
    return {
        "sql": plan.sql,
        "plot_required": plan.plot_required,
        "chart_type": chart_type,
        "title": plan.title,
        "x_key": plan.x_key,
        "y_keys": list(plan.y_keys),
        "filters": list(plan.filters),
        "metrics": list(plan.metrics),
        "dimensions": list(plan.dimensions),
        "tool": "query",
        "error": None,
        "refused": False,
    }


@tool("run_sql")
def run_sql(
    sql: str,
    plot_required: bool = False,
    x_key: str = "",
    y_keys: list[str] | None = None,
    *,
    session: Annotated[Session, InjectedToolArg],
) -> dict[str, Any]:
    """Run one allow-listed read-only SELECT against the shipping book."""
    keys = list(y_keys or [])
    try:
        rows = run_select(session, sql or "")
    except SqlRejected as exc:
        return {"error": str(exc), "rows": [], "refused": not exc.repair}
    problem = _chart_problem(plot_required, x_key or None, keys, rows)
    if problem is not None:
        return {"error": problem, "rows": [], "refused": False}
    return {"rows": rows, "error": None, "refused": False}


@tool("explain_rows")
def explain_rows(question: str, rows_json: str, plot_required: bool = False) -> dict[str, str]:
    """Turn computed rows into a short answer with BAML ExplainRows."""
    answer = b.ExplainRows(
        question=question,
        rows_json=rows_json,
        plot_required=plot_required,
    )
    return {"answer": answer}


@tool("forecast_demand")
def forecast_demand(
    horizon_months: int = 4,
    sku: str = "",
    forecast_method: str = "auto",
    start_month: str = "",
    end_month: str = "",
    *,
    session: Annotated[Session, InjectedToolArg],
) -> dict[str, Any]:
    """Forecast demand from historical monthly quantity. Numbers come from computation only."""
    built = build_forecast(
        monthly_quantities(session, sku or None),
        horizon_months,
        sku or None,
        forecast_method or "auto",
        start_month or None,
        end_month or None,
    )
    return {
        "tool": "forecast",
        "answer": built.answer,
        "plot_required": built.plot_required,
        "chart_type": "line" if built.plot_required else None,
        "title": built.title,
        "x_key": "month" if built.plot_required else None,
        "y_keys": ["history", "forecast"] if built.plot_required else [],
        "rows": built.rows,
        "filters": built.filters,
        "metrics": ["quantity"],
        "dimensions": ["month"],
        "method": LABELS[built.method],
        "error": None,
        "refused": False,
    }


TOOLS = [choose_tool, write_query, run_sql, explain_rows, forecast_demand]


def _chart_problem(
    plot_required: bool,
    x_key: str | None,
    y_keys: list[str],
    rows: list[dict[str, str]],
) -> str | None:
    if not plot_required:
        return None
    if not rows:
        return "The query returned no rows."
    if not x_key or not y_keys:
        return "A plot needs x_key and y_keys that match the SELECT aliases."
    columns = set(rows[0])
    missing = [key for key in [x_key, *y_keys] if key not in columns]
    if missing:
        return f"Result is missing columns: {', '.join(missing)}."
    return None


def rows_to_json(rows: object) -> str:
    if not isinstance(rows, list):
        return "[]"
    return json.dumps(rows)
