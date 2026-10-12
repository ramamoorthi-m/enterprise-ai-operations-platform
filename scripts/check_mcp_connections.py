import asyncio

from app.mcp.jira_client import JiraMCPClient
from app.mcp.github_client import GitHubMCPClient


async def main():
    clients = [
        ("Jira", JiraMCPClient()),
        ("GitHub", GitHubMCPClient()),
    ]

    for name, client in clients:
        try:
            await client.connect()
            tools = await client.list_tools()

            print(f"\n{name} MCP: CONNECTED")
            print("Available tools:", [tool.name for tool in tools])

        except Exception as exc:
            print(f"\n{name} MCP: FAILED")
            print(f"{type(exc).__name__}: {exc}")

        finally:
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())