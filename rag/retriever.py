import os
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

DB_DIR = "faiss_index"

def retrieve_context(query: str, k: int = 3) -> list:
    """Retrieves top-k relevant chunks from FAISS for a given query."""
    if not os.path.exists(DB_DIR):
        # Return empty if DB is not initialized to allow fallback
        return []
        
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    try:
        vectorstore = FAISS.load_local(DB_DIR, embeddings, allow_dangerous_deserialization=True)
        docs = vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]
    except Exception as e:
        print(f"Error during retrieval: {e}")
        return []
