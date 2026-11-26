"""LangGraph compute tools and ReAct response collection."""

from __future__ import annotations

import json
from typing import Any, cast

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from sqlmodel import Session

from src.agent.answer import response_from_state, run_question
from src.agent.nodes import has_compute_result, route_after_agent
from src.agent.tools import TOOLS, forecast_demand, parse_tool_payload, query_book
from src.schemas.questions.question import QuestionExplanation


def test_tools_are_registered_by_name() -> None:
    names = {tool.name for tool in TOOLS}
    assert names == {"query_book", "forecast_demand"}


def test_compute_tools_keep_runtime_out_of_schema() -> None:
    assert "runtime" not in query_book.args
    assert "question" in query_book.args
    assert "runtime" not in forecast_demand.args
    assert "horizon_months" in forecast_demand.args


def test_has_compute_result_requires_ok_tool_payload() -> None:
    failed = [ToolMessage(content='{"ok": false, "kind": "query"}', tool_call_id="1")]
    assert has_compute_result(failed) is False
    ok = [ToolMessage(content='{"ok": true, "kind": "query", "rows": []}', tool_call_id="1")]
    assert has_compute_result(ok) is True


def test_route_after_agent_prefers_tools_then_end() -> None:
    with_calls = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[{"name": "query_book", "args": {"question": "x"}, "id": "1"}],
            )
        ],
        "nudge_count": 0,
        "steps": 1,
    }
    assert route_after_agent(with_calls) == "tools"  # type: ignore[arg-type]
    done = {
        "messages": [
            ToolMessage(
                content=json.dumps({"ok": True, "kind": "query", "rows": [{"n": "1"}]}),
                tool_call_id="1",
            ),
            AIMessage(content="One delayed order."),
        ],
        "nudge_count": 0,
        "steps": 2,
    }
    assert route_after_agent(done) == "end"  # type: ignore[arg-type]
    empty = {
        "messages": [AIMessage(content="I guess 55.")],
        "nudge_count": 0,
        "steps": 1,
    }
    assert route_after_agent(empty) == "nudge"  # type: ignore[arg-type]
    nudged = {
        "messages": [AIMessage(content="Still guessing.")],
        "nudge_count": 1,
        "steps": 2,
    }
    assert route_after_agent(nudged) == "give_up"  # type: ignore[arg-type]


def test_response_from_state_collects_multiple_charts() -> None:
    query_payload = {
        "ok": True,
        "kind": "query",
        "sql": "SELECT week, delayed FROM t",
        "filters": ["delayed"],
        "metrics": ["orders"],
        "dimensions": ["week"],
        "rows": [{"week": "2025-10-01", "delayed": "3"}],
        "chart": {
            "type": "line",
            "title": "Delayed by week",
            "x_key": "week",
            "y_keys": ["delayed"],
            "rows": [{"week": "2025-10-01", "delayed": "3"}],
        },
    }
    forecast_payload = {
        "ok": True,
        "kind": "forecast",
        "method": "three-month moving average",
        "filters": ["SKU STICKER-0063"],
        "metrics": ["quantity"],
        "dimensions": ["month"],
        "rows": [{"month": "2026-01", "history": "", "forecast": "10"}],
        "chart": {
            "type": "line",
            "title": "Demand",
            "x_key": "month",
            "y_keys": ["history", "forecast"],
            "rows": [{"month": "2026-01", "history": "", "forecast": "10"}],
        },
    }
    result = response_from_state(
        {
            "messages": [
                HumanMessage(content="plot delays and forecast stickers"),
                AIMessage(
                    content="",
                    tool_calls=[{"name": "query_book", "args": {}, "id": "1"}],
                ),
                ToolMessage(content=json.dumps(query_payload), tool_call_id="1"),
                AIMessage(
                    content="",
                    tool_calls=[{"name": "forecast_demand", "args": {}, "id": "2"}],
                ),
                ToolMessage(content=json.dumps(forecast_payload), tool_call_id="2"),
                AIMessage(content="Delays rose; plan about 10 units."),
            ]
        }
    )
    assert result.answer == "Delays rose; plan about 10 units."
    assert result.plot_required is True
    assert len(result.charts) == 2
    assert result.chart is not None
    assert result.chart.title == "Delayed by week"
    assert len(result.explanations) == 2
    assert result.explanation.tool == "mixed"
    assert "SELECT week" in result.explanation.plan
    assert "moving average" in result.explanation.plan


def test_run_question_keeps_explanation(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "ok": True,
        "kind": "query",
        "sql": "SELECT 55 AS delayed",
        "filters": ["status delayed"],
        "metrics": ["orders"],
        "dimensions": [],
        "rows": [{"delayed": "55"}],
        "chart": None,
    }

    def invoke(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        assert state["messages"][0].content == "how many delayed"
        assert config is not None
        return {
            "messages": [
                state["messages"][0],
                ToolMessage(content=json.dumps(payload), tool_call_id="1"),
                AIMessage(content="55 delayed orders."),
            ]
        }

    monkeypatch.setattr("src.agent.answer.graph.invoke", invoke)
    session = cast(Session, object())
    response = run_question(session, "how many delayed")
    assert response.answer == "55 delayed orders."
    assert response.charts == []
    assert response.explanation == QuestionExplanation(
        tool="query",
        filters=["status delayed"],
        metrics=["orders"],
        dimensions=[],
        plan="SELECT 55 AS delayed",
        rows=[{"delayed": "55"}],
    )


def test_parse_tool_payload_rejects_junk() -> None:
    assert parse_tool_payload("not-json") is None
    assert parse_tool_payload('{"ok": true}') == {"ok": True}
