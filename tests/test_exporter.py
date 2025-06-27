import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from output.export import IdeaExporter

def test_export_markdown_creates_file_with_content(tmp_path):
    exporter = IdeaExporter()
    ideas = ["First idea", "Second idea"]
    file_path = tmp_path / "ideas.md"

    exporter.export_markdown(ideas, str(file_path))

    assert file_path.exists()
    expected = "- First idea\n- Second idea\n"
    assert file_path.read_text(encoding="utf-8") == expected
