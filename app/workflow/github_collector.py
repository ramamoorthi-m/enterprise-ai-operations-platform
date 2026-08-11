import os

from dotenv import load_dotenv

from app.state.state import EnterpriseState
from app.tools.github_tools import get_repository_issues
from app.tools.github_tools import get_recent_commits
from app.tools.github_tools import get_deployment_status

load_dotenv()



def github_collector(state: EnterpriseState):
    owner=os.getenv("GITHUB_OWNER")
    repo=os.getenv("GITHUB_REPO")

    if not owner or not repo:
        raise ValueError("GITHUB_OWNER and GITHUB_REPO must be configured")

    repository=f"{owner}/{repo}"

    print(f"DEBUG GitHub repository: {repository}")

    
    issues=get_repository_issues.invoke({"repository":repository})
    commits=get_recent_commits.invoke({"repository":repository})
    deployment=get_deployment_status.invoke({"repository":repository})

    github_data = {
        "repository": repository,
        **issues,
        **commits,
        **deployment,
    }

    return {
        "github_data": github_data,
        "status": "github_collection_completed",
    }