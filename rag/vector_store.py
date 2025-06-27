"""Vector store wrapper for retrieval augmented generation."""


class VectorStore:
    """Placeholder vector store using ChromaDB or similar."""

    def __init__(self, path: str = "db") -> None:
        self.path = path

    def index_documents(self, docs: list) -> None:
        """Index documents into the vector store."""
        pass

    def similar(self, query: str, k: int = 5) -> list:
        """Return top-k similar documents."""
        return []
