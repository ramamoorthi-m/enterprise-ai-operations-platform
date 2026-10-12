import os

import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

JIRA_URL = os.getenv("JIRA_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "SCRUM")


def search_jira(jql: str, fields: str = "summary") -> list[dict]:
    """Execute a Jira issue search and return its issues."""

    if not JIRA_URL or not JIRA_EMAIL or not JIRA_API_TOKEN:
        raise ValueError(
            "Jira configuration is incomplete. "
            "Check JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN."
        )

    response = requests.get(
        f"{JIRA_URL}/rest/api/3/search/jql",
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={"Accept": "application/json"},
        params={
            "jql": jql,
            "maxResults": 100,
            "fields": fields,
        },
        timeout=10,
    )
    response.raise_for_status()

    return response.json().get("issues", [])


@tool
def get_open_tasks(project: str) -> dict:
    """Get open Jira tasks for a project."""

    issues = search_jira(
        f"project = {project} AND statusCategory != Done"
    )

    return {
        "project": project,
        "open_tasks": len(issues),
    }


@tool
def get_blocked_tasks(project: str) -> dict:
    """Get blocked Jira tasks for a project."""

    issues = search_jira(
        f'project = {project} AND status = "Blocked"'
    )

    return {
        "project": project,
        "blocked_tasks": len(issues),
    }


@tool
def get_overdue_tasks(project: str) -> dict:
    """Get overdue Jira tasks for a project."""

    issues = search_jira(
        f"project = {project} AND due < now() "
        "AND statusCategory != Done"
    )

    return {
        "project": project,
        "overdue_tasks": len(issues),
    }


@tool
def get_current_sprint(project: str) -> dict:
    """Get issues in the current active Jira sprint."""

    issues = search_jira(
        f"project = {project} AND sprint in openSprints()",
        fields="summary",
    )

    return {
        "project": project,
        "current_sprint": "active",
        "issue_count": len(issues),
        "issues": [
            {
                "key": issue.get("key"),
                "summary": issue.get("fields", {}).get("summary"),
            }
            for issue in issues
        ],
    }