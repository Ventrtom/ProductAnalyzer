import sys, os, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import os
from retrievers.jira_retriever import JiraRetriever, _get, get_roadmap_ideas
import requests
import requests_mock
import pytest
import tenacity


def test_fetch_issues_pagination():
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
        m.get(search_url, [
            {"json": page1, "status_code": 200},
            {"json": page2, "status_code": 200},
        ])

        retriever = JiraRetriever(base_url, "user", "token")
        issues = retriever.fetch_issues("PRJ", max_results=2)

        assert len(issues) == 3
        assert issues[0]["key"] == "PRJ-1"
        assert issues[1]["summary"] == "S2"
        assert issues[2]["status"] == "Done"

        starts = [int(r.qs["startat"][0]) for r in m.request_history]
        assert starts == [0, 2]


def test__get_success_and_error(monkeypatch):
    url = "https://api.example.com"
    params = {"a": "1"}
    token = "tok"

    with requests_mock.Mocker() as m:
        m.get(url, json={"ok": True}, status_code=200)
        result = _get(url, params, token)
        assert result == {"ok": True}
        assert m.last_request.headers["Authorization"] == f"Basic {token}"

    with requests_mock.Mocker() as m:
        m.get(url, status_code=500)
        _get.retry.stop = tenacity.stop_after_attempt(1)
        _get.retry.wait = tenacity.wait_none()
        with pytest.raises(requests.HTTPError):
            _get(url, params, token)


def test_get_roadmap_ideas_env_and_missing(monkeypatch):
    url = "https://jira.example.com"
    project = "PRJ"
    token = "tok"
    search_url = url + "/rest/api/2/search"

    monkeypatch.setenv("JIRA_URL", url)
    monkeypatch.setenv("JIRA_PROJECT_KEY", project)
    monkeypatch.setenv("JIRA_AUTH_TOKEN", token)

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
        issues = get_roadmap_ideas()
        assert issues == [
            {
                "key": "PRJ-1",
                "summary": "S1",
                "description": "D1",
                "status": "Todo",
            }
        ]

    monkeypatch.delenv("JIRA_URL")
    monkeypatch.delenv("JIRA_PROJECT_KEY")
    monkeypatch.delenv("JIRA_AUTH_TOKEN")
    with pytest.raises(ValueError):
        get_roadmap_ideas()
