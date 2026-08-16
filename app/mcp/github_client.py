import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_SERVER_URL = "http://127.0.0.1:8002/mcp"


class GitHubMCPClient:
    """Client for communicating with the GitHub MCP server."""

    def __init__(
        self,
        server_url: str = MCP_SERVER_URL,
    ):
        self.server_url = server_url
        self._http_client = None
        self._session = None

    async def connect(self):
        """Establish connection with the GitHub MCP server."""

        self._http_client = streamable_http_client(
            self.server_url
        )

        read_stream, write_stream = (
            await self._http_client.__aenter__()
        )

        self._session = ClientSession(
            read_stream,
            write_stream,
        )

        await self._session.__aenter__()
        await self._session.initialize()

    async def close(self):
        """Close the MCP connection."""

        if self._session is not None:
            await self._session.__aexit__(
                None,
                None,
                None,
            )
            self._session = None

        if self._http_client is not None:
            await self._http_client.__aexit__(
                None,
                None,
                None,
            )
            self._http_client = None

    async def list_tools(self):
        """Return tools exposed by the GitHub MCP server."""

        if self._session is None:
            raise RuntimeError(
                "GitHub MCP client is not connected."
            )

        result = await self._session.list_tools()

        return result.tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
    ) -> dict:
        """Call a GitHub MCP tool."""

        if self._session is None:
            raise RuntimeError(
                "GitHub MCP client is not connected."
            )

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

    async def get_repository_issues(
        self,
        repository: str,
    ) -> dict:
        """Get open GitHub issues."""

        return await self.call_tool(
            "github_get_repository_issues",
            {"repository": repository},
        )

    async def get_recent_commits(
        self,
        repository: str,
    ) -> dict:
        """Get the most recent GitHub commit."""

        return await self.call_tool(
            "github_get_recent_commits",
            {"repository": repository},
        )

    async def get_deployment_status(
        self,
        repository: str,
    ) -> dict:
        """Get the latest GitHub Actions status."""

        return await self.call_tool(
            "github_get_deployment_status",
            {"repository": repository},
        )