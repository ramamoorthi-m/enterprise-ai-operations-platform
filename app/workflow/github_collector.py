from app.state.state import EnterpriseState
from app.tools.github_tools import get_repository_issues
from app.tools.github_tools import get_recent_commits
from app.tools.github_tools import get_deployment_status



def github_collector(state: EnterpriseState):
    project=state["project"]
    issues=get_repository_issues.invoke({"repository":project})
    commits=get_recent_commits.invoke({"repository":project})
    deployment=get_deployment_status.invoke({"repository":project})

    github_data = {
        "repository": project,
        **issues,
        **commits,
        **deployment,
    }

    return {
        "github_data": github_data,
        "status": "github_collection_completed",
    }