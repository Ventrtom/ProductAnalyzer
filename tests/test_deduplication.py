import sys
from pathlib import Path

import pytest

# Ensure project root is on the path when running tests directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from deduplication.checker import DeduplicationChecker


def test_is_duplicate_add_flow_string():
    checker = DeduplicationChecker()
    idea = "Launch new API"
    assert checker.is_duplicate(idea) is False
    checker.add(idea)
    assert checker.is_duplicate(idea) is True


def test_is_duplicate_add_flow_dict():
    checker = DeduplicationChecker()
    idea = {"title": "Improve onboarding"}
    assert checker.is_duplicate(idea) is False
    checker.add(idea)
    # should match regardless of type or case
    assert checker.is_duplicate({"summary": "improve onboarding"}) is True


def test_hash_equivalence_between_dict_and_string():
    checker = DeduplicationChecker()
    idea_dict = {"title": "  My Unique Idea  "}
    idea_str = "my unique idea"
    assert checker._hash_title(idea_dict) == checker._hash_title(idea_str)
