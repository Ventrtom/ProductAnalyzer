"""Agent orchestrator module.

This module controls the flow between retrievers, reasoning, and exporting
components. The current implementation provides a very small pipeline that can
fetch data, run a reasoning engine and print/store the resulting ideas.
"""

from __future__ import annotations

import json
import os
from typing import List

from dotenv import load_dotenv

from deduplication.checker import DeduplicationChecker
from ideas.composer import IdeaComposer
from llm_modules.reasoning import ReasoningEngine
from output.export import IdeaExporter
from retrievers.jira_retriever import get_roadmap_ideas
from retrievers.roadmap_retriever import retrieve_roadmap_documents


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
        )
        print(f"Fetched {len(jira_issues)} issues")

        print("\n== Running reasoning engine ==")
        ideas = self.reasoning.analyze(roadmap_docs, jira_issues)

        # Placeholder: integrate deduplication layer here
        # ideas = [i for i in ideas if not self.dedup_checker.is_duplicate(i)]

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

        return composed


def main() -> None:
    """Entry point for CLI execution."""

    load_dotenv()

    roadmap_url = os.getenv("ROADMAP_URL", "http://localhost:8000")
    jira_url = os.getenv("JIRA_URL")
    jira_project = os.getenv("JIRA_PROJECT_KEY", "PROJ")
    jira_token = os.getenv("JIRA_AUTH_TOKEN")

    orchestrator = AgentOrchestrator(
        roadmap_url=roadmap_url,
        jira_project_key=jira_project,
        jira_url=jira_url,
        jira_token=jira_token,
    )
    orchestrator.run_agent()


if __name__ == "__main__":
    main()
