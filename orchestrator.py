"""Agent orchestrator module.

This module controls the flow between retrievers, reasoning, and exporting
components. The current implementation provides a very small pipeline that can
fetch data, run a reasoning engine and print/store the resulting ideas.
"""

from __future__ import annotations

import json
import os
import sys
from typing import List

from dotenv import load_dotenv

from deduplication.checker import DeduplicationChecker
from ideas.composer import IdeaComposer
from llm_modules.reasoning import ReasoningEngine
from output.export import IdeaExporter
from feedback.collector import collect_ratings
from retrievers.jira_retriever import get_roadmap_ideas
from retrievers.roadmap_retriever import retrieve_roadmap_documents


def require_env(keys: list[str]) -> None:
    """Ensure required environment variables are present."""

    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        print("Missing required environment variables: " + ", ".join(missing))
        sys.exit(1)


class AgentOrchestrator:
    """Orchestrates the ProductAnalyzer modules."""

    def __init__(
        self,
        roadmap_url: str,
        jira_project_key: str,
        jira_url: str | None = None,
        jira_token: str | None = None,
        model_name: str = "gpt-4o",
    ) -> None:
        """Store configuration and initialise submodules."""

        self.roadmap_url = roadmap_url.rstrip("/")
        self.jira_project_key = jira_project_key
        self.jira_url = jira_url
        self.jira_token = jira_token

        self.reasoning = ReasoningEngine(model_name)

        # Placeholders for future integration
        self.dedup_checker = DeduplicationChecker()
        self.exporter = IdeaExporter()
        self.composer = IdeaComposer()

    def run_agent(self) -> List[dict]:
        """Run the core retrieval and reasoning workflow."""

        print("\n== Retrieving roadmap documentation ==")
        roadmap_docs = retrieve_roadmap_documents(self.roadmap_url)
        print(f"Fetched {len(roadmap_docs)} documents")

        print("\n== Retrieving JIRA issues ==")
        jira_issues = get_roadmap_ideas(
            jira_url=self.jira_url,
            project_key=self.jira_project_key,
            auth_token=self.jira_token,
            # Quote project key to avoid 400 errors if the key contains digits or other characters
            jql=f'project="{self.jira_project_key}"',
        )
        print(f"Fetched {len(jira_issues)} issues")

        print("\n== Running reasoning engine ==")
        ideas = self.reasoning.analyze(roadmap_docs, jira_issues)

        # Filter out ideas we've already seen
        deduped: List[dict] = []
        for idea in ideas:
            if not self.dedup_checker.is_duplicate(idea):
                deduped.append(idea)
                self.dedup_checker.add(idea)
        ideas = deduped

        composed = self.composer.compose(ideas)

        if not composed:
            print("No ideas generated")
        else:
            print("Generated ideas:")
            for idea in composed:
                print(f"- {idea['title']}")

        os.makedirs("output", exist_ok=True)
        with open("output/ideas.json", "w", encoding="utf-8") as f:
            json.dump(composed, f, ensure_ascii=False, indent=2)

        # Export ideas in Markdown format as well
        markdown_items = [idea["markdown"] for idea in composed]
        self.exporter.export_markdown(markdown_items, "output/ideas.md")

        collect_ratings(composed)

        return composed


def main() -> None:
    """Entry point for CLI execution."""

    load_dotenv()

    require_env(
        [
            "JIRA_URL",
            "JIRA_PROJECT_KEY",
            "JIRA_AUTH_TOKEN",
            "OPENAI_API_KEY",
            "ROADMAP_URL",
        ]
    )

    roadmap_url = os.environ["ROADMAP_URL"]
    jira_url = os.environ["JIRA_URL"]
    jira_project = os.environ["JIRA_PROJECT_KEY"]
    jira_token = os.environ["JIRA_AUTH_TOKEN"]

    orchestrator = AgentOrchestrator(
        roadmap_url=roadmap_url,
        jira_project_key=jira_project,
        jira_url=jira_url,
        jira_token=jira_token,
    )
    orchestrator.run_agent()


if __name__ == "__main__":
    main()
