from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os

# Import your routers
from app.routes import chat, data # <--- Import data router
from app.core.config import settings
# from app.core import vector_store # Optional: Trigger initialization if needed

# Create FastAPI app instance
app = FastAPI(title=settings.APP_TITLE)

# --- Mount Static Files ---
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(base_dir, "static")
if os.path.exists(static_dir):
    app.mount(
        "/static",
        StaticFiles(directory=static_dir),
        name="static"
    )
    print(f"Mounted static directory at: {static_dir}")
else:
    print(f"Warning: Static directory not found at {static_dir}.")

# --- Include Routers ---
app.include_router(chat.router, prefix="", tags=["Chat"])
app.include_router(data.router, prefix="", tags=["Data Management"]) # <--- Include data router

# --- Optional: Root Redirect ---
# @app.get("/", include_in_schema=False)
# async def root_redirect():
#     # Redirect root to the chat interface (assuming chat is at '/')
#     # Adjust if your chat interface is under a different path prefix
#     return RedirectResponse(url="/") # Or url=chat.router.url_path_for("get_chat_page") ?

# --- Optional: Add startup event if needed for complex initializations ---
# @app.on_event("startup")
# async def startup_event():
#     print("Application startup...")
#     # Initialize things like DB connections, ML models if not done at import time
#     # vector_store.initialize_store() # Example

# --- Run with Uvicorn (for development) ---
if __name__ == "__main__":
    import uvicorn
    # Run from command line: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    print("Starting Uvicorn directly is possible, but running 'uvicorn app.main:app --reload' is recommended.")
    uvicorn.run(app, host="0.0.0.0", port=8000)