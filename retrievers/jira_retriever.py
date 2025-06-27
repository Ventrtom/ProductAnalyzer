from __future__ import annotations

import os
from typing import List, Optional

from dotenv import load_dotenv
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel


# ----------------------------------------------------------------------------
# Low level helpers
# ----------------------------------------------------------------------------

# Helper for HTTP GET with retry
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    reraise=True,
)
def _jira_get(
    jira_url: str,
    endpoint: str,
    params: dict[str, object],
    auth_token: str,
) -> dict:
    """
    Spustí GET na zadaný JIRA endpoint s retry logikou.
    """
    url = f"{jira_url.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Basic {auth_token}",
        "Accept": "application/json",
    }
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    reraise=True,
)
def _get(url: str, params: dict[str, str], token: str) -> dict:
    """Issue a GET request with retries."""

    headers = {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
    }
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


class JiraRetriever:
    """Simple JIRA REST API client."""

    def __init__(self, url: str, username: str, token: str) -> None:
        self.base_url = url.rstrip("/")
        self.auth: tuple[str, str] = (username, token)

    def fetch_issues(self, project_key: str, max_results: int = 50) -> List[dict]:
        """Return issues for the given project."""

        search_url = f"{self.base_url}/rest/api/2/search"

        start_at = 0
        issues: List[dict] = []

        while True:
            params = {
                "jql": f"project={project_key}",
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "summary,description,status,labels",
            }

            data = _get(search_url, params, self.auth[1])

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

# 3) Pydantic model pro Issue
class JiraIssue(BaseModel):
    key: str
    summary: Optional[str]
    description: Optional[str]
    status: Optional[str]
    labels: Optional[List[str]]


def fetch_all_issues(
    jira_url: str,
    project_key: str,
    auth_token: str,
    max_results: int = 50,
) -> List[JiraIssue]:
    """
    Načte všechny issue z projektu, stránku po stránce.
    """
    endpoint = "rest/api/2/search"
    start_at = 0
    issues: List[JiraIssue] = []

    while True:
        params = {
            "jql": f"project={project_key}",
            "startAt": start_at,
            "maxResults": max_results,
            "fields": "summary,description,status,labels",
        }
        data = _jira_get(jira_url, endpoint, params, auth_token)

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
    jira_url: str | None = None,
    project_key: str | None = None,
    auth_token: str | None = None,
) -> List[dict]:
    """Load JIRA issues as simple dictionaries.

    Environment variables ``JIRA_URL``, ``JIRA_PROJECT_KEY`` and
    ``JIRA_AUTH_TOKEN`` are used as defaults when parameters are not
    supplied. A missing configuration raises ``ValueError``.
    """

    load_dotenv()

    jira_url = jira_url or os.getenv("JIRA_URL")
    project_key = project_key or os.getenv("JIRA_PROJECT_KEY")
    auth_token = auth_token or os.getenv("JIRA_AUTH_TOKEN")

    if not jira_url or not project_key or not auth_token:
        raise ValueError(
            "Missing JIRA_URL, JIRA_PROJECT_KEY or JIRA_AUTH_TOKEN"
        )

    issues = fetch_all_issues(jira_url, project_key, auth_token)
    return [
        {
            "key": i.key,
            "summary": i.summary,
            "description": i.description,
            "status": i.status,
        }
        for i in issues
    ]


if __name__ == "__main__":
    # Example usage: print all issues as JSON
    for issue in get_roadmap_ideas():
        print(issue)
