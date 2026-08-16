from langchain_core.tools import tool

from app.mcp.github_client import GitHubMCPClient


class GitHubMCPToolProvider:
    """Expose GitHub MCP capabilities to the InvestigationAgent."""

    def __init__(self, client: GitHubMCPClient):
        self.client = client

    async def github_get_repository_issues(
        self,
        repository: str,
    ) -> dict:
        """Get open issues in a GitHub repository."""

        return await self.client.get_repository_issues(
            repository
        )

    async def github_get_recent_commits(
        self,
        repository: str,
    ) -> dict:
        """Get the most recent GitHub commit."""

        return await self.client.get_recent_commits(
            repository
        )

    async def github_get_deployment_status(
        self,
        repository: str,
    ) -> dict:
        """Get the latest GitHub Actions workflow status."""

        return await self.client.get_deployment_status(
            repository
        )

    def get_tools(self):
        """Return GitHub MCP functions as LangChain tools."""

        return [
            tool(self.github_get_repository_issues),
            tool(self.github_get_recent_commits),
            tool(self.github_get_deployment_status),
        ]