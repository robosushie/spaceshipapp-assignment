"""Run one question against the shipping book."""

from __future__ import annotations

from sqlmodel import Session

from src.agent.graph import graph
from src.agent.schema import BOOK_AS_OF, logistics_ddl
from src.schemas.questions.question import QuestionChart, QuestionExplanation, QuestionResponse


def run_question(session: Session, question: str) -> QuestionResponse:
    result = graph.invoke(
        {
            "question": question,
            "schema_ddl": logistics_ddl(),
            "as_of": BOOK_AS_OF,
            "repairs": 0,
        },
        config={"configurable": {"session": session}},
    )
    plot_required = bool(result.get("plot_required"))
    chart = _chart(result) if plot_required else None
    if chart is None:
        plot_required = False
    return QuestionResponse(
        answer=str(result.get("answer") or "The question could not be queried."),
        plot_required=plot_required,
        chart=chart,
        explanation=_explanation(result),
    )


def _explanation(result: dict[str, object]) -> QuestionExplanation:
    tool = "forecast" if result.get("tool") == "forecast" else "query"
    plan = result.get("method") if tool == "forecast" else result.get("sql")
    return QuestionExplanation(
        tool=tool,
        filters=_strings(result.get("filters")),
        metrics=_strings(result.get("metrics")),
        dimensions=_strings(result.get("dimensions")),
        plan=plan if isinstance(plan, str) else "",
        rows=_rows(result.get("rows")),
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


def _chart(result: dict[str, object]) -> QuestionChart | None:
    chart_type = result.get("chart_type")
    x_key = result.get("x_key")
    y_keys = result.get("y_keys")
    rows = result.get("rows")
    title = result.get("title")
    if (
        chart_type not in {"bar", "line", "area", "pie", "scatter"}
        or not isinstance(x_key, str)
        or not x_key
    ):
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
