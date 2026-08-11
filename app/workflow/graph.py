from langgraph.graph import StateGraph, END

from app.state.state import EnterpriseState
from app.workflow.planner import planner
from app.workflow.investigator import investigator
from app.workflow.aggregator import aggregator
from app.workflow.evaluator import evaluator
from app.workflow.router import route_after_evaluation
from app.workflow.retry import retry_handler
from app.workflow.report_generator import report_generator


builder = StateGraph(EnterpriseState)

builder.add_node("planner", planner)
builder.add_node("investigator", investigator)
builder.add_node("aggregator", aggregator)
builder.add_node("evaluator", evaluator)
builder.add_node("report_generator", report_generator)
builder.add_node("retry_handler", retry_handler)

builder.set_entry_point("planner")
builder.add_edge("planner", "investigator")
builder.add_edge("investigator", "aggregator")
builder.add_edge("aggregator", "evaluator")



builder.add_conditional_edges(
    "evaluator",
    route_after_evaluation,
    {
        "success": "report_generator",
        "retry": "retry_handler",
        "failed": END
    },
)

builder.add_edge("report_generator", END)
builder.add_edge("retry_handler", "planner")
graph = builder.compile()