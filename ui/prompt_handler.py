"""User interface module.

Handles user input via CLI or Streamlit and converts it into task prompts
for the agent orchestrator.
"""


class PromptHandler:
    """Collects and formats user prompts."""

    def __init__(self) -> None:
        pass

    def get_prompt(self) -> str:
        """Return the user's prompt.

        For now this returns a static placeholder string.
        """
        return "Generate new product ideas based on documentation and JIRA tickets."
