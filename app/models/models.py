# app/models/models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, CheckConstraint, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base

class Parish(Base):
    __tablename__ = "parishes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    coordinates = Column(JSON)  # JSONB in PostgreSQL
    current_crime_level = Column(Integer)
    police_allocated = Column(Integer)
    
    # Relationships
    intelligence_items = relationship("Intelligence", back_populates="parish")
    predictions = relationship("Prediction", back_populates="parish")

class Intelligence(Base):
    __tablename__ = "intelligence"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)
    parish_id = Column(Integer, ForeignKey("parishes.id"))
    description = Column(Text)
    severity = Column(Integer)
    confidence = Column(Float, default=0.5)
    is_verified = Column(Boolean, default=False)
    feedback_score = Column(Integer, default=0)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Add check constraint for severity
    __table_args__ = (
        CheckConstraint('severity >= 1 AND severity <= 10', name='check_severity_range'),
    )
    
    # Relationships
    parish = relationship("Parish", back_populates="intelligence_items")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    parish_id = Column(Integer, ForeignKey("parishes.id"))
    predicted_crime_level = Column(Integer)
    recommended_officers = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    parish = relationship("Parish", back_populates="predictions")

class ModelVersion(Base):
    __tablename__ = "model_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    model_type = Column(String(50), nullable=False)
    accuracy = Column(Float)
    features = Column(JSON)  # JSONB in PostgreSQL
    binary_data = Column(LargeBinary)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# app/models/models.py
# Add this new class

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())