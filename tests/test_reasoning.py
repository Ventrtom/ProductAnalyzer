import json
from types import SimpleNamespace

import llm_modules.reasoning as reasoning


def make_mock_openai(response_content):
    def mock_create(*args, **kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=response_content))]
        )

    def mock_openai(*args, **kwargs):
        return SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=mock_create))
        )

    return mock_openai


def test_generate_new_ideas_valid_json(monkeypatch):
    expected = [
        {
            "title": "Idea",
            "problem": "A problem",
            "proposal": "A proposal",
            "business_value": "High",
            "confidence_score": 0.8,
        }
    ]
    mock_openai = make_mock_openai(json.dumps(expected))
    monkeypatch.setattr(reasoning, "OpenAI", mock_openai)
    ideas = reasoning.generate_new_ideas([{"content": "doc"}], [])
    assert ideas == expected


def test_generate_new_ideas_invalid_json(monkeypatch):
    mock_openai = make_mock_openai("not valid")
    monkeypatch.setattr(reasoning, "OpenAI", mock_openai)
    ideas = reasoning.generate_new_ideas([{"content": "doc"}], [])
    assert ideas == []
