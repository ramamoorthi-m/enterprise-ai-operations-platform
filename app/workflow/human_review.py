from langgraph.types import interrupt

from app.state.state import EnterpriseState


def human_review(state: EnterpriseState):
    """
    Pause the investigation for human review.
    """

    decision = interrupt(
        {
            "type": "human_review",
            "reason": state.get("human_review_reason", ""),
            "confidence": state.get("confidence"),
            "findings": state.get("findings", []),
            "analysis": state.get("analysis", {}),
        }
    )

    return {
        "human_review_decision": decision
    }