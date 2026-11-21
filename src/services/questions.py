import logging

from fastapi import HTTPException
from sqlmodel import Session

from src.agent.graph import graph
from src.agent.schema import BOOK_AS_OF, logistics_ddl
from src.lib.config import get_settings
from src.schemas import QuestionChart, QuestionResponse

logger = logging.getLogger("spaceship.questions")
_UNAVAILABLE = "Questions are unavailable."


def ask_question(session: Session, question: str) -> QuestionResponse:
    if not get_settings().anthropic_api_key.strip():
        raise HTTPException(status_code=503, detail=_UNAVAILABLE)
    try:
        result = graph.invoke(
            {
                "question": question,
                "schema_ddl": logistics_ddl(),
                "as_of": BOOK_AS_OF,
                "repairs": 0,
            },
            config={"configurable": {"session": session}},
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("question graph failed")
        raise HTTPException(status_code=503, detail=_UNAVAILABLE) from None

    plot_required = bool(result.get("plot_required"))
    chart = _chart(result) if plot_required else None
    if chart is None:
        plot_required = False
    return QuestionResponse(
        answer=str(result.get("answer") or "The question could not be queried."),
        plot_required=plot_required,
        chart=chart,
    )


def _chart(result: dict[str, object]) -> QuestionChart | None:
    chart_type = result.get("chart_type")
    x_key = result.get("x_key")
    y_keys = result.get("y_keys")
    rows = result.get("rows")
    title = result.get("title")
    if chart_type not in {"bar", "line", "area", "pie", "scatter"} or not isinstance(x_key, str) or not x_key:
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
