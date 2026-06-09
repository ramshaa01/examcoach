import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

DATA_DIR = "data"
DB_DIR = "faiss_index"

def ingest_documents():
    """Reads PDFs, chunks them, and creates FAISS index."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Please place PDFs in '{DATA_DIR}' directory.")
        return False
        
    papers = [f for f in os.listdir(DATA_DIR) if f.endswith('.pdf')]
    if not papers:
        print("No PDFs found.")
        return False

    documents = []
    for paper in papers:
        loader = PyPDFLoader(os.path.join(DATA_DIR, paper))
        documents.extend(loader.load())

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(DB_DIR)
    print(f"Successfully ingested {len(papers)} documents.")
    return True

if __name__ == "__main__":
    ingest_documents()
