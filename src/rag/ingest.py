import os

from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
SOURCE_FILE = os.path.join(DATA_DIR, "grit_support_guidelines.md")
VECTORSTORE_DIR = os.path.join(DATA_DIR, "vectorstore")

def ingest_data():
    if not os.path.exists(SOURCE_FILE):
        print(f"Error: Source file not found at {SOURCE_FILE}")
        return

    print("Loading document...")
    loader = TextLoader(SOURCE_FILE, encoding='utf-8')
    documents = loader.load()

    print("Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")

    print("Initializing embeddings (this might take a moment)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print(f"Creating/Updating vector store at {VECTORSTORE_DIR}...")
    # This automatically persists to disk in the specified directory
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTORSTORE_DIR
    )

    print(f"Ingestion Complete. Database persisted at {VECTORSTORE_DIR}")
    return vectorstore

if __name__ == "__main__":
    ingest_data()
