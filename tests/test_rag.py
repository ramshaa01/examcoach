"""Unit tests for RAG retriever and hybrid search logic."""
from rag.retriever import retrieve_context


def test_empty_retrieval_returns_empty_list():
    res = retrieve_context("")
    assert res == []


def test_retrieval_graceful_fallback():
    # Even if FAISS index has no items or fails to load, retrieve_context should not crash
    res = retrieve_context("NonexistentQuery12345")
    assert isinstance(res, list)
