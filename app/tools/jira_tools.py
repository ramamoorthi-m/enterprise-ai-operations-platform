import os 
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool
load_dotenv()
JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "SCRUM")

@tool
def get_open_tasks():
    """Get the current number of open tasks in Jira."""

    url = f"{os.getenv('JIRA_URL')}/rest/api/3/search/jql"

    response = requests.get(
        url,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={
            "Accept": "application/json"
        },
        params={
            "jql": f"project = {JIRA_PROJECT_KEY}",
            "maxResults": 100
        },
        timeout=10
    )

    print("STATUS:", response.status_code)
    print("URL:", response.url)
    print("RESPONSE:", response.text)

    response.raise_for_status()

    data = response.json()

    return {
        "project": JIRA_PROJECT_KEY,
        "open_tasks": len(data.get("issues", []))
    }

@tool
def get_blocked_tasks():
    """Get the current number of blocked tasks in Jira."""

    url = f"{JIRA_URL}/rest/api/3/search/jql"

    response = requests.get(
        url,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={
            "Accept": "application/json"
        },
        params={
            "jql": f'project = {JIRA_PROJECT_KEY} AND status = "Blocked"',
            "maxResults": 100
        },
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    return {
        "project": JIRA_PROJECT_KEY,
        "blocked_tasks": len(data.get("issues", []))
    }

@tool
def get_overdue_tasks():
    """Get the current number of overdue tasks in Jira."""

    url = f"{JIRA_URL}/rest/api/3/search/jql"

    response = requests.get(
        url,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={
            "Accept": "application/json"
        },
        params={
            "jql": f'project = {JIRA_PROJECT_KEY} AND due < now() AND statusCategory != Done',
            "maxResults": 100
        },
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    return {
        "project": JIRA_PROJECT_KEY,
        "overdue_tasks": len(data.get("issues", []))
    }

@tool
def get_current_sprint():
    """Get the current active Jira sprint."""

    url = f"{JIRA_URL}/rest/api/3/search/jql"

    response = requests.get(
        url,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={
            "Accept": "application/json"
        },
        params={
            "jql": f"project = {JIRA_PROJECT_KEY} AND sprint in openSprints()",
            "maxResults": 100,
            "fields": "summary"
        },
        timeout=10
    )

    response.raise_for_status()

    data = response.json()
    

    issues = data.get("issues", [])

    return {
        "project": JIRA_PROJECT_KEY,
        "current_sprint": "active",
        "issue_count": len(issues),
        "issues": [
            {
                "key": issue.get("key"),
                "summary": issue.get("fields", {}).get("summary")
            }
            for issue in issues
        ]
    }