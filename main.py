# app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
import json
import uvicorn

from app.core.config import settings
from app.api.v1.endpoints import intelligence, parishes
from app.socket.manager import manager
from app.db.session import get_db, engine
from app.db.init_db import init_db
from sqlalchemy.orm import Session

app = FastAPI(
    title="Jamaica Police Intelligence System API",
    description="Backend API for real-time intelligence gathering and resource allocation",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    intelligence.router,
    prefix=f"{settings.API_V1_STR}/intelligence",
    tags=["intelligence"]
)
app.include_router(
    parishes.router,
    prefix=f"{settings.API_V1_STR}/parishes",
    tags=["parishes"]
)

@app.get("/")
async def root():
    return {"message": "Jamaica Police Intelligence System API"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            
            # Parse the received data
            try:
                message = json.loads(data)
                
                # Handle different message types
                if message.get("action") == "subscribe":
                    parish_id = message.get("parish_id")
                    if parish_id:
                        await manager.subscribe_to_parish(websocket, parish_id)
                
                # Echo the message back for now
                await websocket.send_text(f"Message received: {data}")
            except json.JSONDecodeError:
                await websocket.send_text(f"Error: Invalid JSON")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    # Create a database session
    db = next(get_db())
    
    # Initialize the database
    init_db(db)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)