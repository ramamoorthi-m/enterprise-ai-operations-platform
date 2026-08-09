from langgraph.graph import StateGraph, END

from app.state.state import EnterpriseState
from app.workflow.planner import planner
from app.workflow.github_collector import github_collector
from app.workflow.jira_collector import jira_collector
from app.workflow.router import route_after_planner
from app.workflow.router import route_after_github
from app.workflow.aggregator import aggregator
from app.workflow.evaluator import evaluator
from app.workflow.router import route_after_evaluation
from app.workflow.retry import retry_handler
from app.workflow.report_generator import report_generator


builder = StateGraph(EnterpriseState)

builder.add_node("planner", planner)
builder.add_node("github_collector", github_collector)
builder.add_node("jira_collector", jira_collector)
builder.add_node("aggregator", aggregator)
builder.add_node("evaluator", evaluator)
builder.add_node("retry_handler", retry_handler)
builder.add_node("report_generator", report_generator)

builder.set_entry_point("planner")

builder.add_conditional_edges(
    "planner",
    route_after_planner,
    {
        "github": "github_collector",
        "jira": "jira_collector",
    },
)

builder.add_conditional_edges(
    "github_collector",
    route_after_github,
    {
        "jira": "jira_collector",
        "aggregator": "aggregator",
    },
)

builder.add_conditional_edges(
    "evaluator",
    route_after_evaluation,
    {
        "success": "report_generator",
        "retry": "retry_handler",
        "failed": END
    },
)

builder.add_edge("jira_collector", "aggregator")
builder.add_edge("aggregator", "evaluator")
builder.add_edge("report_generator", END)
builder.add_edge("retry_handler", "planner")
graph = builder.compile()