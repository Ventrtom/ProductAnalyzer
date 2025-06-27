# jira_retriever.py

from __future__ import annotations

"""Retrieve JIRA issues for the orchestrator."""

import os
import logging
from typing import List, Optional

import requests
from requests.exceptions import HTTPError
from dotenv import load_dotenv
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

JIRA_URL = os.getenv("JIRA_URL")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
JIRA_AUTH_TOKEN = os.getenv("JIRA_AUTH_TOKEN")
# Optional JQL query overriding the project key
JIRA_JQL = os.getenv("JIRA_JQL")

if not JIRA_URL or not JIRA_AUTH_TOKEN:
    raise EnvironmentError("JIRA_URL and JIRA_AUTH_TOKEN must be set")

logger.debug(
    "Environment loaded JIRA_URL=%s JIRA_PROJECT_KEY=%s JIRA_JQL=%s",
    JIRA_URL,
    JIRA_PROJECT_KEY,
    JIRA_JQL,
)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
def _jira_get(
    endpoint: str,
    params: dict[str, object],
    auth_token: str | None = None,
    *,
    jira_url: str | None = None,
) -> dict:
    """Low level GET helper with retry."""

    jira_url = jira_url or JIRA_URL
    auth_token = auth_token or JIRA_AUTH_TOKEN

    url = f"{jira_url.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Basic {auth_token}",
        "Accept": "application/json",
    }

    logger.debug(
        "_jira_get called with endpoint=%s jira_url=%s params=%s",
        endpoint,
        jira_url,
        params,
    )
    logger.debug("Request URL: %s", url)

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    logger.debug("Response status: %s", resp.status_code)
    resp.raise_for_status()
    data = resp.json()
    logger.debug("Response JSON: %s", data)
    return data

class JiraIssue(BaseModel):
    key: str
    summary: Optional[str]
    description: Optional[str]
    status: Optional[str]
    labels: Optional[List[str]]

def _fetch_issues(jira_url: str, auth_token: str, jql: str, max_results: int) -> List[JiraIssue]:
    """Fetch issues from JIRA using the given JQL query."""

    endpoint = "rest/api/2/search"
    start_at = 0
    issues: List[JiraIssue] = []

    logger.debug(
        "Starting issue fetch with jql=%s max_results=%d",
        jql,
        max_results,
    )

    while True:
        logger.debug("Fetching page starting at %d", start_at)
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "fields": "summary,description,status,labels",
        }
        logger.debug("Request params: %s", params)
        try:
            data = _jira_get(endpoint, params, auth_token, jira_url=jira_url)
        except HTTPError as e:
            logger.error("JIRA Error response: %s", e.response.text)
            raise

        logger.debug("Received %d issues", len(data.get("issues", [])))
        for raw in data.get("issues", []):
            logger.debug("Processing raw issue: %s", raw.get("key"))
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

    logger.debug("Total issues fetched: %d", len(issues))
    return issues

def fetch_all_issues(project_key: str = JIRA_PROJECT_KEY, max_results: int = 50) -> List[JiraIssue]:
    """Compatibility wrapper returning all issues for a project."""

    if not project_key:
        raise ValueError("Project key must be provided when JIRA_JQL is not used")
    # Quote the project key to avoid JQL syntax errors for non-alphanumeric keys
    jql = f'project="{project_key}"'
    logger.debug(
        "fetch_all_issues called with project_key=%s max_results=%d",
        project_key,
        max_results,
    )
    return _fetch_issues(JIRA_URL, JIRA_AUTH_TOKEN, jql, max_results)

def get_roadmap_ideas(
    jira_url: str | None = None,
    project_key: str | None = None,
    auth_token: str | None = None,
    jql: str | None = None,
    max_results: int = 50,
) -> List[dict]:
    """Return roadmap ideas from JIRA as list of plain dicts."""

    jira_url = jira_url or JIRA_URL
    auth_token = auth_token or JIRA_AUTH_TOKEN
    project_key = project_key or JIRA_PROJECT_KEY
    if jql:
        final_jql = jql
    elif JIRA_JQL:
        final_jql = JIRA_JQL
    elif project_key:
        # Quote the project key to avoid issues with numeric or special keys
        final_jql = f'project="{project_key}"'
    else:
        final_jql = None

    logger.debug(
        "get_roadmap_ideas called with jira_url=%s project_key=%s jql=%s max_results=%d",
        jira_url,
        project_key,
        jql,
        max_results,
    )

    if not jira_url or not auth_token:
        raise ValueError("Missing JIRA_URL or JIRA_AUTH_TOKEN")
    if not final_jql:
        raise ValueError("JQL query could not be determined")

    issues = _fetch_issues(jira_url, auth_token, final_jql, max_results)
    result = [issue.model_dump(exclude={"labels"}) for issue in issues]
    logger.debug("Returning %d roadmap ideas", len(result))
    return result

class JiraRetriever:
    """Backward compatible class-based API."""

    def __init__(self, url: str, username: str, token: str) -> None:
        self.base_url = url.rstrip("/")
        self.token = token
        logger.debug(
            "Initialized JiraRetriever with base_url=%s username=%s",
            self.base_url,
            username,
        )

    def fetch_issues(self, project_key: str, max_results: int = 50) -> List[dict]:
        logger.debug(
            "JiraRetriever.fetch_issues called with project_key=%s max_results=%d",
            project_key,
            max_results,
        )
        return get_roadmap_ideas(
            jira_url=self.base_url,
            project_key=project_key,
            auth_token=self.token,
            max_results=max_results,
        )

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
def _get(url: str, params: dict[str, str], token: str) -> dict:
    """Legacy helper kept for compatibility."""
    headers = {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
    }
    logger.debug(
        "_get called with url=%s params=%s token_provided=%s",
        url,
        params,
        bool(token),
    )
    resp = requests.get(url, params=params, headers=headers, timeout=30)
    logger.debug("Legacy _get response status: %s", resp.status_code)
    resp.raise_for_status()
    data = resp.json()
    logger.debug("Legacy _get response JSON: %s", data)
    return data

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    issues = get_roadmap_ideas()
    for issue in issues:
        print(issue)
