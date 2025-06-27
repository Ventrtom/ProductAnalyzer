import sys
import os
import pathlib

# Ensure project root is on the path before importing the retriever
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

# Provide dummy environment so ``jira_retriever`` does not fail on import
os.environ.setdefault("JIRA_URL", "https://jira.example.com")
os.environ.setdefault("JIRA_PROJECT_KEY", "PRJ")
os.environ.setdefault("JIRA_AUTH_TOKEN", "token")

from retrievers import jira_retriever
from retrievers.jira_retriever import fetch_all_issues, _jira_get
import requests
import requests_mock
import pytest
import tenacity


def test_fetch_issues_pagination(monkeypatch):
    base_url = "https://jira.example.com"
    search_url = base_url + "/rest/api/2/search"

    page1 = {
        "issues": [
            {
                "key": "PRJ-1",
                "fields": {
                    "summary": "S1",
                    "description": "D1",
                    "status": {"name": "Todo"},
                    "labels": ["l1"],
                },
            },
            {
                "key": "PRJ-2",
                "fields": {
                    "summary": "S2",
                    "description": None,
                    "status": {"name": "Doing"},
                    "labels": [],
                },
            },
        ],
        "startAt": 0,
        "maxResults": 2,
        "total": 3,
    }

    page2 = {
        "issues": [
            {
                "key": "PRJ-3",
                "fields": {
                    "summary": "S3",
                    "description": "D3",
                    "status": {"name": "Done"},
                    "labels": ["l3"],
                },
            }
        ],
        "startAt": 2,
        "maxResults": 2,
        "total": 3,
    }

    with requests_mock.Mocker() as m:
        m.get(
            search_url,
            [
                {"json": page1, "status_code": 200},
                {"json": page2, "status_code": 200},
            ],
        )

        monkeypatch.setattr(jira_retriever, "JIRA_URL", base_url)

        issues = fetch_all_issues("PRJ", max_results=2)

        assert len(issues) == 3
        assert issues[0].key == "PRJ-1"
        assert issues[1].summary == "S2"
        assert issues[2].status == "Done"

        starts = [int(r.qs["startat"][0]) for r in m.request_history]
        assert starts == [0, 2]


def test__jira_get_success_and_error(monkeypatch):
    url = "https://api.example.com"
    params = {"a": "1"}
    token = "tok"

    monkeypatch.setattr(jira_retriever, "JIRA_URL", url)

    with requests_mock.Mocker() as m:
        m.get(url + "/", json={"ok": True}, status_code=200)
        result = _jira_get("", params, token)
        assert result == {"ok": True}
        assert m.last_request.headers["Authorization"] == f"Basic {token}"

    with requests_mock.Mocker() as m:
        m.get(url + "/", status_code=500)
        _jira_get.retry.stop = tenacity.stop_after_attempt(1)
        _jira_get.retry.wait = tenacity.wait_none()
        with pytest.raises(requests.HTTPError):
            _jira_get("", params, token)


def test_fetch_all_issues(monkeypatch):
    url = "https://jira.example.com"
    project = "PRJ"
    search_url = url + "/rest/api/2/search"

    monkeypatch.setattr(jira_retriever, "JIRA_URL", url)

    data = {
        "issues": [
            {
                "key": "PRJ-1",
                "fields": {
                    "summary": "S1",
                    "description": "D1",
                    "status": {"name": "Todo"},
                },
            }
        ],
        "startAt": 0,
        "maxResults": 50,
        "total": 1,
    }

    with requests_mock.Mocker() as m:
        m.get(search_url, json=data, status_code=200)
        issues = fetch_all_issues(project_key=project)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.key == "PRJ-1"
        assert issue.summary == "S1"
        assert issue.description == "D1"
        assert issue.status == "Todo"
