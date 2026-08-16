import pytest

from app.mcp.jira_client import JiraMCPClient
from app.tools.jira_mcp_tools import JiraMCPToolProvider


@pytest.mark.anyio
async def test_jira_mcp_tools():

    client = JiraMCPClient()

    await client.connect()

    try:
        provider = JiraMCPToolProvider(client)

        result = await provider.jira_get_open_tasks("SCRUM")

        assert result["project"] == "SCRUM"
        assert "open_tasks" in result

    finally:
        await client.close()