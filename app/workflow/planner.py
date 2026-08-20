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

You must review the previous investigation before creating
the new plan.

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
- Create a revised investigation plan that specifically addresses
  those gaps.
- Reuse previous sources only when they can provide additional
  or better evidence.
- Do not invent information.
- Do not create tasks for evidence that cannot reasonably be
  obtained using the available tools.
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

Your job is to determine WHAT evidence needs to be collected.
You do not execute tools yourself.

AVAILABLE ENTERPRISE SYSTEMS AND CAPABILITIES:

1. GitHub

Available GitHub capabilities:

- github_get_repository_issues
  Retrieves issues from a GitHub repository.

- github_get_recent_commits
  Retrieves recent commits from a GitHub repository.

- github_get_deployment_status
  Retrieves the latest GitHub Actions deployment/workflow status.

2. Jira

Available Jira capabilities:

- jira_get_open_tasks
  Retrieves currently open Jira tasks.

- jira_get_blocked_tasks
  Retrieves blocked Jira tasks.

- jira_get_overdue_tasks
  Retrieves overdue Jira tasks.

- jira_get_current_sprint
  Retrieves the current Jira sprint.

IMPORTANT CAPABILITY LIMITS:

- There is currently NO GitHub pull-request tool.
- There is currently NO GitHub review tool.
- There is currently NO GitHub branch/file-search tool.
- There is currently NO Jira high-priority-specific tool.
- There is currently NO Jira in-progress-specific tool.
- Do not create investigation tasks that require unavailable capabilities.
- Use the available tools that can reasonably provide the required evidence.
- For information that can be obtained through an available broader
  tool, use that tool instead of inventing a new capability.

PLANNING RULES:

- Only use GitHub and Jira as investigation sources.
- Do not invent information.
- Identify only the sources actually needed.
- Create concrete investigation tasks.
- Every task must specify either "github" or "jira".
- Each task must be achievable using the available capabilities.
- Focus on collecting factual evidence.
- Do not answer the user's question.
- Keep the plan concise.
- Avoid unnecessary duplicate tasks.
- Prioritize evidence directly related to the user's request.

SOURCE SELECTION:

Use Jira when the investigation requires:
- blocked work
- overdue work
- open work
- current sprint information

Use GitHub when the investigation requires:
- repository issues
- recent development activity
- deployment/workflow status

Do not require both sources unless both are genuinely necessary
to answer the user's request.

{retry_context}

User request:

{user_query}
"""

    llm = GeminiClient()

    investigation_plan: InvestigationPlan = (
        llm.generate_structured(
            prompt=prompt,
            response_schema=InvestigationPlan,
        )
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