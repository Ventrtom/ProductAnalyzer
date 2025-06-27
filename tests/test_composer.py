import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ideas.composer import IdeaComposer
import pytest


def test_compose_fields_and_order():
    composer = IdeaComposer()
    inputs = [
        {
            "title": "Idea 1",
            "problem": "Problem 1",
            "proposal": "Proposal 1",
            "business_value": "Value 1",
            "confidence_score": 0.9,
        },
        None,
        {
            "summary": "Idea 2 summary",
            "problem": "Problem 2",
            "proposal": "Proposal 2",
            "confidence_score": 0.8,
        },
        123,
        {
            "title": "Idea 3",
            "proposal": "Proposal 3",
        },
    ]

    result = composer.compose(inputs)

    assert len(result) == 3

    expected_titles = [
        "Idea 1",
        "Idea 2 summary",
        "Idea 3",
    ]

    for out, expected_title in zip(result, expected_titles):
        assert out["title"] == expected_title
        assert isinstance(out.get("id"), str)
        assert isinstance(out.get("markdown"), str)
        assert isinstance(out.get("metadata"), dict)


def test_compose_ignores_invalid_items():
    composer = IdeaComposer()
    data = [None, {"title": "Valid"}, "text", 42]

    result = composer.compose(data)

    assert len(result) == 1
    assert result[0]["title"] == "Valid"
