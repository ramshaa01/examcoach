"""Hybrid Retriever combining Dense (FAISS) + Sparse (BM25) search with source citations."""
from __future__ import annotations

import json
import os
import pickle
from typing import List, Tuple

from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

DB_DIR = "faiss_index"
BM25_FILE = "faiss_index/bm25.pkl"
CORPUS_FILE = "faiss_index/corpus.json"


def retrieve_dense_faiss(query: str, k: int = 3) -> List[Tuple[str, str]]:
    """Fetches top-k from FAISS dense vector store: returns list of (content, source)."""
    if not os.path.exists(os.path.join(DB_DIR, "index.faiss")):
        return []

    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vectorstore = FAISS.load_local(DB_DIR, embeddings, allow_dangerous_deserialization=True)
        docs = vectorstore.similarity_search(query, k=k)
        results = []
        for d in docs:
            src = d.metadata.get("source_file", "Notes")
            page = d.metadata.get("page", None)
            citation = f"{src} (Page {page + 1})" if page is not None else src
            results.append((d.page_content, citation))
        return results
    except Exception as exc:
        print(f"FAISS retrieval note: {exc}")
        return []


def retrieve_sparse_bm25(query: str, k: int = 3) -> List[Tuple[str, str]]:
    """Fetches top-k from BM25 sparse index: returns list of (content, source)."""
    if not (os.path.exists(BM25_FILE) and os.path.exists(CORPUS_FILE)):
        return []

    try:
        with open(BM25_FILE, "rb") as f:
            bm25 = pickle.load(f)

        with open(CORPUS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        texts = data.get("texts", [])
        metas = data.get("metadata", [])
        if not texts:
            return []

        tokenized_query = query.lower().split()
        scores = bm25.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0.05:
                meta = metas[idx] if idx < len(metas) else {}
                src = meta.get("source_file", "Notes")
                page = meta.get("page", None)
                citation = f"{src} (Page {page + 1})" if page is not None else src
                results.append((texts[idx], citation))
        return results
    except Exception as exc:
        print(f"BM25 retrieval note: {exc}")
        return []


def retrieve_context(query: str, k: int = 3) -> List[str]:
    """Hybrid search combining FAISS dense embeddings and BM25 keyword matching with citation chips."""
    if not query.strip():
        return []

    dense_results = retrieve_dense_faiss(query, k=k)
    sparse_results = retrieve_sparse_bm25(query, k=k)

    # Merge & deduplicate by content prefix
    seen_prefixes = set()
    combined_chunks: List[str] = []

    for content, citation in dense_results + sparse_results:
        clean_content = content.strip()
        prefix = clean_content[:80]
        if prefix not in seen_prefixes:
            seen_prefixes.add(prefix)
            formatted = f"📌 [Source: {citation}]\n{clean_content}"
            combined_chunks.append(formatted)

        if len(combined_chunks) >= k:
            break

    return combined_chunks
