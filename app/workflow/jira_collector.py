from app.state.state import EnterpriseState
from app.tools.jira_tools import get_open_tasks
from app.tools.jira_tools import get_blocked_tasks
from app.tools.jira_tools import get_overdue_tasks
from app.tools.jira_tools import get_current_sprint


def jira_collector(state: EnterpriseState):

    project = state["project"]

    open_tasks = get_open_tasks.invoke({})
    blocked_tasks = get_blocked_tasks.invoke({})
    overdue_tasks = get_overdue_tasks.invoke({})
    sprint = get_current_sprint.invoke({})

    jira_data = {
        "project": project,
        **open_tasks,
        **blocked_tasks,
        **overdue_tasks,
        **sprint,
    }

    return {
        "jira_data": jira_data,
        "status": "jira_collection_completed",
    }