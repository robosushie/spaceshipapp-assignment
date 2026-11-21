import json
from typing import Any

from langchain_core.runnables import RunnableConfig

from src.agent.baml_client import b
from src.agent.baml_client import types as baml_types
from src.agent.schema import BOOK_AS_OF
from src.agent.sql_guard import SqlRejected, run_select
from src.agent.state import AgentState

COULD_NOT_QUERY = "The question could not be queried."
_CHART_TYPES = {
    baml_types.ChartType.Bar: "bar",
    baml_types.ChartType.Line: "line",
    baml_types.ChartType.Area: "area",
    baml_types.ChartType.Pie: "pie",
    baml_types.ChartType.Scatter: "scatter",
}


def write_query(state: AgentState) -> dict[str, Any]:
    error = state.get("error") or ""
    repairs = state.get("repairs", 0)
    if error:
        repairs += 1
    plan = b.WriteQuery(
        question=state["question"],
        schema=state["schema_ddl"],
        as_of=state.get("as_of") or BOOK_AS_OF,
        previous_sql=state.get("sql") or "",
        error=error,
    )
    chart_type = _CHART_TYPES[plan.chart_type] if plan.chart_type is not None else None
    return {
        "repairs": repairs,
        "sql": plan.sql,
        "plot_required": plan.plot_required,
        "chart_type": chart_type,
        "title": plan.title,
        "x_key": plan.x_key,
        "y_keys": list(plan.y_keys),
        "error": None,
        "refused": False,
    }


def run_query(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    configurable = config.get("configurable") or {}
    session = configurable["session"]
    try:
        rows = run_select(session, state.get("sql") or "")
    except SqlRejected as exc:
        return {"error": str(exc), "rows": [], "refused": not exc.repair}
    problem = _chart_problem(state, rows)
    if problem is not None:
        return {"error": problem, "rows": [], "refused": False}
    return {"rows": rows, "error": None, "refused": False}


def explain(state: AgentState) -> dict[str, str]:
    answer = b.ExplainRows(
        question=state["question"],
        rows_json=json.dumps(state.get("rows") or []),
        plot_required=bool(state.get("plot_required")),
    )
    return {"answer": answer}


def give_up(state: AgentState) -> dict[str, Any]:
    return {
        "answer": COULD_NOT_QUERY,
        "plot_required": False,
        "rows": [],
        "question": state.get("question", ""),
    }


def after_run(state: AgentState) -> str:
    if state.get("refused"):
        return "give_up"
    if state.get("error"):
        if int(state.get("repairs") or 0) >= 2:
            return "give_up"
        return "write_query"
    return "explain"


def _chart_problem(state: AgentState, rows: list[dict[str, str]]) -> str | None:
    if not state.get("plot_required"):
        return None
    if not rows:
        return "The query returned no rows."
    x_key = state.get("x_key")
    y_keys = state.get("y_keys") or []
    if not x_key or not y_keys:
        return "A plot needs x_key and y_keys that match the SELECT aliases."
    columns = set(rows[0])
    missing = [key for key in [x_key, *y_keys] if key not in columns]
    if missing:
        return f"Result is missing columns: {', '.join(missing)}."
    return None
