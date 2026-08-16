from mcp.server import MCPServer

from app.tools.github_tools import (
    get_repository_issues,
    get_recent_commits,
    get_deployment_status,
)


mcp = MCPServer(
    "Enterprise GitHub MCP Server"
)


@mcp.tool()
def github_get_repository_issues(
    repository: str,
) -> dict:
    """Get open issues in a GitHub repository."""

    return get_repository_issues.invoke(
        {"repository": repository}
    )


@mcp.tool()
def github_get_recent_commits(
    repository: str,
) -> dict:
    """Get the most recent commit in a GitHub repository."""

    return get_recent_commits.invoke(
        {"repository": repository}
    )


@mcp.tool()
def github_get_deployment_status(
    repository: str,
) -> dict:
    """Get the latest GitHub Actions workflow status."""

    return get_deployment_status.invoke(
        {"repository": repository}
    )


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8002,
        stateless_http=True,
        json_response=True,
    )