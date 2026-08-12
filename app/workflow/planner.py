from app.llm.client import GeminiClient
from app.state.plan import InvestigationPlan
from app.state.state import EnterpriseState


def planner(state: EnterpriseState):
    """Generate or revise an investigation plan using Gemini."""

    user_query = state["user_query"]

    retry_count = state.get("retry_count", 0)

    previous_plan = state.get("plan", [])
    previous_findings = state.get("findings", [])
    previous_analysis = state.get("analysis", {})
    previous_errors = state.get("errors", [])

    is_retry = retry_count > 0

    if is_retry:
        retry_context = f"""
This is investigation retry attempt {retry_count + 1}.

You must review the previous investigation before creating the new plan.

Previous investigation plan:
{previous_plan}

Previous findings:
{previous_findings}

Previous analysis:
{previous_analysis}

Previous errors:
{previous_errors}

Retry rules:

- Do NOT blindly repeat the previous investigation.
- Identify the evidence gaps or weaknesses from the previous attempt.
- Create a revised investigation plan that specifically addresses those gaps.
- Reuse previous sources only when they can provide additional or better evidence.
- Do not invent information.
- Do not create tasks for evidence that cannot reasonably be obtained from GitHub or Jira.
- Keep the revised plan concise.
"""
    else:
        retry_context = """
This is the first investigation attempt.

Create the initial investigation plan based only on the user's request.
"""

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

{retry_context}

User request:

{user_query}
"""

    llm = GeminiClient()

    investigation_plan: InvestigationPlan = llm.generate_structured(
        prompt=prompt,
        response_schema=InvestigationPlan,
    )

    return {
        "project": investigation_plan.project,
        "plan": [
            {
                "description": task.description,
                "source": task.source,
            }
            for task in investigation_plan.tasks
        ],
        "required_sources": investigation_plan.required_sources,
        "status": "planning_completed",
    }