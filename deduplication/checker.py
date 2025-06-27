"""Deduplication layer for idea checking."""


import hashlib
from typing import Dict, Set


class DeduplicationChecker:
    """Simple in-memory deduplication checker."""

    def __init__(self) -> None:
        """Initialize storage for seen idea hashes."""
        self._seen_hashes: Set[str] = set()

    def _hash_title(self, idea: Dict | str) -> str:
        """Return a stable hash for the given idea's title."""

        if isinstance(idea, dict):
            title = idea.get("title") or idea.get("summary") or str(idea)
        else:
            title = str(idea)

        normalized = title.strip().lower()
        return hashlib.sha1(normalized.encode("utf-8")).hexdigest()

    def add(self, idea: Dict | str) -> None:
        """Add an idea to the seen set."""

        self._seen_hashes.add(self._hash_title(idea))

    def is_duplicate(self, idea: Dict | str) -> bool:
        """Return ``True`` if the idea title has been seen before."""

        return self._hash_title(idea) in self._seen_hashes
