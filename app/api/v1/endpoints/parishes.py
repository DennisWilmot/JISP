# app/api/v1/endpoints/parishes.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.db.session import get_db
from app.models.models import Parish, Intelligence
from app.schemas.parish import Parish as ParishSchema
from app.schemas.parish import ParishUpdate, ParishWithStats
from app.ml.models.resource_allocator import ResourceAllocator
from app.ml.models.crime_prediction import CrimePredictionModel

router = APIRouter()

@router.get("/", response_model=List[ParishSchema])
def read_parishes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Retrieve all parishes"""
    return db.query(Parish).offset(skip).limit(limit).all()

@router.get("/with-stats", response_model=List[ParishWithStats])
def read_parishes_with_stats(
    db: Session = Depends(get_db)
):
    """Retrieve parishes with additional statistics"""
    parishes = db.query(Parish).all()
    result = []
    
    for parish in parishes:
        # Get intelligence count
        intelligence_count = db.query(func.count(Intelligence.id)).filter(
            Intelligence.parish_id == parish.id
        ).scalar()
        
        # Get average severity
        avg_severity = db.query(func.avg(Intelligence.severity)).filter(
            Intelligence.parish_id == parish.id
        ).scalar() or 0.0
        
        # Get crime trend (simplified for now)
        crime_trend = "stable"  # This would be calculated based on historical data
        
        parish_data = ParishSchema.from_orm(parish)
        parish_with_stats = ParishWithStats(
            **parish_data.dict(),
            intelligence_count=intelligence_count,
            average_severity=float(avg_severity),
            crime_trend=crime_trend
        )
        result.append(parish_with_stats)
    
    return result

@router.get("/{parish_id}", response_model=ParishSchema)
def read_parish(
    parish_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve a specific parish by ID"""
    db_parish = db.query(Parish).filter(Parish.id == parish_id).first()
    if db_parish is None:
        raise HTTPException(status_code=404, detail="Parish not found")
    return db_parish

@router.patch("/{parish_id}", response_model=ParishSchema)
def update_parish(
    parish_id: int,
    parish: ParishUpdate,
    db: Session = Depends(get_db)
):
    """Update parish data"""
    db_parish = db.query(Parish).filter(Parish.id == parish_id).first()
    if db_parish is None:
        raise HTTPException(status_code=404, detail="Parish not found")
    
    update_data = parish.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_parish, key, value)
    
    db.commit()
    db.refresh(db_parish)
    return db_parish

@router.post("/allocate-resources", response_model=dict)
def allocate_resources(
    db: Session = Depends(get_db)
):
    """Allocate police resources across parishes based on crime levels"""
    # First, update crime level predictions for all parishes
    prediction_model = CrimePredictionModel()
    parishes = db.query(Parish).all()
    
    for parish in parishes:
        # Predict crime level
        crime_level = prediction_model.predict_crime_level(db, parish.id)
        parish.current_crime_level = crime_level
    
    db.commit()
    
    # Now allocate resources
    allocator = ResourceAllocator()
    allocation = allocator.allocate_resources(db)
    
    # Update parish allocations in the database
    for parish_id, officers in allocation.items():
        parish = db.query(Parish).filter(Parish.id == parish_id).first()
        if parish:
            parish.police_allocated = officers
    
    db.commit()
    
    return allocation

# Add to app/api/v1/endpoints/parishes.py
from app.services.allocation_service import execute_allocation_plan

@router.post("/execute-allocation", response_model=Dict[int, int])
async def execute_allocation(
    allocation_plan: Dict[int, int],
    db: Session = Depends(get_db)
):
    """Execute an allocation plan provided by admin"""
    try:
        result = await execute_allocation_plan(db, allocation_plan)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))