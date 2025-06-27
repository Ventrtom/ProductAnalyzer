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
    auth_token: str = JIRA_AUTH_TOKEN,
) -> dict:
    """
    Spustí GET na zadaný JIRA endpoint s retry logikou.
    """
    url = f"{JIRA_URL.rstrip('/')}/{endpoint.lstrip('/')}"
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


if __name__ == "__main__":
    # 4) Příklad použití: vypíše všechna issue jako JSON
    all_issues = fetch_all_issues()
    for issue in all_issues:
        print(issue.json())
