# app/schemas/intelligence.py
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

class IntelligenceType(str, Enum):
    CRIME = "Crime"
    EVENT = "Event"
    PERSON = "Person"
    GANG_ACTIVITY = "Gang Activity" 
    POLICE = "Police"
    SUSPICIOUS_ACTIVITY = "Suspicious Activity"

class IntelligenceBase(BaseModel):
    type: IntelligenceType = Field(..., description="Type of intelligence")
    parish_id: int = Field(..., description="ID of the parish this intelligence is related to")
    description: str = Field(..., description="Detailed description of the intelligence")
    severity: int = Field(..., ge=1, le=10, description="Severity level (1-10)")
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="Confidence in this intelligence (0.0-1.0)")
    is_verified: bool = Field(False, description="Whether this intelligence has been verified")


class IntelligenceCreate(IntelligenceBase):
    pass

class IntelligenceUpdate(BaseModel):
    type: Optional[IntelligenceType] = None
    parish_id: Optional[int] = None
    description: Optional[str] = None
    severity: Optional[int] = Field(None, ge=1, le=10)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_verified: Optional[bool] = None
    feedback_score: Optional[int] = Field(None, ge=-2, le=2)

class IntelligenceInDB(IntelligenceBase):
    id: int
    feedback_score: int = 0
    timestamp: datetime
    
    class Config:
        orm_mode = True

class Intelligence(IntelligenceInDB):
    pass