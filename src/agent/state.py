from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    question: str
    schema_ddl: str
    as_of: str
    repairs: int
    sql: str
    plot_required: bool
    chart_type: str | None
    title: str | None
    x_key: str | None
    y_keys: list[str]
    error: str | None
    refused: bool
    rows: list[dict[str, str]]
    answer: str
    plan: Any
    tool: str
    sku: str | None
    horizon_months: int
    filters: list[str]
    metrics: list[str]
    dimensions: list[str]
    forecast_method: str
    method: str
