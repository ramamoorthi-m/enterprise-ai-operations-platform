import asyncio

from app.mcp.github_client import GitHubMCPClient


async def main():

    client = GitHubMCPClient()

    try:
        print("Connecting to GitHub MCP Server...")

        await client.connect()

        print("Connected successfully!")

        print("\nAvailable tools:")

        tools = await client.list_tools()

        for tool in tools:
            print(f"- {tool.name}")

        repository = (
            "ramamoorthi-m/"
            "enterprise-ai-operations-platform"
        )

        print("\nTesting GitHub MCP tools...")

        issues = await client.get_repository_issues(
            repository
        )

        commits = await client.get_recent_commits(
            repository
        )

        deployment = await client.get_deployment_status(
            repository
        )

        print("\nRepository issues:")
        print(issues)

        print("\nRecent commits:")
        print(commits)

        print("\nDeployment status:")
        print(deployment)

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())