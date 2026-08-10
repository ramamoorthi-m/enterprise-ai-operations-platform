from app.llm.client import GeminiClient
from app.state.plan import InvestigationPlan
from app.state.state import EnterpriseState


def planner(state: EnterpriseState):
    """Generate an investigation plan using Gemini."""

    user_query = state["user_query"]

    prompt = f"""
You are an enterprise investigation planning agent.

Analyze the user's request and create an investigation plan.

Available enterprise systems:

1. GitHub
   - repositories
   - pull requests
   - commits
   - issues

2. Jira
   - projects
   - tickets
   - sprint status
   - blockers
   - priorities

Rules:

- Only use GitHub and Jira as investigation sources.
- Do not invent information.
- Identify only the sources actually needed.
- Create concrete investigation tasks.
- Every task must specify either github or jira.
- Focus on collecting evidence.
- Do not answer the user's question.
- Keep the plan concise.

User request:

{user_query}
"""

    llm = GeminiClient()

    investigation_plan: InvestigationPlan = llm.generate_structured(
        prompt=prompt,
        response_schema=InvestigationPlan,
    )

    return {
        "project":
            investigation_plan.project,
        "plan": [
            task.description
            for task in investigation_plan.tasks
        ],
        "required_sources": investigation_plan.required_sources,
        "status": "planning_completed",
    }