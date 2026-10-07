from app.tools.github_mcp_tools import GitHubMCPToolProvider


class FakeGitHubClient:

    async def get_repository_issues(self, repository):
        return {
            "repository": repository,
            "open_issues": 0,
        }

    async def get_recent_commits(self, repository):
        return {
            "repository": repository,
            "latest_commit_sha": "test-sha",
        }

    async def get_deployment_status(self, repository):
        return {
            "repository": repository,
            "deployment_status": "success",
        }


def test_github_mcp_tools():

    client = FakeGitHubClient()

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