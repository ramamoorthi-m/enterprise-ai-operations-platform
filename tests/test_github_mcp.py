import pytest

from app.mcp.github_client import GitHubMCPClient
from app.tools.github_mcp_tools import GitHubMCPToolProvider


@pytest.mark.asyncio
async def test_github_mcp_tools():

    client = GitHubMCPClient()

    await client.connect()

    try:
        provider = GitHubMCPToolProvider(client)

        tools = provider.get_tools()

        assert len(tools) == 3

        tool_names = {
            tool.name
            for tool in tools
        }

        assert "github_get_repository_issues" in tool_names
        assert "github_get_recent_commits" in tool_names
        assert "github_get_deployment_status" in tool_names

    finally:
        await client.close()