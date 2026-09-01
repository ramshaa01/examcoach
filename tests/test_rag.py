"""Unit tests for RAG ingestion and hybrid (FAISS + BM25) retrieval."""
from rag.retriever import retrieve_context


def test_empty_retrieval_returns_empty_list():
    res = retrieve_context("")
    assert res == []


def test_retrieval_graceful_fallback():
    # Even if FAISS index has no items or fails to load, retrieve_context should not crash
    res = retrieve_context("NonexistentQuery12345")
    assert isinstance(res, list)


class _FailingEmbeddings:
    """Stands in for GoogleGenerativeAIEmbeddings so tests never hit the network."""

    def __init__(self, *args, **kwargs):
        raise RuntimeError("no network access in tests")


def test_ingest_documents_builds_bm25_index(tmp_path, monkeypatch):
    import rag.ingestion as ingestion

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "notes.txt").write_text(
        "Newton's second law states that force equals mass times acceleration. "
        "This principle underlies JEE Physics mechanics problems.",
        encoding="utf-8",
    )
    db_dir = tmp_path / "faiss_index"

    monkeypatch.setattr(ingestion, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(ingestion, "DB_DIR", str(db_dir))
    monkeypatch.setattr(ingestion, "BM25_FILE", str(db_dir / "bm25.pkl"))
    monkeypatch.setattr(ingestion, "CORPUS_FILE", str(db_dir / "corpus.json"))
    monkeypatch.setattr(ingestion, "GoogleGenerativeAIEmbeddings", _FailingEmbeddings)

    assert ingestion.ingest_documents() is True
    assert (db_dir / "bm25.pkl").exists()
    assert (db_dir / "corpus.json").exists()


def test_hybrid_retrieval_finds_ingested_chunk_via_bm25(tmp_path, monkeypatch):
    import rag.ingestion as ingestion
    import rag.retriever as retriever

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "biology.md").write_text(
        "Photosynthesis converts light energy into chemical energy inside chloroplasts.",
        encoding="utf-8",
    )
    db_dir = tmp_path / "faiss_index"

    monkeypatch.setattr(ingestion, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(ingestion, "DB_DIR", str(db_dir))
    monkeypatch.setattr(ingestion, "BM25_FILE", str(db_dir / "bm25.pkl"))
    monkeypatch.setattr(ingestion, "CORPUS_FILE", str(db_dir / "corpus.json"))
    monkeypatch.setattr(ingestion, "GoogleGenerativeAIEmbeddings", _FailingEmbeddings)
    monkeypatch.setattr(retriever, "DB_DIR", str(db_dir))
    monkeypatch.setattr(retriever, "BM25_FILE", str(db_dir / "bm25.pkl"))
    monkeypatch.setattr(retriever, "CORPUS_FILE", str(db_dir / "corpus.json"))

    assert ingestion.ingest_documents() is True

    results = retriever.retrieve_sparse_bm25("photosynthesis chloroplasts", k=1)
    assert results
    assert "photosynthesis" in results[0][0].lower()

    combined = retriever.retrieve_context("photosynthesis chloroplasts", k=1)
    assert combined
    assert "photosynthesis" in combined[0].lower()
