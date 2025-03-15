# app/socket/manager.py
from fastapi import WebSocket
from typing import List, Dict, Any
import json

class ConnectionManager:
    def __init__(self):
        # Keep track of active connections
        self.active_connections: List[WebSocket] = []
        # Map of parish IDs to connections that are interested in updates for that parish
        self.parish_subscribers: Dict[int, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a disconnected WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Also remove from parish subscriptions
        for parish_id, connections in self.parish_subscribers.items():
            if websocket in connections:
                connections.remove(websocket)
    
    async def subscribe_to_parish(self, websocket: WebSocket, parish_id: int):
        """Subscribe a connection to updates for a specific parish"""
        if parish_id not in self.parish_subscribers:
            self.parish_subscribers[parish_id] = []
        
        if websocket not in self.parish_subscribers[parish_id]:
            self.parish_subscribers[parish_id].append(websocket)
        
        await websocket.send_text(json.dumps({
            "event": "subscribed",
            "parish_id": parish_id
        }))
    
    async def broadcast(self, message: Dict[str, Any]):
        """Send a message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                # Connection might be closed or invalid
                pass
    
    async def broadcast_to_parish(self, parish_id: int, message: Dict[str, Any]):
        """Send a message to all clients subscribed to a specific parish"""
        if parish_id not in self.parish_subscribers:
            return
        
        for connection in self.parish_subscribers[parish_id]:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                # Connection might be closed or invalid
                pass
    
    async def send_intelligence_update(self, intelligence_data: Dict[str, Any]):
        """Send intelligence update to relevant subscribers"""
        # Send to everyone subscribed to this parish
        parish_id = intelligence_data.get("parish_id")
        if parish_id:
            await self.broadcast_to_parish(parish_id, {
                "event": "intelligence_update",
                "data": intelligence_data
            })
        
        # Also broadcast to everyone that a new intelligence has been added
        await self.broadcast({
            "event": "new_intelligence",
            "parish_id": parish_id
        })
    
    async def send_resource_update(self, allocation_data: Dict[int, int]):
        """Send resource allocation update to all clients"""
        await self.broadcast({
            "event": "resource_allocation",
            "data": allocation_data
        })
        
        # Also send parish-specific updates
        for parish_id, officers in allocation_data.items():
            await self.broadcast_to_parish(parish_id, {
                "event": "officers_allocated",
                "parish_id": parish_id,
                "officers": officers
            })

# Create a global connection manager instance
manager = ConnectionManager()