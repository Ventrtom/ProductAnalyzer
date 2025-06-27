"""Utilities for retrieving JIRA issues."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import os

import requests
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

JIRA_URL = os.getenv("JIRA_URL")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
JIRA_AUTH_TOKEN = os.getenv("JIRA_AUTH_TOKEN")
JIRA_JQL = os.getenv("JIRA_JQL")


class JiraRetriever:
    """Simple JIRA REST API client used in unit tests."""

    def __init__(self, url: str, username: str, token: str) -> None:
        self.base_url = url.rstrip("/")
        self.auth: Tuple[str, str] = (username, token)

    def fetch_issues(self, project_key: str, max_results: int = 50) -> List[Dict[str, Optional[str]]]:
        """Return issues for the given project."""

        search_url = f"{self.base_url}/rest/api/2/search"

        start_at = 0
        issues: List[Dict[str, Optional[str]]] = []

        while True:
            params = {
                "jql": JIRA_JQL or f"project={project_key}",
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "summary,description,status,labels",
            }

            response = requests.get(
                search_url, params=params, auth=self.auth, timeout=30
            )
            response.raise_for_status()
            data = response.json()

            for issue in data.get("issues", []):
                fields = issue.get("fields", {})
                issues.append(
                    {
                        "key": issue.get("key"),
                        "summary": fields.get("summary"),
                        "description": fields.get("description"),
                        "status": (fields.get("status") or {}).get("name"),
                        "labels": fields.get("labels", []),
                    }
                )

            retrieved = start_at + data.get("maxResults", 0)
            total = data.get("total", 0)
            if retrieved >= total:
                break
            start_at = retrieved

        return issues

# 2) Helper s retry
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    reraise=True
)
def _get(
    url: str,
    params: Dict[str, str],
    auth_token: Optional[str] = None,
) -> dict:
    """Issue a GET request with retries."""
    token = auth_token or os.getenv("JIRA_AUTH_TOKEN")
    headers = {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
    }
    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()

# 3) Pydantic model pro Issue
class JiraIssue(BaseModel):
    key: str
    summary: Optional[str]
    description: Optional[str]
    status: Optional[str]
    labels: Optional[List[str]]


def fetch_all_issues(
    project_key: Optional[str] = None,
    max_results: int = 50,
    jira_url: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> List[JiraIssue]:
    """
    Načte všechny issue z projektu, stránku po stránce.
    """
    jira_url = jira_url or os.getenv("JIRA_URL")
    project_key = project_key or os.getenv("JIRA_PROJECT_KEY")
    auth_token = auth_token or os.getenv("JIRA_AUTH_TOKEN")

    if not jira_url or not project_key or not auth_token:
        raise ValueError("Missing JIRA_URL, JIRA_PROJECT_KEY or JIRA_AUTH_TOKEN")

    search_url = jira_url.rstrip("/") + "/rest/api/2/search"
    start_at = 0
    issues: List[JiraIssue] = []

    while True:
        params = {
            "jql": JIRA_JQL or f"project={project_key}",
            "startAt": start_at,
            "maxResults": max_results,
            "fields": "summary,description,status,labels",
        }
        data = _get(search_url, params, auth_token)

        for raw in data.get("issues", []):
            f = raw.get("fields", {})
            issues.append(
                JiraIssue(
                    key=raw.get("key"),
                    summary=f.get("summary"),
                    description=f.get("description"),
                    status=(f.get("status") or {}).get("name"),
                    labels=f.get("labels", []),
                )
            )

        total = data.get("total", 0)
        start_at += max_results
        if start_at >= total:
            break

    return issues


def get_roadmap_ideas(
    jira_url: Optional[str] = None,
    project_key: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> List[dict]:
    """Fetch issues and return them as dictionaries."""

    jira_url = jira_url or os.getenv("JIRA_URL")
    project_key = project_key or os.getenv("JIRA_PROJECT_KEY")
    auth_token = auth_token or os.getenv("JIRA_AUTH_TOKEN")

    if not jira_url or not project_key or not auth_token:
        raise ValueError("Missing JIRA_URL, JIRA_PROJECT_KEY or JIRA_AUTH_TOKEN")

    # ``fetch_all_issues`` already applies ``JIRA_JQL`` if set
    issues = fetch_all_issues(
        project_key=project_key,
        max_results=50,
        jira_url=jira_url,
        auth_token=auth_token,
    )
    return [
        {
            "key": issue.key,
            "summary": issue.summary,
            "description": issue.description,
            "status": issue.status,
        }
        for issue in issues
    ]


if __name__ == "__main__":
    # 4) Příklad použití: vypíše všechna issue jako JSON
    all_issues = fetch_all_issues()
    for issue in all_issues:
        print(issue.json())
