from __future__ import annotations

import os
from typing import List, Optional, Tuple

from dotenv import load_dotenv
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel

# 1) Načtení .env
load_dotenv()  # pip install python-dotenv

JIRA_URL = os.getenv("JIRA_URL")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
JIRA_AUTH_TOKEN = os.getenv("JIRA_AUTH_TOKEN")

if not (JIRA_URL and JIRA_PROJECT_KEY and JIRA_AUTH_TOKEN):
    raise EnvironmentError(
        "Chybí některé JIRA proměnné v prostředí: "
        "JIRA_URL, JIRA_PROJECT_KEY nebo JIRA_AUTH_TOKEN"
    )

# 2) Helper s retry
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    reraise=True
)
def _jira_get(
    endpoint: str,
    params: dict[str, object],
    *,
    jira_url: str = JIRA_URL,
    auth_token: str = JIRA_AUTH_TOKEN,
) -> dict:
    """Spustí GET na zadaný JIRA endpoint s retry logikou."""

    url = f"{jira_url.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Basic {auth_token}",
        "Accept": "application/json",
    }
    resp = requests.get(url, headers=headers, params=params, timeout=30)
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
    project_key: str = JIRA_PROJECT_KEY,
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
        data = _jira_get(endpoint, params)

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


def _fetch_issues(
    jira_url: str,
    project_key: str,
    auth_token: str,
    jql: str,
    max_results: int,
) -> List[JiraIssue]:
    """Internal helper used by :func:`get_roadmap_ideas`."""

    endpoint = "rest/api/2/search"
    start_at = 0
    issues: List[JiraIssue] = []

    while True:
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "fields": "summary,description,status,labels",
        }
        data = _jira_get(endpoint, params, jira_url=jira_url, auth_token=auth_token)

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
    jql: str | None = None,
    max_results: int = 50,
) -> List[dict]:
    """Return roadmap ideas from JIRA as list of dicts."""

    jira_url = jira_url or os.getenv("JIRA_URL")
    project_key = project_key or os.getenv("JIRA_PROJECT_KEY")
    auth_token = auth_token or os.getenv("JIRA_AUTH_TOKEN")

    if not jira_url or not project_key or not auth_token:
        raise ValueError("Missing JIRA_URL, JIRA_PROJECT_KEY or JIRA_AUTH_TOKEN")

    jql = jql or f"project={project_key}"

    issues = _fetch_issues(jira_url, project_key, auth_token, jql, max_results)
    return [issue.model_dump(exclude={"labels"}) for issue in issues]


class JiraRetriever:
    """Compatibility wrapper for older code."""

    def __init__(self, url: str, username: str, token: str) -> None:
        self.base_url = url.rstrip("/")
        self.token = token

    def fetch_issues(self, project_key: str, max_results: int = 50) -> List[dict]:
        return get_roadmap_ideas(
            jira_url=self.base_url,
            project_key=project_key,
            auth_token=self.token,
            max_results=max_results,
        )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
def _get(url: str, params: dict[str, str], token: str) -> dict:
    """Backward-compatible request helper."""

    headers = {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
    }
    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    # 4) Příklad použití: vypíše všechna issue jako JSON
    all_issues = fetch_all_issues()
    for issue in all_issues:
        print(issue.json())
