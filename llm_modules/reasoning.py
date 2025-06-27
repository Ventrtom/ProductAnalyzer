from __future__ import annotations

import json
import os
from typing import Dict, List, Any
from tenacity import retry, stop_after_attempt, wait_random_exponential
from openai import OpenAI


class ReasoningEngine:
    """Reasoning engine that generates product roadmap ideas using GPT-4o."""

    def __init__(self, model_name: str = "gpt-4o") -> None:
        self.model_name = model_name
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def analyze(
        self,
        documents: List[Dict[str, Any]],
        jira_issues: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generate new roadmap ideas based on project documentation and existing Jira issues.

        Parameters
        ----------
        documents : List of dicts containing keys like 'title', 'content', or 'body'.
        jira_issues : List of dicts containing 'key', 'summary', 'description', 'status', 'labels'.

        Returns
        -------
        List of idea dicts with keys 'title', 'problem', 'proposal', 'business_value', 'confidence_score'.
        """
        return generate_new_ideas(
            client=self.client,
            model_name=self.model_name,
            docs=documents,
            jira_ideas=jira_issues,
        )


@retry(stop=stop_after_attempt(4), wait=wait_random_exponential(min=1, max=10))
def generate_new_ideas(
    client: OpenAI,
    model_name: str,
    docs: List[Dict[str, Any]],
    jira_ideas: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Generates novel roadmap ideas by prompting GPT-4o with both documentation and
    detailed Jira issue information.
    """
    # Prepare documentation text
    doc_snippets = []
    for d in docs:
        # Join available text fields
        text = d.get("content") or d.get("text") or d.get("body") or ""
        if title := d.get("title"):
            doc_snippets.append(f"### {title}\n{text}")
        else:
            doc_snippets.append(text)
    docs_text = "\n\n".join(doc_snippets)

    # Prepare existing Jira ideas summary
    issue_lines = []
    for issue in jira_ideas:
        key = issue.get("key", "")
        summary = issue.get("summary", "")
        status = issue.get("status", "")
        labels = ", ".join(issue.get("labels", [])) or "-"
        desc = issue.get("description", "-")
        issue_lines.append(
            f"- {key}: {summary} (status: {status}, labels: {labels})\n  Description: {desc}"
        )
    issues_text = "\n".join(issue_lines)

    # Build prompts
    system_prompt = (
        "You are an expert product manager and consultant. Generate strategic, novel product roadmap ideas."
    )
    user_prompt = (
        "Project Documentation:\n" + docs_text +
        "\n\nExisting Jira Issues:\n" + issues_text +
        "\n\nPlease propose 2-5 new, non-overlapping roadmap ideas in JSON array format."
        " Each idea should be an object with keys:\n"
        "  - title: concise idea name\n"
        "  - problem: user or business problem addressed\n"
        "  - proposal: summary of the solution\n"
        "  - business_value: expected impact or ROI\n"
        "  - confidence_score: 0.0-1.0 confidence in this idea."
    )

    # Call OpenAI API
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
    )

    content = response.choices[0].message.content or ""

    try:
        ideas = json.loads(content)
        if isinstance(ideas, dict):
            ideas = [ideas]
        # Validate idea structure
        valid_ideas: List[Dict[str, Any]] = []
        for idea in ideas:
            if all(k in idea for k in [
                "title", "problem", "proposal", "business_value", "confidence_score"
            ]):
                valid_ideas.append(idea)
        return valid_ideas
    except json.JSONDecodeError:
        # If parsing fails, return empty list
        return []
