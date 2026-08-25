from langgraph.graph import StateGraph, END

from app.state.state import EnterpriseState
from app.workflow.planner import planner
from app.workflow.investigator import investigator
from app.workflow.aggregator import aggregator
from app.workflow.analysis import analysis
from app.workflow.evaluator import evaluator
from app.workflow.router import (
    route_after_evaluation,
    route_after_human_review,
)
from app.workflow.retry import retry_handler
from app.workflow.report_generator import report_generator
from app.workflow.human_review import human_review
from langgraph.checkpoint.memory import MemorySaver
from app.guardrails.input_guardrail import validate_input


builder = StateGraph(EnterpriseState)

builder.add_node("input_guardrail", validate_input)
builder.add_node("planner", planner)
builder.add_node("investigator", investigator)
builder.add_node("aggregator", aggregator)
builder.add_node("analysis", analysis)
builder.add_node("evaluator", evaluator)
builder.add_node("report_generator", report_generator)
builder.add_node("retry_handler", retry_handler)
builder.add_node("human_review", human_review)

builder.set_entry_point("input_guardrail")
builder.add_edge("input_guardrail","planner")
builder.add_edge("planner", "investigator")
builder.add_edge("investigator", "aggregator")
builder.add_edge("aggregator", "analysis")
builder.add_edge("analysis", "evaluator")



builder.add_conditional_edges(
    "evaluator",
    route_after_evaluation,
    {
        "success": "report_generator",
        "retry": "retry_handler",
        "human_review": "human_review",
        "failed": END
    },
)

builder.add_conditional_edges(
    "human_review",
    route_after_human_review,
    {
        "success": "report_generator",
        "retry": "retry_handler",
        "failed": END
    },
)



builder.add_edge("report_generator", END)
builder.add_edge("retry_handler", "planner")

checkpointer = MemorySaver()

graph = builder.compile(checkpointer=checkpointer)