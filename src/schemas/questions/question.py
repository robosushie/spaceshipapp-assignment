from typing import Literal

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class QuestionChart(BaseModel):
    type: Literal["bar", "line", "area", "pie", "scatter"]
    title: str
    x_key: str
    y_keys: list[str]
    rows: list[dict[str, str]]


class QuestionResponse(BaseModel):
    answer: str
    plot_required: bool
    chart: QuestionChart | None = None
