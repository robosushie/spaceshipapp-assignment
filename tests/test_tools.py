"""LangGraph tools for the question graph."""

from __future__ import annotations

from typing import Any, cast

import pytest
from sqlmodel import Session

from src.agent.answer import run_question
from src.agent.nodes import after_run, give_up
from src.agent.tools import TOOLS, choose_tool, forecast_demand, run_sql, write_query
from src.schemas.questions.question import QuestionExplanation


def test_tools_are_registered_by_name() -> None:
    names = {tool.name for tool in TOOLS}
    assert names == {
        "choose_tool",
        "write_query",
        "run_sql",
        "explain_rows",
        "forecast_demand",
    }


def test_baml_tools_expose_question_args_not_session() -> None:
    assert "session" not in choose_tool.args
    assert "question" in choose_tool.args
    assert "as_of" in choose_tool.args
    assert "session" not in write_query.args
    assert "question" in write_query.args
    assert "schema_ddl" in write_query.args


def test_compute_tools_keep_session_out_of_schema() -> None:
    assert "session" not in run_sql.args
    assert "sql" in run_sql.args
    assert "session" not in forecast_demand.args
    assert "horizon_months" in forecast_demand.args


def test_after_run_routes_repair_explain_and_give_up() -> None:
    assert after_run({"refused": True}) == "give_up"
    assert after_run({"error": "bad", "repairs": 1}) == "write_query"
    assert after_run({"error": "bad", "repairs": 2}) == "give_up"
    assert after_run({"rows": [{"n": "1"}]}) == "explain"


def test_give_up_clears_the_plot() -> None:
    result = give_up({"question": "how many"})
    assert result["answer"] == "The question could not be queried."
    assert result["plot_required"] is False
    assert result["rows"] == []


def test_run_question_keeps_explanation(monkeypatch: pytest.MonkeyPatch) -> None:
    def invoke(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        assert state["question"] == "how many delayed"
        assert config is not None
        return {
            "tool": "query",
            "answer": "55 delayed orders.",
            "plot_required": False,
            "sql": "SELECT 55 AS delayed",
            "filters": ["status delayed"],
            "metrics": ["orders"],
            "dimensions": [],
            "rows": [{"delayed": "55"}],
        }

    monkeypatch.setattr("src.agent.answer.graph.invoke", invoke)
    session = cast(Session, object())
    response = run_question(session, "how many delayed")
    assert response.answer == "55 delayed orders."
    assert response.explanation == QuestionExplanation(
        tool="query",
        filters=["status delayed"],
        metrics=["orders"],
        dimensions=[],
        plan="SELECT 55 AS delayed",
        rows=[{"delayed": "55"}],
    )
