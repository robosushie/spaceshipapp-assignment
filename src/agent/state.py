from typing import NotRequired

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    nudge_count: NotRequired[int]
    steps: NotRequired[int]
