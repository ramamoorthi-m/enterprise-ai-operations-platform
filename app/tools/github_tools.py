from langchain_core.tools import tool
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITHUB_TOKEN")

@tool
def get_repository_issues(repository: str):
    """Get the current open issues in a GitHub repository."""

    

    url = f"https://api.github.com/repos/{repository}/issues"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    params = {
        "state": "open",
        "per_page": 100
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    response.raise_for_status()

    issues = response.json()

    return {
        "repository": repository,
        "open_issues": len(issues)
    }

@tool
def get_recent_commits(repository: str):
    """Get the most recent commit in a GitHub repository."""

    url = f"https://api.github.com/repos/{repository}/commits"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    params = {
        "per_page": 1
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    commits = response.json()

    latest_commit = commits[0]

    return {
        "repository": repository,
        "latest_commit_sha": latest_commit["sha"],
        "latest_commit_message": latest_commit["commit"]["message"],
        "latest_commit_author": latest_commit["commit"]["author"]["name"],
        "latest_commit_date": latest_commit["commit"]["author"]["date"]
    }

@tool
def get_deployment_status(repository: str):
    """Get the latest GitHub Actions workflow status."""

    owner, repo = repository.split("/", 1)

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2026-03-10",
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"

    response = requests.get(
        url,
        headers=headers,
        params={
            "per_page": 1,
        },
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    workflow_runs = data.get("workflow_runs", [])

    if not workflow_runs:
        return {
            "repository": repository,
            "deployment_status": "no_workflow_runs_found",
        }

    latest_run = workflow_runs[0]

    return {
        "repository": repository,
        "deployment_status": latest_run.get("status"),
        "conclusion": latest_run.get("conclusion"),
        "workflow_name": latest_run.get("name"),
        "branch": latest_run.get("head_branch"),
        "commit_sha": latest_run.get("head_sha"),
        "run_number": latest_run.get("run_number"),
        "run_url": latest_run.get("html_url"),
        "created_at": latest_run.get("created_at"),
        "updated_at": latest_run.get("updated_at"),
    }