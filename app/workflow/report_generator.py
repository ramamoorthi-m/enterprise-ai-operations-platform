from app.agents.report_generator import ReportGeneratorAgent
from app.guardrails.output_guardrail import (
    OutputGuardrailError,
    validate_report_output,
)
from app.state.state import EnterpriseState


agent = ReportGeneratorAgent()


def report_generator(state: EnterpriseState):

    result = agent.generate(state)

    report = result.get("report", "")

    try:
        validate_report_output(
            report=report,
            state=state,
        )

    except OutputGuardrailError as exc:
        return {
            "report": "",
            "status": "output_guardrail_failed",
            "errors": [
                *state.get("errors", []),
                str(exc),
            ],
        }

    return result