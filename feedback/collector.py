from __future__ import annotations

import json
import os
from typing import List, Dict


def collect_ratings(ideas: List[Dict]) -> None:
    """Prompt the user to rate each idea and store the ratings."""

    ratings = []
    for idea in ideas:
        title = idea.get("title", "Idea")
        idea_id = idea.get("id")
        while True:
            try:
                value = int(input(f"Rate idea '{title}' (1-5): "))
                if 1 <= value <= 5:
                    break
            except ValueError:
                pass
            print("Please enter a number between 1 and 5.")
        ratings.append({"id": idea_id, "rating": value})

    os.makedirs("output", exist_ok=True)
    with open("output/feedback.json", "w", encoding="utf-8") as f:
        json.dump(ratings, f, ensure_ascii=False, indent=2)
