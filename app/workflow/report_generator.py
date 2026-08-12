from app.agents.report_generator import ReportGeneratorAgent
from app.state.state import EnterpriseState


agent = ReportGeneratorAgent()


def report_generator(state: EnterpriseState):

    result = agent.generate(state)

    return result