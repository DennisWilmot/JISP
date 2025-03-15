from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
import json
import uvicorn
from sqlalchemy.orm import Session

from app.core.config import settings
# Import all endpoint routers together
from app.api.v1.endpoints import intelligence, parishes, insights
from app.socket.manager import manager
from app.socket.events import handle_subscribe, handle_intelligence_create
from app.db.session import get_db
from app.db.init_db import init_db
from app.ml.active_learning import ActiveLearningSystem


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
app.include_router(
    insights.router,
    prefix=f"{settings.API_V1_STR}/insights",
    tags=["insights"]
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
            
            # Create a database session for this connection
            db = next(get_db())
            
            try:
                message = json.loads(data)
                action = message.get("action", "")
                
                if action == "subscribe":
                    parish_id = message.get("parish_id")
                    if parish_id:
                        await handle_subscribe(websocket, parish_id)
                
                elif action == "create_intelligence":
                    intelligence_data = message.get("data")
                    if intelligence_data:
                        await handle_intelligence_create(intelligence_data, db)
                
                # Add more action handlers as needed
                
                # Echo the message back for now
                await websocket.send_text(json.dumps({"status": "success", "message": "Action processed"}))
            
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"status": "error", "message": "Invalid JSON"}))
            except Exception as e:
                await websocket.send_text(json.dumps({"status": "error", "message": str(e)}))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

active_learning = ActiveLearningSystem()

@app.on_event("startup")
async def startup_event():
    # Create a database session
    db = next(get_db())
    
    # Initialize the database
    init_db(db)
    
    # Start active learning monitoring
    active_learning.start_monitoring(get_db)