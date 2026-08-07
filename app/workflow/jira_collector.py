from app.state.state import EnterpriseState
from app.tools.jira_tools import get_open_tasks
from app.tools.jira_tools import get_blocked_tasks
from app.tools.jira_tools import get_overdue_tasks
from app.tools.jira_tools import get_current_sprint




def jira_collector(state: EnterpriseState):

    """
    Mock Jira collector.

    Later this will be replaced with a real Jira API/MCP integration.
    """

    open_tasks=get_open_tasks()
    blocked_tasks=get_blocked_tasks()
    overdue_tasks=get_overdue_tasks()
    sprint=get_current_sprint()

    jira_data = {
        "project": "Project Alpha",
        **open_tasks,
        **blocked_tasks,
        **overdue_tasks,
        **sprint,
    }

    return {
        "jira_data": jira_data,
        "status": "jira_collection_completed",
    }