import json
import sys
from pathlib import Path
from unittest.mock import MagicMock
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Provide environment variables so the retriever module loads
os.environ.setdefault("JIRA_URL", "https://jira.example.com")
os.environ.setdefault("JIRA_PROJECT_KEY", "PRJ")
os.environ.setdefault("JIRA_AUTH_TOKEN", "token")

from retrievers import jira_retriever

# Older orchestrator versions import ``get_roadmap_ideas`` while newer use
# ``fetch_all_issues``. Ensure the expected symbol exists before import.
if not hasattr(jira_retriever, "get_roadmap_ideas"):
    jira_retriever.get_roadmap_ideas = jira_retriever.fetch_all_issues

import orchestrator
from orchestrator import AgentOrchestrator


def test_run_agent_with_mocks(tmp_path, monkeypatch):
    # Run in temporary directory so output files are created there
    monkeypatch.chdir(tmp_path)

    docs = [{"title": "Doc", "content": "doc"}]
    issues = [{"key": "PRJ-1", "summary": "old"}]
    ideas = [
        {
            "title": "New Idea",
            "problem": "p",
            "proposal": "pr",
            "business_value": "bv",
            "confidence_score": 0.8,
        }
    ]

    retrieve_mock = MagicMock(return_value=docs)
    issues_mock = MagicMock(return_value=issues)
    analyze_mock = MagicMock(return_value=ideas)

    def export_mock(items, path):
        # Write a simple file to emulate export
        with open(path, "w", encoding="utf-8") as f:
            for item in items:
                f.write(f"{item}\n")

    export_magic = MagicMock(side_effect=export_mock)

    monkeypatch.setattr(orchestrator, "retrieve_roadmap_documents", retrieve_mock)
    func = "fetch_all_issues" if hasattr(orchestrator, "fetch_all_issues") else "get_roadmap_ideas"
    monkeypatch.setattr(orchestrator, func, issues_mock)
    monkeypatch.setattr(orchestrator.ReasoningEngine, "analyze", analyze_mock)
    monkeypatch.setattr(orchestrator.IdeaExporter, "export_markdown", export_magic)

    agent = AgentOrchestrator(
        roadmap_url="http://example.com",
        jira_project_key="PRJ",
        jira_url="http://jira.example.com",
        jira_token="token",
    )

    result = agent.run_agent()

    # Verify mocks were called
    retrieve_mock.assert_called_once_with("http://example.com")
    issues_mock.assert_called_once()
    analyze_mock.assert_called_once_with(docs, issues)
    export_magic.assert_called_once()

    out_dir = tmp_path / "output"
    assert (out_dir / "ideas.json").exists()
    assert (out_dir / "ideas.md").exists()

    with open(out_dir / "ideas.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data and data[0]["title"] == "New Idea"
    assert result[0]["title"] == "New Idea"
