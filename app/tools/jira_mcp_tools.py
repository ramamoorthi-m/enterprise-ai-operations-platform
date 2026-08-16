from langchain_core.tools import tool

from app.mcp.jira_client import JiraMCPClient


class JiraMCPToolProvider:
    """Expose Jira MCP capabilities to the InvestigationAgent."""

    def __init__(self, client: JiraMCPClient):
        self.client = client

    async def jira_get_open_tasks(self, project: str) -> dict:
        """Get currently open Jira tasks for a project."""
        return await self.client.get_open_tasks(project)

    async def jira_get_blocked_tasks(self, project: str) -> dict:
        """Get blocked Jira tasks for a project."""
        return await self.client.get_blocked_tasks(project)

    async def jira_get_overdue_tasks(self, project: str) -> dict:
        """Get overdue Jira tasks for a project."""
        return await self.client.get_overdue_tasks(project)

    async def jira_get_current_sprint(self, project: str) -> dict:
        """Get the current Jira sprint for a project."""
        return await self.client.get_current_sprint(project)

    def get_tools(self):
        """Return Jira MCP functions as LangChain tools."""

        return [
            tool(self.jira_get_open_tasks),
            tool(self.jira_get_blocked_tasks),
            tool(self.jira_get_overdue_tasks),
            tool(self.jira_get_current_sprint),
        ]