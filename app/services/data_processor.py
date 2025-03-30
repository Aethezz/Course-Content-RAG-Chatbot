import os
import shutil
from pathlib import Path
from typing import List

from langchain_community.document_loaders import (
    UnstructuredFileLoader,
    DirectoryLoader,
    TextLoader,
    PyPDFLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

from app.core.config import settings
from app.core.vector_store import get_vector_store, get_embedding_function # Assuming these still work

# --- Keep load_and_split_document as it was ---
def load_and_split_document(file_path: str) -> List[Document]:
    """Loads a document and splits it into chunks."""
    print(f"Loading document: {file_path}")
    file_extension = Path(file_path).suffix.lower()

    try:
        if file_extension == ".pdf":
            loader = PyPDFLoader(file_path)
        elif file_extension == ".txt":
            loader = TextLoader(file_path, encoding='utf-8')
        else:
             loader = UnstructuredFileLoader(file_path, mode="single", strategy="fast")

        documents = loader.load()

        if not documents:
             print(f"Warning: No content loaded from {file_path}")
             return []

    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        try:
             print("Attempting fallback with basic UnstructuredFileLoader...")
             loader = UnstructuredFileLoader(file_path)
             documents = loader.load()
             if not documents:
                 print(f"Fallback loader also failed for {file_path}")
                 return []
        except Exception as fallback_e:
             print(f"Fallback loader failed for {file_path}: {fallback_e}")
             return []

    print(f"Splitting document sections...") # Removed count here as it might not be accurate pre-split
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Document split into {len(chunks)} chunks.")
    return chunks


# --- Modify process_and_store_document ---
def process_and_store_document(file_path: str):
    """Processes a single document and stores it in the vector store in batches."""
    # Define a reasonable batch size (less than the reported max of 166)
    # Let's choose 100, but you can tune this.
    BATCH_SIZE = 100
    source_filename = Path(file_path).name

    try:
        # 1. Load and Split
        chunks = load_and_split_document(file_path)
        if not chunks:
            print(f"Skipping storing for {file_path} due to loading/splitting issues.")
            return False

        total_chunks = len(chunks)
        print(f"Preparing to add {total_chunks} chunks for {source_filename} in batches of {BATCH_SIZE}...")

        # Add source metadata to each chunk
        for chunk in chunks:
            chunk.metadata["source"] = source_filename

        # 2. Get Vector Store
        vector_db = get_vector_store()

        # 3. Add to Vector Store IN BATCHES
        for i in range(0, total_chunks, BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            print(f"  Adding batch {i//BATCH_SIZE + 1}/{(total_chunks + BATCH_SIZE - 1)//BATCH_SIZE} ({len(batch)} chunks)...")
            try:
                vector_db.add_documents(batch)
            except Exception as batch_e:
                print(f"  !!! Error adding batch starting at index {i}: {batch_e}")
                # Optionally decide whether to continue with next batch or fail entirely
                # For now, we'll just log the error and continue
                # If you want to stop on first batch error, uncomment the next line:
                # raise batch_e # Re-raise the exception to stop processing

        print(f"Successfully processed and stored {total_chunks} chunks for: {source_filename}")
        return True

    except Exception as e:
        print(f"Error during overall processing of document {file_path}: {e}")
        # If a batch error was re-raised, it will be caught here too
        return False
    finally:
        # Clean up the temporary uploaded file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed temporary file: {file_path}")
        except Exception as cleanup_e:
            print(f"Error cleaning up file {file_path}: {cleanup_e}")