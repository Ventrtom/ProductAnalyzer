"""Output exporters for ProductAnalyzer."""


class IdeaExporter:
    """Exports ideas to various formats."""

    def __init__(self) -> None:
        pass

    def export_markdown(self, ideas: list, path: str) -> None:
        """Export ideas as a Markdown file."""
        with open(path, "w", encoding="utf-8") as f:
            for idea in ideas:
                f.write(f"- {idea}\n")
