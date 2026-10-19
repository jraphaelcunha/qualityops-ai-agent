import os

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
VECTORSTORE_DIR = os.path.join(DATA_DIR, "vectorstore")

def query_knowledge_base(query: str, k: int = 3):
    """
    Queries the ChromaDB vector store for the most relevant documents.
    """
    if not os.path.exists(VECTORSTORE_DIR):
        return ["Error: Vector store not found. Please run ingest.py first."]

    # Initialize embeddings (must match ingestion)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Load vector store
    vectorstore = Chroma(
        persist_directory=VECTORSTORE_DIR,
        embedding_function=embeddings
    )

    # Perform similarity search
    results = vectorstore.similarity_search(query, k=k)

    return [doc.page_content for doc in results]

if __name__ == "__main__":
    test_query = "What is the rule about PIN verification?"
    print(f"Querying: '{test_query}'...\n")

    try:
        results = query_knowledge_base(test_query)
        for i, result in enumerate(results, 1):
            print(f"--- Result {i} ---")
            print(result)
            print("\n")
    except (RuntimeError, ValueError, OSError) as e:
        print(f"An error occurred: {e}")
