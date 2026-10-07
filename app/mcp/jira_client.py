import json

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_SERVER_URL = "http://127.0.0.1:8001/mcp"


class JiraMCPClient:
    """Client for communicating with the Jira MCP server."""

    def __init__(self, server_url: str = MCP_SERVER_URL):
        self.server_url = server_url
        self._http_client = None
        self._mcp_transport = None
        self._session = None

    async def connect(self):
        """Establish connection with the Jira MCP server."""

        if self._session is not None:
            return

        http_client = None
        mcp_transport = None
        session = None

        try:
            http_client = httpx2.AsyncClient(
                timeout=httpx2.Timeout(
                    connect=5.0,
                    read=30.0,
                    write=10.0,
                    pool=5.0,
                )
            )

            mcp_transport = streamable_http_client(
                self.server_url,
                http_client=http_client,
            )

            read_stream, write_stream = (
                await mcp_transport.__aenter__()
            )

            session = ClientSession(
                read_stream,
                write_stream,
            )

            await session.__aenter__()
            await session.initialize()

            self._http_client = http_client
            self._mcp_transport = mcp_transport
            self._session = session

        except Exception:
            if session is not None:
                try:
                    await session.__aexit__(
                        None,
                        None,
                        None,
                    )
                except Exception:
                    pass

            if mcp_transport is not None:
                try:
                    await mcp_transport.__aexit__(
                        None,
                        None,
                        None,
                    )
                except Exception:
                    pass

            if http_client is not None:
                try:
                    await http_client.aclose()
                except Exception:
                    pass

            raise

    async def close(self):
        """Close the MCP connection and HTTP client."""

        session = self._session
        mcp_transport = self._mcp_transport
        http_client = self._http_client

        self._session = None
        self._mcp_transport = None
        self._http_client = None

        if session is not None:
            try:
                await session.__aexit__(
                    None,
                    None,
                    None,
                )
            except Exception:
                pass

        if mcp_transport is not None:
            try:
                await mcp_transport.__aexit__(
                    None,
                    None,
                    None,
                )
            except Exception:
                pass

        if http_client is not None:
            try:
                await http_client.aclose()
            except Exception:
                pass

    async def list_tools(self):
        """Return tools exposed by the Jira MCP server."""

        if self._session is None:
            raise RuntimeError(
                "MCP client is not connected."
            )

        result = await self._session.list_tools()

        return result.tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
    ) -> dict:
        """Call an MCP tool and return its JSON result."""

        if self._session is None:
            raise RuntimeError(
                "MCP client is not connected."
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