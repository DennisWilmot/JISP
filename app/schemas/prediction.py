# app/schemas/prediction.py
from datetime import datetime
from pydantic import BaseModel

class PredictionBase(BaseModel):
    parish_id: int
    predicted_crime_level: int
    recommended_officers: int

class PredictionCreate(PredictionBase):
    pass

class PredictionInDB(PredictionBase):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True  # Updated from orm_mode=True

class Prediction(PredictionInDB):
    pass