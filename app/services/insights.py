# app/services/insights.py
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.models.models import Intelligence, Parish, Prediction
from app.ml.models.resource_allocator import ResourceAllocator
from app.ml.models.crime_prediction import CrimePredictionModel

class InsightsGenerator:
    def __init__(self, db: Session):
        self.db = db
        self.resource_allocator = ResourceAllocator()
        self.prediction_model = CrimePredictionModel()
    
    def generate_resource_insights(self) -> List[Dict[str, Any]]:
        """
        Generate insights about resource allocation based on recent intelligence
        Returns a list of resource adjustment recommendations
        """
        # Get current allocations
        parishes = self.db.query(Parish).all()
        current_allocations = {parish.id: parish.police_allocated for parish in parishes}
        parish_names = {parish.id: parish.name for parish in parishes}
        
        # Update crime level predictions
        for parish in parishes:
            crime_level = self.prediction_model.predict_crime_level(self.db, parish.id)
            parish.current_crime_level = crime_level
        
        self.db.commit()
        
        # Get new recommended allocations
        new_allocations = self.resource_allocator.allocate_resources(self.db)
        
        # Generate insights based on differences
        insights = []
        for parish_id, new_count in new_allocations.items():
            current_count = current_allocations.get(parish_id, 0)
            difference = new_count - current_count
            
            if abs(difference) >= 5:  # Only suggest significant changes
                # Determine confidence based on recent intelligence volume
                recent_intelligence = self._get_recent_intelligence_count(parish_id)
                
                if recent_intelligence > 20:
                    confidence = "high"
                elif recent_intelligence > 10:
                    confidence = "medium"
                else:
                    confidence = "low"
                
                # Create recommendation
                parish_name = parish_names.get(parish_id, f"Parish {parish_id}")
                
                if difference > 0:
                    action = "Increase"
                    reason = self._get_increase_reason(parish_id)
                else:
                    action = "Reduce"
                    reason = self._get_decrease_reason(parish_id)
                
                insights.append({
                    "parish_id": parish_id,
                    "parish_name": parish_name,
                    "action": action,
                    "officers": abs(difference),
                    "confidence": confidence,
                    "reason": reason
                })
        
        # Sort by confidence and then by number of officers
        insights.sort(key=lambda x: (
            {"high": 0, "medium": 1, "low": 2}[x["confidence"]], 
            -x["officers"]
        ))
        
        return insights
    
    def _get_recent_intelligence_count(self, parish_id: int) -> int:
        """Get count of intelligence from the last 14 days for a parish"""
        two_weeks_ago = datetime.now() - timedelta(days=14)
        return self.db.query(func.count(Intelligence.id)).filter(
            Intelligence.parish_id == parish_id,
            Intelligence.timestamp > two_weeks_ago
        ).scalar()
    
    def _get_increase_reason(self, parish_id: int) -> str:
        """Generate a reason for increasing officers"""
        # Get most common intelligence types for this parish recently
        week_ago = datetime.now() - timedelta(days=7)
        common_type = self.db.query(
            Intelligence.type, 
            func.count(Intelligence.id).label('count')
        ).filter(
            Intelligence.parish_id == parish_id,
            Intelligence.timestamp > week_ago
        ).group_by(Intelligence.type).order_by(desc('count')).first()
        
        if common_type:
            intel_type = common_type[0]
            high_severity = self.db.query(func.avg(Intelligence.severity)).filter(
                Intelligence.parish_id == parish_id,
                Intelligence.timestamp > week_ago
            ).scalar() or 0
            
            if high_severity > 7:
                severity_text = "high-severity"
            elif high_severity > 4:
                severity_text = "moderate"
            else:
                severity_text = "recent"
            
            return f"Increase due to {severity_text} {intel_type.lower()} reports in this area"
        
        return "Increase based on predicted crime level trends"
    
    def _get_decrease_reason(self, parish_id: int) -> str:
        """Generate a reason for decreasing officers"""
        month_ago = datetime.now() - timedelta(days=30)
        
        # Check if intelligence volume has decreased
        old_count = self.db.query(func.count(Intelligence.id)).filter(
            Intelligence.parish_id == parish_id,
            Intelligence.timestamp.between(month_ago, month_ago + timedelta(days=15))
        ).scalar()
        
        new_count = self.db.query(func.count(Intelligence.id)).filter(
            Intelligence.parish_id == parish_id,
            Intelligence.timestamp > (month_ago + timedelta(days=15))
        ).scalar()
        
        if old_count > new_count * 1.5:
            return "Decrease due to significant reduction in reported incidents"
        
        return "Resources needed more urgently in other areas based on relative crime levels"