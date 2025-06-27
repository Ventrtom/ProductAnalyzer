from __future__ import annotations
import os
import sys
import json
from typing import Any, Dict, List, Callable
from tenacity import retry, stop_after_attempt, wait_random_exponential
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError, RateLimitError

# Tool function imports
from retrievers.jira_retriever import fetch_jira_issues
from retrievers.roadmap_retriever import retrieve_roadmap_documents
from retrievers.competitor_scraper import fetch_competitors

from llm_modules.reasoning import generate_new_ideas
from deduplication.checker import DeduplicationChecker
from ideas.composer import IdeaComposer
from output.export import IdeaExporter
from feedback.collector import collect_ratings


def _tool_fetch_roadmap(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetch roadmap documents using provided URL.
    """
    url = params.get("roadmap_url")
    if not url:
        raise ValueError("Parameter 'roadmap_url' is required")
    docs = retrieve_roadmap_documents(url)
    return docs


def _tool_fetch_jira(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetch JIRA issues based on a JQL query.
    """
    jql = params.get("jql")
    if not jql:
        raise ValueError("Parameter 'jql' is required")
    max_results = params.get("max_results", 50)
    issues = fetch_jira_issues(jql=jql, max_results=max_results)
    return issues

# Register additional tools as needed
TOOLS: Dict[str, Callable] = {
    "fetch_roadmap": _tool_fetch_roadmap,
    "fetch_jira": _tool_fetch_jira,
    "fetch_competitors": fetch_competitors,
}

class AgentOrchestrator:
    """Dynamic AI agent orchestrator using OpenAI function calling."""

    def __init__(self) -> None:
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.dedup = DeduplicationChecker()
        self.composer = IdeaComposer()
        self.exporter = IdeaExporter()

    def _build_tool_descriptions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "fetch_roadmap",
                "description": "Fetch roadmap documents from a given URL.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "roadmap_url": {"type": "string", "description": "URL of the roadmap document"}
                    },
                    "required": ["roadmap_url"]
                }
            },
            {
                "name": "fetch_jira",
                "description": "Fetch Jira issues matching a JQL query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "jql": {"type": "string", "description": "Jira Query Language string to filter issues"},
                        "max_results": {"type": "integer", "description": "Maximum number of issues to fetch"}
                    },
                    "required": ["jql"]
                }
            },
            {
                "name": "fetch_competitors",
                "description": "Fetch top competitors for a given product or domain via web-based GPT.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_name": {"type": "string", "description": "Name of the product or domain"},
                        "max_results": {"type": "integer", "description": "Number of competitors to return"}
                    },
                    "required": ["product_name"]
                }
            }
        ]

    @retry(stop=stop_after_attempt(4), wait=wait_random_exponential(min=1, max=10))
    def run(self, goal: str) -> None:
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": "You are an AI agent that plans and executes tools to achieve a user goal."},
            {"role": "user", "content": goal},
        ]

        # loop until done
        for _ in range(5):  # max steps
            try:
                response = self.client.chat.completions.create(
                    model=os.getenv("LLM_MODEL", "gpt-4o"),
                    messages=messages,
                    functions=self._build_tool_descriptions(),
                    function_call="auto"
                )
            except RateLimitError as e:
                print("[ERROR] OpenAI RateLimitError:", e)
                print("➡ Možný důvod: používáš project-bound API key bez přiděleného kreditu.")
                print("➡ Řešení: vytvoř nový user-bound klíč (sk-...) a vlož ho do .env")
                raise
            except OpenAIError as e:
                print("[ERROR] OpenAI Error:", e)
                raise

            msg = response.choices[0].message
            if msg.function_call:
                name = msg.function_call.name
                args = json.loads(msg.function_call.arguments)
                result = TOOLS[name](args)
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": name,
                        "arguments": json.dumps(args)
                    }
                })
                messages.append({"role": "function", "name": name, "content": json.dumps(result)})
                continue
            # final response
            print(msg.content)
            return

if __name__ == "__main__":
    orchestrator = AgentOrchestrator()
    orchestrator.run(goal="Generate 3 high-impact roadmap ideas based on the project.")
