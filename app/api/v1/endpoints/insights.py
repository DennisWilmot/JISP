# app/api/v1/endpoints/insights.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter()

@router.get("/test")
def test_endpoint():
    """Simple test endpoint to verify routing"""
    return {"message": "Insights test endpoint is working"}

@router.get("/resource-recommendations")
def get_resource_insights(db: Session = Depends(get_db)):
    """Simplified version for testing"""
    return [
        {
            "parish_id": 1,
            "parish_name": "Kingston",
            "action": "Increase",
            "officers": 10,
            "confidence": "high",
            "reason": "Increase due to recent crime reports in this area"
        }
    ]