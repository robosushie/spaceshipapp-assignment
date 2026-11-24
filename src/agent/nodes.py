"""Graph nodes that invoke LangGraph tools for each step."""

from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableConfig

from src.agent import tools
from src.agent.schema import BOOK_AS_OF
from src.agent.state import AgentState

COULD_NOT_QUERY = "The question could not be queried."


def choose_tool(state: AgentState) -> dict[str, Any]:
    return tools.choose_tool.invoke(
        {
            "question": state["question"],
            "as_of": state.get("as_of") or BOOK_AS_OF,
        }
    )


def route_tool(state: AgentState) -> str:
    return "forecast" if state.get("tool") == "forecast" else "write_query"


def forecast(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    session = _session(config)
    return tools.forecast_demand.invoke(
        {
            "horizon_months": int(state.get("horizon_months") or 4),
            "sku": state.get("sku") or "",
            "forecast_method": state.get("forecast_method") or "auto",
            "start_month": state.get("start_month") or "",
            "end_month": state.get("end_month") or "",
            "session": session,
        }
    )


def write_query(state: AgentState) -> dict[str, Any]:
    error = state.get("error") or ""
    repairs = state.get("repairs", 0)
    if error:
        repairs += 1
    plan = tools.write_query.invoke(
        {
            "question": state["question"],
            "schema_ddl": state["schema_ddl"],
            "as_of": state.get("as_of") or BOOK_AS_OF,
            "previous_sql": state.get("sql") or "",
            "error": error,
        }
    )
    return {"repairs": repairs, **plan}


def run_query(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    session = _session(config)
    return tools.run_sql.invoke(
        {
            "sql": state.get("sql") or "",
            "plot_required": bool(state.get("plot_required")),
            "x_key": state.get("x_key") or "",
            "y_keys": list(state.get("y_keys") or []),
            "session": session,
        }
    )


def explain(state: AgentState) -> dict[str, str]:
    return tools.explain_rows.invoke(
        {
            "question": state["question"],
            "rows_json": tools.rows_to_json(state.get("rows")),
            "plot_required": bool(state.get("plot_required")),
        }
    )


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


def _session(config: RunnableConfig) -> Any:
    configurable = config.get("configurable") or {}
    return configurable["session"]
