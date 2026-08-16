from mcp.server import MCPServer

from app.tools.jira_tools import (
    get_open_tasks,
    get_blocked_tasks,
    get_overdue_tasks,
    get_current_sprint,
)


mcp = MCPServer(
    "Enterprise Jira MCP Server"
)


@mcp.tool()
def jira_get_open_tasks(project: str) -> dict:
    """Get currently open Jira tasks for a project."""

    return get_open_tasks.invoke(
        {"project": project}
    )


@mcp.tool()
def jira_get_blocked_tasks(project: str) -> dict:
    """Get blocked Jira tasks for a project."""

    return get_blocked_tasks.invoke(
        {"project": project}
    )


@mcp.tool()
def jira_get_overdue_tasks(project: str) -> dict:
    """Get overdue Jira tasks for a project."""

    return get_overdue_tasks.invoke(
        {"project": project}
    )


@mcp.tool()
def jira_get_current_sprint(project: str) -> dict:
    """Get the current Jira sprint status for a project."""

    return get_current_sprint.invoke(
        {"project": project}
    )


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001,
        stateless_http=True,
        json_response=True,
    )