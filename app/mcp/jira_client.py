import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_SERVER_URL = "http://127.0.0.1:8001/mcp"


class JiraMCPClient:
    """Client for communicating with the Jira MCP server."""

    def __init__(self, server_url: str = MCP_SERVER_URL):
        self.server_url = server_url
        self._http_client = None
        self._session = None

    async def connect(self):
        """Establish connection with the Jira MCP server."""

        self._http_client = streamable_http_client(
            self.server_url
        )

        read_stream, write_stream = await self._http_client.__aenter__()

        self._session = ClientSession(
            read_stream,
            write_stream,
        )

        await self._session.__aenter__()
        await self._session.initialize()

    async def close(self):
        """Close the MCP connection."""

        if self._session is not None:
            await self._session.__aexit__(None, None, None)
            self._session = None

        if self._http_client is not None:
            await self._http_client.__aexit__(None, None, None)
            self._http_client = None

    async def list_tools(self):
        """Return tools exposed by the Jira MCP server."""

        if self._session is None:
            raise RuntimeError("MCP client is not connected.")

        result = await self._session.list_tools()

        return result.tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
    ) -> dict:
        """Call an MCP tool and return its JSON result."""

        if self._session is None:
            raise RuntimeError("MCP client is not connected.")

        result = await self._session.call_tool(
            tool_name,
            arguments=arguments,
        )

        if result.is_error:
            raise RuntimeError(
                f"MCP tool '{tool_name}' returned an error."
            )

        if not result.content:
            return {}

        text = result.content[0].text

        return json.loads(text)

    async def get_open_tasks(self, project: str) -> dict:
        """Get open Jira tasks."""

        return await self.call_tool(
            "jira_get_open_tasks",
            {"project": project},
        )

    async def get_blocked_tasks(self, project: str) -> dict:
        """Get blocked Jira tasks."""

        return await self.call_tool(
            "jira_get_blocked_tasks",
            {"project": project},
        )

    async def get_overdue_tasks(self, project: str) -> dict:
        """Get overdue Jira tasks."""

        return await self.call_tool(
            "jira_get_overdue_tasks",
            {"project": project},
        )

    async def get_current_sprint(self, project: str) -> dict:
        """Get current Jira sprint."""

        return await self.call_tool(
            "jira_get_current_sprint",
            {"project": project},
        )