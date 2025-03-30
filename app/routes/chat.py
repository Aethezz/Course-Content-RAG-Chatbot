from fastapi import (
    APIRouter,
    Request,
    WebSocket,
    WebSocketDisconnect,
    Depends,
)
from fastapi.templating import Jinja2Templates
from app.services.chatbot_service import get_bot_response
from typing import List
# In app/routes/chat.py
from app.core.config import settings # Make sure settings is imported


# ... (websocket endpoint) ...

# Configure templates
# It's often better to initialize templates in main.py and pass via Depends
# but for simplicity here, we initialize directly. Make sure the path is correct.
templates = Jinja2Templates(directory="templates")

router = APIRouter()

class ConnectionManager:
    """Manages active WebSocket connections."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"New connection: {websocket.client}. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
         if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"Connection closed: {websocket.client}. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        # ... (implementation as before) ...
        try:
            await websocket.send_text(message)
        except RuntimeError as e:
            print(f"Failed to send message, websocket likely closed: {e}")
            await self.safe_disconnect(websocket) # Call safe_disconnect here
        except Exception as e:
            print(f"Unexpected error sending message: {e}")
            await self.safe_disconnect(websocket)

    # --- ENSURE THIS METHOD IS PRESENT ---
    async def safe_disconnect(self, websocket: WebSocket):
        """Disconnects safely, ignoring errors if already closed."""
        self.disconnect(websocket) # Remove from list first
        try:
             await websocket.close(code=1000)
        except RuntimeError as e:
             if "WebSocket is not open" not in str(e):
                  print(f"Error closing websocket {websocket.client}: {e}")
        except Exception as e:
             print(f"Unexpected error closing websocket {websocket.client}: {e}")
    # ----------------------------------

# --- Create ONE instance of the manager ---
manager = ConnectionManager()

# In app/routes/chat.py
# ... (imports and manager code) ...

@router.get("/", tags=["Chat Interface"])
async def get_chat_page(request: Request):
    """Serves the main chat HTML page."""
    # Pass settings to the template context
    return templates.TemplateResponse("chat.html", {"request": request, "settings": settings})

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    client_addr = f"{websocket.client.host}:{websocket.client.port}"
    print(f"--- WebSocket Connected: {client_addr} ---") # Log connection
    try:
        while True:
            print(f"[{client_addr}] Waiting to receive text...") # Log before receive
            data = await websocket.receive_text() # User message
            print(f"[{client_addr}] Received text: {data}") # Log AFTER receive

            print(f"[{client_addr}] >>> Calling get_bot_response...") # Log BEFORE service call
            # Call the RAG service
            bot_response_text = await get_bot_response(data)
            print(f"[{client_addr}] <<< Got bot response (first 50 chars): {bot_response_text[:50]}...") # Log AFTER service call

            print(f"[{client_addr}] Sending response back to client...") # Log before send
            # Send bot's response back to the client
            await manager.send_personal_message(f"Bot: {bot_response_text}", websocket)
            print(f"[{client_addr}] Response sent.") # Log after send

    except WebSocketDisconnect:
        # Log the disconnect reason if available
        # print(f"[{client_addr}] WebSocket disconnected. Reason: {websocket.client_state}, Code: {websocket.application_state}") # Might need different attrs
        print(f"[{client_addr}] WebSocket disconnected.")
        manager.disconnect(websocket) # Call disconnect from manager

    except Exception as e:
        # Print DETAILED traceback for ANY exception in the loop
        print(f"!!! WebSocket Error ({client_addr}) !!!")
        import traceback
        traceback.print_exc() # Print the full traceback
        await manager.safe_disconnect(websocket) # Ensure disconnect on error