# app/schemas/parish.py
from typing import Dict, Optional, List
from pydantic import BaseModel, Field

class ParishBase(BaseModel):
    name: str
    coordinates: Dict[str, float]  # {"lat": float, "lng": float}

class ParishCreate(ParishBase):
    pass

class ParishUpdate(BaseModel):
    name: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    current_crime_level: Optional[int] = Field(None, ge=0, le=100)
    police_allocated: Optional[int] = Field(None, ge=0)

class ParishInDB(ParishBase):
    id: int
    current_crime_level: int = 0
    police_allocated: int = 0
    recommended_allocation: int = 0  # Add this line
    
    class Config:
        from_attributes = True

class Parish(ParishInDB):
    pass

class ParishWithStats(Parish):
    intelligence_count: int = 0
    average_severity: float = 0.0
    crime_trend: str = "stable"  # "increasing", "decreasing", or "stable"

