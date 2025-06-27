"""Reasoning module using OpenAI GPT-4o."""

from __future__ import annotations

import json
from typing import Dict, List

from openai import OpenAI


class ReasoningEngine:
    """Placeholder reasoning engine."""

    def __init__(self, model_name: str = "gpt-4o") -> None:
        self.model_name = model_name

    def analyze(self, documents: list) -> list:
        """Return list of proposed ideas based on input documents."""
        return []


def generate_new_ideas(docs: List[Dict], jira_ideas: List[Dict]) -> List[Dict]:
    """Generate 2-3 novel roadmap ideas using GPT-4o.

    Parameters
    ----------
    docs:
        List of documentation snippets or pages.
    jira_ideas:
        Existing JIRA ideas to avoid duplicating.

    Returns
    -------
    List[Dict]
        Newly proposed ideas each containing ``title``, ``problem``, ``proposal``,
        ``business_value`` and ``confidence_score``.
    """

    client = OpenAI()  # API key expected via ``OPENAI_API_KEY`` environment var

    existing_titles = [
        idea.get("title") or idea.get("summary") or "" for idea in jira_ideas
    ]
    doc_text = "\n".join(
        d.get("content")
        or d.get("text")
        or d.get("body", "")
        or json.dumps(d)
        for d in docs
    )

    system_prompt = (
        "You are an expert product manager tasked with generating new roadmap "
        "ideas. The suggestions must not overlap with existing JIRA ideas."
    )
    user_prompt = (
        "Documentation:\n" + doc_text + "\n\n" +
        "Existing JIRA ideas:\n" + "\n".join(f"- {t}" for t in existing_titles) +
        "\n\nGenerate 2-3 new roadmap ideas in JSON format. "
        "Each idea must contain the keys 'title', 'problem', 'proposal', "
        "'business_value', and 'confidence_score'."
    )

    response = client.chat.completions.create(
        model="gpt-4o",
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
        return ideas
    except json.JSONDecodeError:
        return []
