"""Run one question against the shipping book."""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from sqlmodel import Session

from src.agent.graph import graph
from src.agent.tools import parse_tool_payload
from src.schemas.questions.question import QuestionChart, QuestionExplanation, QuestionResponse

COULD_NOT_QUERY = "The question could not be queried."


def run_question(session: Session, question: str) -> QuestionResponse:
    result = graph.invoke(
        {
            "messages": [HumanMessage(content=question)],
            "nudge_count": 0,
            "steps": 0,
        },
        config={"configurable": {"session": session}},
    )
    return response_from_state(result)


def response_from_state(result: dict[str, Any]) -> QuestionResponse:
    messages = result.get("messages") or []
    charts: list[QuestionChart] = []
    explanations: list[QuestionExplanation] = []
    for message in messages:
        if not isinstance(message, ToolMessage):
            continue
        payload = parse_tool_payload(message.content)
        if payload is None or payload.get("ok") is not True:
            continue
        explanation = explanation_from_payload(payload)
        if explanation is not None:
            explanations.append(explanation)
        chart = chart_from_payload(payload.get("chart"))
        if chart is not None:
            charts.append(chart)
    answer = last_ai_text(messages) or COULD_NOT_QUERY
    explanation = rollup_explanation(explanations)
    return QuestionResponse(
        answer=answer,
        plot_required=bool(charts),
        chart=charts[0] if charts else None,
        charts=charts,
        explanation=explanation,
        explanations=explanations,
    )


def last_ai_text(messages: list[Any]) -> str:
    for message in reversed(messages):
        if not isinstance(message, AIMessage):
            continue
        if message.tool_calls:
            continue
        content = message.content
        if isinstance(content, str) and content.strip():
            return content.strip()
        if isinstance(content, list):
            parts = [
                str(block.get("text", ""))
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            text = "".join(parts).strip()
            if text:
                return text
    return ""


def explanation_from_payload(payload: dict[str, Any]) -> QuestionExplanation | None:
    kind = payload.get("kind")
    if kind not in {"query", "forecast"}:
        return None
    plan = payload.get("sql") if kind == "query" else payload.get("method")
    return QuestionExplanation(
        tool=kind,
        filters=_strings(payload.get("filters")),
        metrics=_strings(payload.get("metrics")),
        dimensions=_strings(payload.get("dimensions")),
        plan=plan if isinstance(plan, str) else "",
        rows=_rows(payload.get("rows")),
    )


def rollup_explanation(explanations: list[QuestionExplanation]) -> QuestionExplanation:
    if not explanations:
        return QuestionExplanation()
    if len(explanations) == 1:
        return explanations[0]
    kinds = {item.tool for item in explanations if item.tool in {"query", "forecast"}}
    tool: Literal["query", "forecast", "mixed"] = "mixed"
    if kinds == {"query"}:
        tool = "query"
    elif kinds == {"forecast"}:
        tool = "forecast"
    return QuestionExplanation(
        tool=tool,
        filters=_unique(item for block in explanations for item in block.filters),
        metrics=_unique(item for block in explanations for item in block.metrics),
        dimensions=_unique(item for block in explanations for item in block.dimensions),
        plan=" | ".join(block.plan for block in explanations if block.plan),
        rows=[row for block in explanations for row in block.rows][:50],
    )


def chart_from_payload(value: object) -> QuestionChart | None:
    if not isinstance(value, dict):
        return None
    chart_type = value.get("type")
    x_key = value.get("x_key")
    y_keys = value.get("y_keys")
    rows = value.get("rows")
    title = value.get("title")
    if chart_type not in {"bar", "line", "area", "pie", "scatter"}:
        return None
    if not isinstance(x_key, str) or not x_key:
        return None
    if not isinstance(y_keys, list) or not all(isinstance(key, str) and key for key in y_keys):
        return None
    if not isinstance(rows, list) or not rows:
        return None
    return QuestionChart(
        type=chart_type,
        title=title if isinstance(title, str) and title else "Result",
        x_key=x_key,
        y_keys=list(y_keys),
        rows=[row for row in rows if isinstance(row, dict)],
    )


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _rows(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    rows: list[dict[str, str]] = []
    for row in value:
        if isinstance(row, dict):
            rows.append({str(key): "" if cell is None else str(cell) for key, cell in row.items()})
    return rows


def _unique(values: Any) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in values:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered
