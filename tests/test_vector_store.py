import pytest

from rag.vector_store import VectorStore


def test_vector_store_path():
    store = VectorStore(path="my_db")
    assert store.path == "my_db"


def test_methods_do_not_raise():
    store = VectorStore()
    # Should not raise when indexing empty list
    store.index_documents([])
    # Should return empty list without raising
    assert store.similar("test") == []

# TODO: Enable search behaviour tests after implementation
