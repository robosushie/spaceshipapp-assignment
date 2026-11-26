"""ReAct agent nodes: model step, nudge, and give-up."""

from __future__ import annotations

from typing import Any, Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from src.agent.state import AgentState
from src.agent.tools import TOOLS, parse_tool_payload
from src.lib.config import get_settings

COULD_NOT_QUERY = "The question could not be queried."
MAX_STEPS = 8
SYSTEM_PROMPT = """You are the Spaceship desk agent for one shipping book that ends on 2025-12-30.
Treat that date as today.

You have two compute tools only:
- query_book: analytics on past orders (counts, filters, trends, charts).
- forecast_demand: demand and inventory projections from monthly quantity.

Rules:
- Call a compute tool for every factual claim.
  Never invent row values, SQL results, or forecast numbers.
- You may call either tool multiple times when the user needs several metrics or plots.
- You may mix query_book and forecast_demand in one turn or across turns.
- When a tool returns a chart object, keep that plot; when chart is null, do not invent one.
- After tools succeed, write a short clear answer from the tool results only.
- If a tool returns ok=false, call again with clearer args, or say you could not answer.
"""


def agent(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    steps = int(state.get("steps") or 0)
    if steps >= MAX_STEPS:
        return {"messages": [AIMessage(content=COULD_NOT_QUERY)], "steps": steps}
    model = _model().bind_tools(TOOLS)
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    response = model.invoke(messages, config=config)
    return {"messages": [response], "steps": steps + 1}


def route_after_agent(state: AgentState) -> Literal["tools", "nudge", "give_up", "end"]:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    if has_compute_result(state["messages"]):
        return "end"
    if int(state.get("nudge_count") or 0) < 1:
        return "nudge"
    return "give_up"


def nudge(state: AgentState) -> dict[str, Any]:
    return {
        "messages": [
            HumanMessage(
                content=(
                    "You must call query_book or forecast_demand before answering. "
                    "Do not invent numbers."
                )
            )
        ],
        "nudge_count": int(state.get("nudge_count") or 0) + 1,
    }


def give_up(state: AgentState) -> dict[str, Any]:
    _ = state
    return {"messages": [AIMessage(content=COULD_NOT_QUERY)]}


def has_compute_result(messages: list[Any]) -> bool:
    for message in messages:
        if not isinstance(message, ToolMessage):
            continue
        payload = parse_tool_payload(message.content)
        if payload is not None and payload.get("ok") is True:
            return True
    return False


def _model() -> ChatAnthropic:
    settings = get_settings()
    return ChatAnthropic(
        model="claude-sonnet-5-5",
        api_key=settings.anthropic_api_key,
    )
