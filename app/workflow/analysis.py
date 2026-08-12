from app.agents.analysis import AnalysisAgent
from app.llm.client import GeminiClient
from app.state.state import EnterpriseState


def analysis(state: EnterpriseState):
    """LangGraph node that runs the AnalysisAgent."""

    llm = GeminiClient()

    agent = AnalysisAgent(
        llm=llm,
    )

    result = agent.analyze(
        state=dict(state),
    )

    return {
        "analysis": result.model_dump(),
        "confidence": result.confidence,
        "status": "analysis_completed",
    }