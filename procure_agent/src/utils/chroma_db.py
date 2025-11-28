import chromadb
from chromadb.utils import embedding_functions
import os

# Initialize ChromaDB Client
# Using a local persistent directory
DB_DIR = os.path.join(os.getcwd(), "chroma_db")
client = chromadb.PersistentClient(path=DB_DIR)

# Use Google Generative AI Embeddings (if available) or default SentenceTransformer
# For simplicity in this demo, we'll use the default SentenceTransformer which Chroma downloads automatically.
# If you want to use Gemini embeddings, you'd need to configure that specific embedding function.
embedding_func = embedding_functions.DefaultEmbeddingFunction()

def get_collection():
    """Get or create the procurement_data collection."""
    return client.get_or_create_collection(
        name="procurement_data",
        embedding_function=embedding_func
    )

def add_documents(documents, metadatas, ids):
    """Add documents to the collection."""
    collection = get_collection()
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

def query_collection(query_text, n_results=3):
    """Query the collection for relevant documents."""
    collection = get_collection()
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results
