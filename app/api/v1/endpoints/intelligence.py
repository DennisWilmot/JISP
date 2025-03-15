# app/api/v1/endpoints/intelligence.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.db.session import get_db
from app.models.models import Intelligence
from app.schemas.intelligence import Intelligence as IntelligenceSchema
from app.schemas.intelligence import IntelligenceCreate, IntelligenceUpdate

router = APIRouter()

@router.post("/", response_model=IntelligenceSchema, status_code=status.HTTP_201_CREATED)
def create_intelligence(
    intelligence: IntelligenceCreate,
    db: Session = Depends(get_db)
):
    """Create new intelligence data"""
    db_intelligence = Intelligence(**intelligence.dict())
    db.add(db_intelligence)
    db.commit()
    db.refresh(db_intelligence)
    
    # TODO: Trigger update of predictions
    
    return db_intelligence

@router.get("/", response_model=List[IntelligenceSchema])
def read_intelligence(
    skip: int = 0,
    limit: int = 100,
    parish_id: Optional[int] = None,
    intelligence_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve intelligence data with optional filtering"""
    query = db.query(Intelligence)
    
    if parish_id:
        query = query.filter(Intelligence.parish_id == parish_id)
    
    if intelligence_type:
        query = query.filter(Intelligence.type == intelligence_type)
    
    return query.order_by(Intelligence.timestamp.desc()).offset(skip).limit(limit).all()

@router.get("/{intelligence_id}", response_model=IntelligenceSchema)
def read_intelligence_by_id(
    intelligence_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve specific intelligence by ID"""
    db_intelligence = db.query(Intelligence).filter(Intelligence.id == intelligence_id).first()
    if db_intelligence is None:
        raise HTTPException(status_code=404, detail="Intelligence not found")
    return db_intelligence

@router.patch("/{intelligence_id}", response_model=IntelligenceSchema)
def update_intelligence(
    intelligence_id: int,
    intelligence: IntelligenceUpdate,
    db: Session = Depends(get_db)
):
    """Update intelligence data"""
    db_intelligence = db.query(Intelligence).filter(Intelligence.id == intelligence_id).first()
    if db_intelligence is None:
        raise HTTPException(status_code=404, detail="Intelligence not found")
    
    # Update only the provided fields
    update_data = intelligence.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_intelligence, key, value)
    
    db.commit()
    db.refresh(db_intelligence)
    
    # TODO: Trigger update of predictions if necessary
    
    return db_intelligence

@router.delete("/{intelligence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_intelligence(
    intelligence_id: int,
    db: Session = Depends(get_db)
):
    """Delete intelligence data"""
    db_intelligence = db.query(Intelligence).filter(Intelligence.id == intelligence_id).first()
    if db_intelligence is None:
        raise HTTPException(status_code=404, detail="Intelligence not found")
    
    db.delete(db_intelligence)
    db.commit()
    
    # TODO: Trigger update of predictions
    
    return None
@router.get("/types", response_model=List[str])
def get_intelligence_types():
    """Get all available intelligence types"""
    return [intel_type.value for intel_type in IntelligenceType]

# app/api/v1/endpoints/intelligence.py
# Add this to your existing intelligence.py file

from app.services.validation import validate_intelligence, check_intelligence_trends

@router.post("/with-validation", response_model=Dict[str, Any])
def create_intelligence_with_validation(
    intelligence: IntelligenceCreate,
    db: Session = Depends(get_db)
):
    """Create new intelligence with validation"""
    # Convert Pydantic model to dict
    data = intelligence.dict()
    
    # Validate the intelligence data
    is_valid, message = validate_intelligence(data, db)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    # Create the intelligence record
    db_intelligence = Intelligence(**data)
    db.add(db_intelligence)
    db.commit()
    db.refresh(db_intelligence)
    
    # Get trends for the associated parish
    trends = check_intelligence_trends(db_intelligence.parish_id, db)
    
    # Return both the new intelligence and the updated trends
    return {
        "intelligence": IntelligenceSchema.from_orm(db_intelligence),
        "trends": trends,
        "message": message  # This will contain any warnings
    }

# app/api/v1/endpoints/intelligence.py
# Add this to your existing intelligence.py file

@router.get("/insights/{parish_id}", response_model=Dict[str, Any])
def get_intelligence_insights(
    parish_id: int,
    db: Session = Depends(get_db)
):
    """Get intelligence insights for a specific parish"""
    # Check if parish exists
    parish = db.query(Parish).filter(Parish.id == parish_id).first()
    if parish is None:
        raise HTTPException(status_code=404, detail="Parish not found")
    
    # Get trends
    trends = check_intelligence_trends(parish_id, db)
    
    # Get recent intelligence (last 30 days)
    month_ago = datetime.now() - timedelta(days=30)
    recent_intelligence = db.query(Intelligence).filter(
        Intelligence.parish_id == parish_id,
        Intelligence.timestamp > month_ago
    ).order_by(Intelligence.timestamp.desc()).limit(10).all()
    
    # Get parish details
    parish_details = {
        "id": parish.id,
        "name": parish.name,
        "current_crime_level": parish.current_crime_level,
        "police_allocated": parish.police_allocated,
    }
    
    return {
        "parish": parish_details,
        "trends": trends,
        "recent_intelligence": [IntelligenceSchema.from_orm(intel) for intel in recent_intelligence]
    }