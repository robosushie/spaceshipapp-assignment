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


class QuestionExplanation(BaseModel):
    tool: Literal["query", "forecast", "mixed"] = "query"
    filters: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    plan: str = ""
    rows: list[dict[str, str]] = Field(default_factory=list)


class QuestionResponse(BaseModel):
    answer: str
    plot_required: bool
    chart: QuestionChart | None = None
    charts: list[QuestionChart] = Field(default_factory=list)
    explanation: QuestionExplanation = Field(default_factory=QuestionExplanation)
    explanations: list[QuestionExplanation] = Field(default_factory=list)
