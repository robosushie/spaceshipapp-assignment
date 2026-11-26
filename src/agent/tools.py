"""LangGraph compute tools for the ReAct question agent."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime

from src.agent.baml_client import b
from src.agent.baml_client import types as baml_types
from src.agent.forecast import build_forecast, monthly_quantities
from src.agent.forecasting import LABELS
from src.agent.forecasting.common import valid_month
from src.agent.schema import BOOK_AS_OF, logistics_ddl
from src.agent.sql_guard import SqlRejected, run_select

_CHART_TYPES = {
    baml_types.ChartType.Bar: "bar",
    baml_types.ChartType.Line: "line",
    baml_types.ChartType.Area: "area",
    baml_types.ChartType.Pie: "pie",
    baml_types.ChartType.Scatter: "scatter",
}
_MAX_QUERY_ATTEMPTS = 3


@tool("query_book")
def query_book(question: str, runtime: ToolRuntime) -> str:
    """Run one analytics query against the shipping book.

    Use for counts, filters, comparisons, trends, and charts of past orders.
    Call again with a narrower question when the user needs another plot or metric.
    Do not invent row values; only report what this tool returns.
    """
    session = _session(runtime)
    schema = logistics_ddl()
    previous_sql = ""
    error = ""
    last_error = "The query could not be run."
    for _ in range(_MAX_QUERY_ATTEMPTS):
        plan = b.WriteQuery(
            question=question,
            schema=schema,
            as_of=BOOK_AS_OF,
            previous_sql=previous_sql,
            error=error,
        )
        chart_type = _CHART_TYPES[plan.chart_type] if plan.chart_type is not None else None
        try:
            rows = run_select(session, plan.sql)
        except SqlRejected as exc:
            last_error = str(exc)
            if not exc.repair:
                return _payload(
                    {
                        "ok": False,
                        "kind": "query",
                        "error": last_error,
                        "rows": [],
                    }
                )
            previous_sql = plan.sql
            error = last_error
            continue
        problem = _chart_problem(plan.plot_required, plan.x_key, list(plan.y_keys), rows)
        if problem is not None:
            last_error = problem
            previous_sql = plan.sql
            error = problem
            continue
        chart = None
        if plan.plot_required and chart_type and plan.x_key and plan.y_keys and rows:
            chart = {
                "type": chart_type,
                "title": plan.title or "Result",
                "x_key": plan.x_key,
                "y_keys": list(plan.y_keys),
                "rows": rows,
            }
        return _payload(
            {
                "ok": True,
                "kind": "query",
                "sql": plan.sql,
                "filters": list(plan.filters),
                "metrics": list(plan.metrics),
                "dimensions": list(plan.dimensions),
                "rows": rows,
                "chart": chart,
                "summary": f"{len(rows)} row(s) returned.",
            }
        )
    return _payload(
        {
            "ok": False,
            "kind": "query",
            "error": last_error,
            "rows": [],
        }
    )


@tool("forecast_demand")
def forecast_demand(
    horizon_months: int = 4,
    sku: str = "",
    forecast_method: str = "auto",
    start_month: str = "",
    end_month: str = "",
    *,
    runtime: ToolRuntime,
) -> str:
    """Forecast monthly demand from historical order quantity.

    Use for predict, forecast, project, or inventory planning questions.
    Numbers come only from this computation. Call again for another SKU or horizon.
    """
    session = _session(runtime)
    built = build_forecast(
        monthly_quantities(session, sku.strip() or None),
        horizon_months,
        sku.strip() or None,
        forecast_method or "auto",
        valid_month(start_month) if start_month else None,
        valid_month(end_month) if end_month else None,
    )
    chart = None
    if built.plot_required and built.rows:
        chart = {
            "type": "line",
            "title": built.title or "Demand forecast",
            "x_key": "month",
            "y_keys": ["history", "forecast"],
            "rows": built.rows,
        }
    return _payload(
        {
            "ok": True,
            "kind": "forecast",
            "method": LABELS[built.method],
            "filters": built.filters,
            "metrics": ["quantity"],
            "dimensions": ["month"],
            "rows": built.rows,
            "chart": chart,
            "summary": built.answer,
        }
    )


TOOLS = [query_book, forecast_demand]


def _session(runtime: ToolRuntime) -> Any:
    configurable = runtime.config.get("configurable") or {}
    return configurable["session"]


def _payload(value: dict[str, Any]) -> str:
    return json.dumps(value)


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


def parse_tool_payload(content: object) -> dict[str, Any] | None:
    if not isinstance(content, str) or not content.strip():
        return None
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload
