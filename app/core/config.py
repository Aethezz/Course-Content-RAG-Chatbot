import os
from functools import lru_cache
from pydantic_settings import BaseSettings # Updated import
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_TITLE: str = os.getenv("APP_TITLE", "FastAPI Chatbot")
    GOOGLE_API_KEY: str
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    LLM_MODEL_NAME: str = "gemini-1.5-flash-latest"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    VECTOR_STORE_PATH: str = "./data_store/chroma"
    UPLOADS_DIR: str = "./uploads"
    CHROMA_COLLECTION_NAME: str = "course_material"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    RETRIEVED_DOCS_COUNT: int = 4

    class Config:
        env_file = ".env"
        extra = 'ignore' # Ignore extra fields if any

@lru_cache()
def get_settings():
    # Ensure necessary directories exist
    settings_obj = Settings()
    os.makedirs(settings_obj.VECTOR_STORE_PATH, exist_ok=True)
    os.makedirs(settings_obj.UPLOADS_DIR, exist_ok=True)
    return settings_obj

settings = get_settings()

# Basic validation
if not settings.GOOGLE_API_KEY or "YOUR_NEW_GEMINI_API_KEY" in settings.GOOGLE_API_KEY:
     print("\n!!! WARNING: GOOGLE_API_KEY is not set correctly in .env file. Chatbot generation will fail. !!!\n")