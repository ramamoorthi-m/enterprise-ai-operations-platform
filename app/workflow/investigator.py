import os

from app.agents.investigation import InvestigationAgent
from app.llm.client import GeminiClient
from app.state.state import EnterpriseState

from app.mcp.jira_client import JiraMCPClient
from app.mcp.github_client import GitHubMCPClient

from app.tools.jira_mcp_tools import JiraMCPToolProvider
from app.tools.github_mcp_tools import GitHubMCPToolProvider


async def investigator(state: EnterpriseState):
    """LangGraph node that runs the InvestigationAgent."""

    llm = GeminiClient()

    # ---------------------------------------------------------
    # Connect to Jira MCP server
    # ---------------------------------------------------------

    jira_client = JiraMCPClient()
    await jira_client.connect()

    jira_provider = JiraMCPToolProvider(
        jira_client
    )

    jira_tools = jira_provider.get_tools()

    # ---------------------------------------------------------
    # Connect to GitHub MCP server
    # ---------------------------------------------------------

    github_client = GitHubMCPClient()
    await github_client.connect()

    github_provider = GitHubMCPToolProvider(
        github_client
    )

    github_tools = github_provider.get_tools()

    # ---------------------------------------------------------
    # Combine MCP tools
    # ---------------------------------------------------------

    tools = [
        *jira_tools,
        *github_tools,
    ]

    try:
        # -----------------------------------------------------
        # Create Investigation Agent
        # -----------------------------------------------------

        agent = InvestigationAgent(
            llm=llm,
            tools=tools,
            max_iterations=state.get(
                "max_investigation_iterations",
                5,
            ),
        )

        # -----------------------------------------------------
        # Normalize planner output
        # -----------------------------------------------------

        plan = state.get("plan", [])

        normalized_plan = []

        for task in plan:
            if hasattr(task, "model_dump"):
                normalized_plan.append(
                    task.model_dump()
                )

            elif isinstance(task, dict):
                normalized_plan.append(task)

        # -----------------------------------------------------
        # Build investigation state
        # -----------------------------------------------------

        github_owner = os.getenv(
            "GITHUB_OWNER"
        )

        github_repo = os.getenv(
            "GITHUB_REPO"
        )

        investigation_state = {
            **state,
            "github_repository": (
                state.get("github_repository")
                or f"{github_owner}/{github_repo}"
            ),
        }

        # -----------------------------------------------------
        # Run investigation
        # -----------------------------------------------------

        result = await agent.investigate(
            plan=normalized_plan,
            state=investigation_state,
        )

        history = result.get(
            "investigation_history",
            [],
        )

        # -----------------------------------------------------
        # Separate evidence by source
        # -----------------------------------------------------

        github_data = {}
        jira_data = {}

        github_tool_names = {
            "github_get_repository_issues",
            "github_get_recent_commits",
            "github_get_deployment_status",
        }

        jira_tool_names = {
            "jira_get_open_tasks",
            "jira_get_blocked_tasks",
            "jira_get_overdue_tasks",
            "jira_get_current_sprint",
        }

        for item in history:

            tool_name = item.get("tool")
            tool_result = item.get("result")

            if tool_name in github_tool_names:
                github_data[tool_name] = tool_result

            elif tool_name in jira_tool_names:
                jira_data[tool_name] = tool_result

        # -----------------------------------------------------
        # Return LangGraph state update
        # -----------------------------------------------------

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

    finally:
        # -----------------------------------------------------
        # Always close MCP connections
        # -----------------------------------------------------

        await github_client.close()
        await jira_client.close()