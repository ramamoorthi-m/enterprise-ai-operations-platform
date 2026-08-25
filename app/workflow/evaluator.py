from app.agents.evaluator import EvaluatorAgent
from app.llm.groq_client import GroqClient


def evaluator(state):

    llm = GroqClient(
        model="openai/gpt-oss-120b"
    )

    agent = EvaluatorAgent(
        llm=llm
    )

    result = agent.evaluate(state)

    return {
        "evaluation_passed": result["evaluation_passed"],
        "confidence": result["confidence"],
        "evaluation_reason": result["reason"],
        "human_review_reason": result["reason"],
        "evidence_sufficient": result[
            "evidence_sufficient"
        ],
        "retry_required": result["retry_required"],
        "human_review_required": result[
            "human_review_required"
        ],
        "status": (
            "evaluation_passed"
            if result["evaluation_passed"]
            else "evaluation_failed"
        ),
    }