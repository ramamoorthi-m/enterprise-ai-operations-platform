import os

from app.agents.investigation import InvestigationAgent
from app.llm.client import GeminiClient
from app.state.state import EnterpriseState

from app.tools.jira_tools import (
    get_open_tasks,
    get_blocked_tasks,
    get_overdue_tasks,
    get_current_sprint,
)

from app.tools.github_tools import (
    get_repository_issues,
    get_recent_commits,
    get_deployment_status,
)


def investigator(state: EnterpriseState):
    """LangGraph node that runs the InvestigationAgent."""

    llm = GeminiClient()

    tools = [
        get_open_tasks,
        get_blocked_tasks,
        get_overdue_tasks,
        get_current_sprint,
        get_repository_issues,
        get_recent_commits,
        get_deployment_status,
    ]

    agent = InvestigationAgent(
        llm=llm,
        tools=tools,
        max_iterations=state.get(
            "max_investigation_iterations",
            5,
        ),
    )

    plan = state.get("plan", [])

    normalized_plan = []

    for task in plan:
        if hasattr(task, "model_dump"):
            normalized_plan.append(task.model_dump())
        elif isinstance(task, dict):
            normalized_plan.append(task)

    github_owner = os.getenv("GITHUB_OWNER")
    github_repo = os.getenv("GITHUB_REPO")

    investigation_state = {
        **state,
        "github_repository": state.get(
            "github_repository"
        ) or f"{github_owner}/{github_repo}",
    }

    result = agent.investigate(
        plan=normalized_plan,
        state=investigation_state,
    )

    history = result.get(
        "investigation_history",
        [],
    )

    github_data = {}
    jira_data = {}

    github_tools = {
        "get_repository_issues",
        "get_recent_commits",
        "get_deployment_status",
    }

    jira_tools = {
        "get_open_tasks",
        "get_blocked_tasks",
        "get_overdue_tasks",
        "get_current_sprint",
    }

    for item in history:
        tool_name = item.get("tool")
        tool_result = item.get("result")

        if tool_name in github_tools:
            github_data[tool_name] = tool_result

        elif tool_name in jira_tools:
            jira_data[tool_name] = tool_result

    return {
        "investigation_history": history,

        "investigation_iteration": result.get(
            "investigation_iteration",
            0,
        ),

        "investigation_complete": result.get(
            "investigation_complete",
            False,
        ),

        "github_data": github_data,
        "jira_data": jira_data,

        "findings": result.get(
            "findings",
            [],
        ),

        "status": result.get(
            "status",
            "investigation_completed",
        ),
    }