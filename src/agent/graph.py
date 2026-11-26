from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.agent.nodes import agent, give_up, nudge, route_after_agent
from src.agent.state import AgentState
from src.agent.tools import TOOLS

builder = StateGraph(AgentState)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_node("nudge", nudge)
builder.add_node("give_up", give_up)
builder.add_edge(START, "agent")
builder.add_conditional_edges(
    "agent",
    route_after_agent,
    {"tools": "tools", "nudge": "nudge", "give_up": "give_up", "end": END},
)
builder.add_edge("tools", "agent")
builder.add_edge("nudge", "agent")
builder.add_edge("give_up", END)
graph = builder.compile()
