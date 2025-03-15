# app/socket/events.py
from typing import Dict, Any, List
from fastapi import WebSocket, Depends, WebSocketDisconnect
from sqlalchemy.orm import Session
import json

from app.db.session import get_db
from app.socket.manager import manager
from app.models.models import Intelligence, Parish, Prediction
from app.ml.models.crime_prediction import CrimePredictionModel
from app.ml.models.resource_allocator import ResourceAllocator

async def handle_subscribe(websocket: WebSocket, parish_id: int):
    """Handle subscription to parish updates"""
    await manager.subscribe_to_parish(websocket, parish_id)

async def handle_intelligence_create(data: Dict[str, Any], db: Session):
    """Handle new intelligence creation and broadcast updates"""
    # Create new intelligence record
    new_intelligence = Intelligence(**data)
    db.add(new_intelligence)
    db.commit()
    db.refresh(new_intelligence)
    
    # Run prediction model for affected parish
    prediction_model = CrimePredictionModel()
    parish_id = new_intelligence.parish_id
    
    # Get the parish
    parish = db.query(Parish).filter(Parish.id == parish_id).first()
    if parish:
        # Update crime level prediction
        crime_level = prediction_model.predict_crime_level(db, parish_id)
        parish.current_crime_level = crime_level
        db.commit()
        
        # Create a prediction record
        allocator = ResourceAllocator()
        allocation = allocator.allocate_resources(db)
        
        # Create a new prediction record
        prediction = Prediction(
            parish_id=parish_id,
            predicted_crime_level=crime_level,
            recommended_officers=allocation.get(parish_id, 0)
        )
        db.add(prediction)
        db.commit()
        
        # Broadcast updates
        await manager.send_intelligence_update({
            "id": new_intelligence.id,
            "type": new_intelligence.type,
            "parish_id": new_intelligence.parish_id,
            "severity": new_intelligence.severity,
            "confidence": new_intelligence.confidence,
            "timestamp": new_intelligence.timestamp.isoformat()
        })
        
        # Broadcast resource allocation update
        await manager.send_resource_update(allocation)
        
    return new_intelligence