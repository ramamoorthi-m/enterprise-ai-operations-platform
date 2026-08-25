import pytest

from langgraph.graph import StateGraph, END
from langgraph.types import Command, interrupt

from app.state.state import EnterpriseState


def human_review_test_node(state: EnterpriseState):

    decision = interrupt({
        "type": "human_review",
        "reason": state.get("human_review_reason", ""),
        "confidence": state.get("confidence", 0.0),
    })

    return {
        "human_review_decision": decision
    }


def route_after_review(state: EnterpriseState):

    decision = state.get("human_review_decision")

    if decision == "approve":
        return "approved"

    if decision == "retry":
        return "retry"

    return "rejected"


def build_test_graph():

    builder = StateGraph(EnterpriseState)

    builder.add_node(
        "human_review",
        human_review_test_node,
    )

    builder.add_node(
        "approved",
        lambda state: {
            "status": "approved"
        },
    )

    builder.add_node(
        "retry",
        lambda state: {
            "status": "retry"
        },
    )

    builder.add_node(
        "rejected",
        lambda state: {
            "status": "rejected"
        },
    )

    builder.set_entry_point("human_review")

    builder.add_conditional_edges(
        "human_review",
        route_after_review,
        {
            "approved": "approved",
            "retry": "retry",
            "rejected": "rejected",
        },
    )

    builder.add_edge("approved", END)
    builder.add_edge("retry", END)
    builder.add_edge("rejected", END)

    from langgraph.checkpoint.memory import MemorySaver

    return builder.compile(
        checkpointer=MemorySaver()
    )


@pytest.mark.asyncio
async def test_human_review_approve():

    graph = build_test_graph()

    config = {
        "configurable": {
            "thread_id": "hitl-approve-test",
        }
    }

    state = {
        "confidence": 0.45,
        "human_review_reason": "Evidence requires human judgment.",
    }

    result = await graph.ainvoke(
        state,
        config=config,
    )

    assert result["__interrupt__"]

    result = await graph.ainvoke(
        Command(resume="approve"),
        config=config,
    )

    assert result["human_review_decision"] == "approve"
    assert result["status"] == "approved"