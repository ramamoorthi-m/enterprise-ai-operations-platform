from langgraph.graph import StateGraph, END

from app.state.state import EnterpriseState
from app.workflow.planner import planner


builder = StateGraph(EnterpriseState)

builder.add_node("planner", planner)

builder.set_entry_point("planner")

builder.add_edge("planner", END)

graph = builder.compile()