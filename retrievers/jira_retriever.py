"""Retrieve issues from a JIRA project via the REST API."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import os

import requests
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv


class JiraRetriever:
    """Simple JIRA REST API client."""

    def __init__(self, url: str, username: str, token: str) -> None:
        """Store authentication details for API calls."""

        self.base_url = url.rstrip("/")
        self.auth: Tuple[str, str] = (username, token)

    def fetch_issues(self, project_key: str, max_results: int = 50) -> List[Dict[str, Optional[str]]]:
        """Return issues for the given project.

        Parameters
        ----------
        project_key:
            Key of the JIRA project.
        max_results:
            Number of issues to request per page.
        """

        search_url = f"{self.base_url}/rest/api/2/search"

        start_at = 0
        issues: List[Dict[str, Optional[str]]] = []

        while True:
            params = {
                "jql": f"project={project_key}",
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "summary,description,status,labels",
            }

            response = requests.get(search_url, params=params, auth=self.auth, timeout=30)
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


class JiraIssue(BaseModel):
    """Representation of a JIRA issue used by ``get_roadmap_ideas``."""

    key: str
    summary: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    roadmap: Optional[str] = None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
def _get(url: str, params: Dict[str, str], token: str) -> Dict:
    """Issue a GET request with retries."""

    headers = {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
    }
    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def get_roadmap_ideas(
    jira_url: Optional[str] = None,
    project_key: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> List[Dict]:
    """Fetch all issues from ``project_key`` and return minimal idea dicts."""

    load_dotenv()
    jira_url = jira_url or os.getenv("JIRA_URL")
    project_key = project_key or os.getenv("JIRA_PROJECT_KEY")
    auth_token = auth_token or os.getenv("JIRA_AUTH_TOKEN")

    if not jira_url or not project_key or not auth_token:
        raise ValueError("Missing JIRA_URL, JIRA_PROJECT_KEY or JIRA_AUTH_TOKEN")

    search_url = jira_url.rstrip("/") + "/rest/api/2/search"

    start_at = 0
    max_results = 50
    issues: List[JiraIssue] = []

    while True:
        params = {
            "jql": f"project={project_key}",
            "startAt": start_at,
            "maxResults": max_results,
            "fields": "summary,description,status,roadmap",
        }

        data = _get(search_url, params, auth_token)

        for issue in data.get("issues", []):
            fields = issue.get("fields", {})
            issues.append(
                JiraIssue(
                    key=issue.get("key"),
                    summary=fields.get("summary"),
                    description=fields.get("description"),
                    status=(fields.get("status") or {}).get("name"),
                    roadmap=fields.get("roadmap"),
                )
            )

        retrieved = start_at + data.get("maxResults", 0)
        total = data.get("total", 0)
        if retrieved >= total:
            break
        start_at = retrieved

    return [issue.dict() for issue in issues]

