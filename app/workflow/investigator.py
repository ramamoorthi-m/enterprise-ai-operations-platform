import os

from app.agents.investigation import InvestigationAgent
from app.llm.client import GeminiClient
from app.state.state import EnterpriseState
from app.mcp.jira_client import JiraMCPClient
from app.mcp.github_client import GitHubMCPClient
from app.tools.jira_mcp_tools import JiraMCPToolProvider
from app.tools.github_mcp_tools import GitHubMCPToolProvider
from app.errors.failures import (
    CONNECTION_FAILURE,
    build_failure,
)


async def investigator(state: EnterpriseState):
    llm = GeminiClient()

    required_sources = set(state.get("required_sources", []))

    failures = []

    jira_client = None
    github_client = None
    tools = []

    try:
        # Connect only to the MCP sources required by the investigation plan.
        if "jira" in required_sources:
            jira_client = JiraMCPClient()

            try:
                await jira_client.connect()
            except Exception as exc:
                failures.append(
                    build_failure(
                        category=CONNECTION_FAILURE,
                        source="jira",
                        message=str(exc),
                        retryable=True,
                        blocking=True,
                    )
                )
                jira_client = None
            else:
                jira_provider = JiraMCPToolProvider(jira_client)
                tools.extend(jira_provider.get_tools())

        if "github" in required_sources:
            github_client = GitHubMCPClient()
            try:
                await github_client.connect()
            except Exception as exc:
                failures.append(
                    build_failure(
                        category=CONNECTION_FAILURE,
                        source="github",
                        message=str(exc),
                        retryable=True,
                        blocking=True,
                    )
                )
                github_client = None
            else:
                github_provider = GitHubMCPToolProvider(github_client)
                tools.extend(github_provider.get_tools())


            

        agent = InvestigationAgent(
            llm=llm,
            tools=tools,
            max_iterations=state.get("max_investigation_iterations", 5),
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
            "github_repository": (
                state.get("github_repository")
                or f"{github_owner}/{github_repo}"
            ),
        }

        result = await agent.investigate(
            plan=normalized_plan,
            state=investigation_state,
        )

        history = result.get("investigation_history", [])

        investigation_failures = result.get("failures", [])

        all_failures = [
            *failures,
            *investigation_failures,
        ]

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

        return {
            "investigation_history": history,
            "investigation_iteration": result.get(
                "investigation_iteration", 0
            ),
            "investigation_complete": result.get(
                "investigation_complete", False
            ),
            "github_data": github_data,
            "jira_data": jira_data,
            "findings": result.get("findings", []),
            "failures": all_failures,
            "status": result.get(
                "status",
                "investigation_completed",
            ),
        }

    finally:
        # Cleanup only the MCP clients that were actually connected.
        # Cleanup is best-effort so one close failure does not prevent
        # the other client from being closed.
        if github_client is not None:
            try:
                await github_client.close()
            except Exception:
                pass

        if jira_client is not None:
            try:
                await jira_client.close()
            except Exception:
                pass