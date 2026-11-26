"""Run the questions named in the assignment and the logistics spec."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import pytest
from sqlalchemy import func
from sqlmodel import Session, select

from scripts.bootstrap.run import load_json
from src.agent.answer import run_question
from src.lib.db import engine
from src.models.orders.order import Order

# "SKU X" is the spec's placeholder. STICKER-0063 is the book SKU with the most units.
PROMPTS = (
    ("query", "Show delayed orders by week for the last 3 months", True),
    ("query", "Which carrier has the highest delay rate?", False),
    ("query", "How many orders were delivered late last month?", False),
    ("query", "Show delayed orders by week", True),
    ("forecast", "Predict demand for SKU X for the next 4 months", False),
    ("forecast", "Predict demand for SKU STICKER-0063 for the next 4 months", True),
    ("forecast", "How much inventory should I plan?", True),
    (
        "mixed",
        "Show delayed orders by week and forecast STICKER-0063 for the next 4 months",
        True,
    ),
)


@dataclass(frozen=True)
class PromptResult:
    question: str
    tool: str
    answer: str
    chart_type: str | None
    rows: list[dict[str, str]]
    chart_count: int


def test_spec_prompts_against_the_book() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        pytest.skip("ANTHROPIC_API_KEY is not set")
    load_json()
    with Session(engine) as session:
        orders = session.exec(select(func.count()).select_from(Order)).one()
        assert orders == 400
        results = [_ask(session, question, tool, plot) for tool, question, plot in PROMPTS]
    report = [
        {
            "question": item.question,
            "tool": item.tool,
            "answer": item.answer,
            "chart_type": item.chart_type,
            "chart_count": item.chart_count,
            "rows": item.rows,
        }
        for item in results
    ]
    print(json.dumps(report, indent=2))


def _ask(session: Session, question: str, tool: str, plot: bool) -> PromptResult:
    result = run_question(session, question)
    assert result.answer.strip()
    assert result.answer != "The question could not be queried."
    if tool == "mixed":
        kinds = {item.tool for item in result.explanations}
        assert "query" in kinds
        assert "forecast" in kinds
        assert result.explanation.tool == "mixed"
        assert len(result.charts) >= 2
    else:
        assert result.explanation.tool == tool
    chart_type = None
    rows: list[dict[str, str]] = []
    if plot:
        assert result.charts or result.chart is not None
        chart = result.charts[0] if result.charts else result.chart
        assert chart is not None
        chart_type = chart.type
        rows = chart.rows
        assert rows
    elif result.chart is not None:
        chart_type = result.chart.type
        rows = result.chart.rows
    if tool == "forecast" and result.chart is not None:
        assert result.chart.type == "line"
        assert result.chart.y_keys == ["history", "forecast"]
    return PromptResult(
        question,
        result.explanation.tool,
        result.answer,
        chart_type,
        rows,
        len(result.charts),
    )
