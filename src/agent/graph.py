from langgraph.graph import END, START, StateGraph

from src.agent.nodes import (
    after_run,
    choose_tool,
    explain,
    forecast,
    give_up,
    route_tool,
    run_query,
    write_query,
)
from src.agent.state import AgentState

builder = StateGraph(AgentState)
builder.add_node("choose_tool", choose_tool)
builder.add_node("forecast_demand", forecast)
builder.add_node("write_query", write_query)
builder.add_node("run_sql", run_query)
builder.add_node("explain_rows", explain)
builder.add_node("give_up", give_up)
builder.add_edge(START, "choose_tool")
builder.add_conditional_edges(
    "choose_tool",
    route_tool,
    {"write_query": "write_query", "forecast": "forecast_demand"},
)
builder.add_edge("write_query", "run_sql")
builder.add_conditional_edges(
    "run_sql",
    after_run,
    {"write_query": "write_query", "explain": "explain_rows", "give_up": "give_up"},
)
builder.add_edge("explain_rows", END)
builder.add_edge("give_up", END)
builder.add_edge("forecast_demand", END)
graph = builder.compile()
