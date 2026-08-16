import asyncio

from app.mcp.jira_client import JiraMCPClient


async def main():

    client = JiraMCPClient()

    try:
        print("Connecting to Jira MCP Server...")

        await client.connect()

        print("Connected successfully!")

        print("\nAvailable tools:")

        tools = await client.list_tools()

        for tool in tools:
            print(f"- {tool.name}")

        print("\nTesting Jira MCP client...")

        open_tasks = await client.get_open_tasks("SCRUM")
        blocked_tasks = await client.get_blocked_tasks("SCRUM")
        overdue_tasks = await client.get_overdue_tasks("SCRUM")
        current_sprint = await client.get_current_sprint("SCRUM")

        print("\nOpen tasks:")
        print(open_tasks)

        print("\nBlocked tasks:")
        print(blocked_tasks)

        print("\nOverdue tasks:")
        print(overdue_tasks)

        print("\nCurrent sprint:")
        print(current_sprint)

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())