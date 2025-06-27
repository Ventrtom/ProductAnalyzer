"""Idea composition module."""


from __future__ import annotations

import uuid
from typing import Any, Dict, List


class IdeaComposer:
    """Creates structured idea proposals."""

    def __init__(self) -> None:
        pass

    def compose(self, ideas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return formatted ideas with metadata.

        Parameters
        ----------
        ideas:
            Raw idea dictionaries typically returned by the reasoning layer.

        Returns
        -------
        List[Dict[str, Any]]
            Each idea enriched with ``id`` and ``markdown`` fields as well as a
            ``metadata`` dictionary.
        """

        formatted: List[Dict[str, Any]] = []

        for raw in ideas:
            if not isinstance(raw, dict):
                # Skip invalid items but continue processing
                continue

            title = raw.get("title") or raw.get("summary") or "Untitled idea"
            problem = raw.get("problem", "")
            proposal = raw.get("proposal", "")
            business_value = raw.get("business_value", "")
            confidence = raw.get("confidence_score")

            markdown = (
                f"* **{title}**\n"
                f"  * Problem: {problem}\n"
                f"  * Proposal: {proposal}\n"
                f"  * Business Value: {business_value}\n"
                f"  * Confidence: {confidence}"
            )

            structured = {
                "id": str(uuid.uuid4()),
                "title": title,
                "markdown": markdown,
                "metadata": {
                    "problem": problem,
                    "proposal": proposal,
                    "business_value": business_value,
                    "confidence_score": confidence,
                },
            }

            formatted.append(structured)

        return formatted
