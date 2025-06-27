import os
import sys

import pytest

# Ensure the project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui.prompt_handler import PromptHandler


def test_get_prompt_returns_expected_value():
    handler = PromptHandler()
    prompt = handler.get_prompt()
    assert prompt == "Generate new product ideas based on documentation and JIRA tickets."
