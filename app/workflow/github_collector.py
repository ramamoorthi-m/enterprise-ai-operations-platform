from app.state.state import EnterpriseState
from app.tools.github_tools import get_repository_issues
from app.tools.github_tools import get_recent_commits
from app.tools.github_tools import get_deployment_status



def github_collector(state: EnterpriseState):
    issues=get_repository_issues()
    commits=get_recent_commits()
    deployment=get_deployment_status()

    github_data = {
        "repository": "Project Alpha",
        **issues,
        **commits,
        **deployment,
    }

    return {
        "github_data": github_data,
        "status": "github_collection_completed",
    }