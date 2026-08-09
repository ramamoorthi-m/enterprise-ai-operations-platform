from app.tools.github_tools import get_repository_issues


repository = "ramamoorthi-m/enterprise-ai-operations-platform"

result = get_repository_issues.invoke({
    "repository": repository
})

print(result)