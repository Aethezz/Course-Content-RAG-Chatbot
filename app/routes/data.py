from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, status
import shutil
from pathlib import Path
import os

from app.services.data_processor import process_and_store_document
from app.core.config import settings

router = APIRouter(prefix="/data", tags=["Data Management"])

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Uploads a document file (.pdf, .docx, .txt).
    The file is processed and indexed in the background.
    """
    if not file.filename:
         raise HTTPException(status_code=400, detail="No filename provided.")

    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
 
    temp_file_path = Path(settings.UPLOADS_DIR) / file.filename
    try:
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"File saved temporarily to: {temp_file_path}")

        # Add the processing task to run in the background
        background_tasks.add_task(process_and_store_document, str(temp_file_path))

        return {
            "filename": file.filename,
            "message": "File received and scheduled for processing.",
            "temp_path": str(temp_file_path) 
        }
    except Exception as e:
        if temp_file_path.exists():
            os.remove(temp_file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save or schedule file processing: {e}",
        )
    finally:
        await file.close()

@router.get("/collections")
async def get_collections_info():
    """ Gets basic info about the ChromaDB collection. """
    try:
        import chromadb
        client = chromadb.PersistentClient(path=settings.VECTOR_STORE_PATH)
        collection = client.get_collection(name=settings.CHROMA_COLLECTION_NAME)
        count = collection.count()
        return {
            "collection_name": settings.CHROMA_COLLECTION_NAME,
            "vector_store_path": settings.VECTOR_STORE_PATH,
            "document_count": count, # Approximate count of indexed chunks
        }
    except Exception as e:
         # Handle case where collection might not exist yet
        if "does not exist" in str(e).lower():
             return {
                "collection_name": settings.CHROMA_COLLECTION_NAME,
                "vector_store_path": settings.VECTOR_STORE_PATH,
                "document_count": 0,
                "status": "Collection not found or empty."
            }
        raise HTTPException(status_code=500, detail=f"Error accessing vector store: {e}")