import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from feedback.collector import collect_ratings


def test_collect_ratings_writes_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    inputs = iter(["5", "3"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    ideas = [
        {"id": "1", "title": "Idea 1"},
        {"id": "2", "title": "Idea 2"},
    ]

    collect_ratings(ideas)

    fb_path = tmp_path / "output" / "feedback.json"
    assert fb_path.exists()
    data = json.loads(fb_path.read_text(encoding="utf-8"))
    assert data == [{"id": "1", "rating": 5}, {"id": "2", "rating": 3}]
