# --- app/core/vector_store.py (Using Recommended PersistentClient) ---
import os
import chromadb
# from chromadb.config import Settings as ChromaSettings # <-- No longer needed for this init

# --- Use the chosen embedding class ---
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from app.core.config import settings

# --- Initialize Embedding Model ---
try:
    print(f"Initializing HuggingFaceEmbeddings with model: {settings.EMBEDDING_MODEL_NAME}")
    embedding_function = HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL_NAME,
        cache_folder="./embedding_cache"
    )
    print("HuggingFaceEmbeddings initialized.")
except Exception as e:
     print(f"!!! Error initializing HuggingFaceEmbeddings: {e}")
     raise RuntimeError(f"Failed to initialize embeddings: {e}") from e

# --- Initialize ChromaDB Client using the NEW Recommended PersistentClient ---
os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True) # Ensure path exists

try:
    print(f"Attempting to initialize ChromaDB PersistentClient at: {settings.VECTOR_STORE_PATH}")

    # NEW WAY: Use PersistentClient and just provide the path
    chroma_client = chromadb.PersistentClient(
        path=settings.VECTOR_STORE_PATH
        # Optional: Pass settings ONLY if needed, e.g., for telemetry
        # settings=chromadb.Settings(anonymized_telemetry=False)
    )
    print("ChromaDB PersistentClient initialized successfully.")

    # Get or create the collection using the client
    chroma_collection = chroma_client.get_or_create_collection(
         name=settings.CHROMA_COLLECTION_NAME
    )
    print(f"ChromaDB collection '{settings.CHROMA_COLLECTION_NAME}' loaded/created.")
    print(f"Collection document count: {chroma_collection.count()}")

except Exception as e:
    # This specific error shouldn't happen now, but keep general error handling
    print(f"!!! Error initializing ChromaDB PersistentClient or collection: {e}")
    print("!!! Please check ChromaDB documentation and ensure the path is accessible and valid.")
    raise RuntimeError(f"Failed to initialize ChromaDB: {e}") from e


# --- LangChain Vector Store Wrapper (remains the same) ---
try:
    vector_store = Chroma(
        client=chroma_client, # Pass the configured PersistentClient
        collection_name=settings.CHROMA_COLLECTION_NAME,
        embedding_function=embedding_function,
    )
    print("LangChain Chroma vector store wrapper initialized.")
except Exception as e:
    print(f"!!! Error initializing LangChain Chroma wrapper: {e}")
    raise RuntimeError(f"Failed to initialize LangChain Chroma wrapper: {e}") from e

# --- Dependency Functions ---
def get_vector_store() -> Chroma:
    if 'vector_store' not in globals() or vector_store is None:
        raise RuntimeError("Vector store not initialized or initialization failed.")
    return vector_store

def get_embedding_function():
    if 'embedding_function' not in globals() or embedding_function is None:
        raise RuntimeError("Embedding function not initialized or initialization failed.")
    return embedding_function

# --- Log final embedding model used ---
print(f"Vector Store configured with embedding model: {settings.EMBEDDING_MODEL_NAME}")
