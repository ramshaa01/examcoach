"""Multi-format Document Ingestion (PDF, TXT, MD) with FAISS + BM25 indexing."""
from __future__ import annotations

import json
import os
import pickle
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi

DATA_DIR = "data"
DB_DIR = "faiss_index"
BM25_FILE = "faiss_index/bm25.pkl"
CORPUS_FILE = "faiss_index/corpus.json"


def load_documents_from_data_dir() -> List:
    """Loads all supported documents (.pdf, .txt, .md) from data/ directory."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        return []

    documents = []
    for fname in os.listdir(DATA_DIR):
        fpath = os.path.join(DATA_DIR, fname)
        if not os.path.isfile(fpath):
            continue

        try:
            if fname.lower().endswith(".pdf"):
                loader = PyPDFLoader(fpath)
                docs = loader.load()
                for d in docs:
                    d.metadata["source_file"] = fname
                documents.extend(docs)
            elif fname.lower().endswith((".txt", ".md")):
                loader = TextLoader(fpath, encoding="utf-8")
                docs = loader.load()
                for d in docs:
                    d.metadata["source_file"] = fname
                documents.extend(docs)
        except Exception as exc:
            print(f"Error loading {fname}: {exc}")

    return documents


def ingest_documents() -> bool:
    """Chunks documents, builds FAISS dense index, and builds BM25 sparse index."""
    documents = load_documents_from_data_dir()
    if not documents:
        print("No documents found in data/ folder.")
        return False

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""],
    )
    docs = text_splitter.split_documents(documents)
    if not docs:
        return False

    os.makedirs(DB_DIR, exist_ok=True)

    # 1. FAISS Dense Index
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vectorstore = FAISS.from_documents(docs, embeddings)
        vectorstore.save_local(DB_DIR)
    except Exception as exc:
        print(f"FAISS index build error (embedding key check): {exc}")
        # Proceed with BM25 even if FAISS fails
        pass

    # 2. BM25 Sparse Index & Corpus Store
    corpus_texts = [d.page_content for d in docs]
    corpus_metadata = [d.metadata for d in docs]
    tokenized_corpus = [doc.lower().split() for doc in corpus_texts]

    bm25 = BM25Okapi(tokenized_corpus)

    with open(BM25_FILE, "wb") as f:
        pickle.dump(bm25, f)

    with open(CORPUS_FILE, "w", encoding="utf-8") as f:
        json.dump({"texts": corpus_texts, "metadata": corpus_metadata}, f)

    print(f"Successfully ingested {len(documents)} source files into {len(docs)} chunks.")
    return True


if __name__ == "__main__":
    ingest_documents()
