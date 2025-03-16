# Updated app/ml/models/resource_allocator.py
import numpy as np
from typing import Dict, List
from sqlalchemy.orm import Session

from app.models.models import Parish, SystemSettings, Prediction
from app.core.config import settings
from datetime import datetime

class ResourceAllocator:
    def __init__(self):
        self.total_officers = settings.TOTAL_OFFICERS
        self.min_officers_per_parish = settings.MIN_OFFICERS_PER_PARISH
    
    def allocate_resources(self, db: Session) -> Dict[int, int]:
        """
        Allocate police officers across parishes based on crime levels
        Returns a dictionary mapping parish_id to officer count
        """
        # Get total officers from database
        total_officers_setting = db.query(SystemSettings).filter(SystemSettings.key == "total_officers").first()
        if total_officers_setting:
            self.total_officers = int(total_officers_setting.value)
        else:
            # Fall back to config setting if database value not found
            self.total_officers = settings.TOTAL_OFFICERS
            
        # Get all parishes with their crime levels
        parishes = db.query(Parish).all()
        
        # Extract crime levels and parish IDs
        parish_ids = [parish.id for parish in parishes]
        crime_levels = [parish.current_crime_level or 0 for parish in parishes]
        
        # Calculate recommended officer allocation (purely based on crime level ratio)
        recommendations = self._calculate_recommended_allocation(parish_ids, crime_levels)
        
        # Calculate actual allocation (with other factors considered)
        allocations = self._calculate_actual_allocation(parish_ids, crime_levels)
        
        # Update parishes with the allocations and recommendations
        for parish_id in parish_ids:
            parish = db.query(Parish).filter(Parish.id == parish_id).first()
            if parish:
                # Use DIFFERENT algorithms for these two values
                parish.police_allocated = allocations[parish_id]
                parish.recommended_allocation = recommendations[parish_id]
        
        # Create/update prediction records 
        for parish_id in parish_ids:
            parish = db.query(Parish).filter(Parish.id == parish_id).first()
            if parish:
                # Create new prediction record
                prediction = Prediction(
                    parish_id=parish_id,
                    predicted_crime_level=parish.current_crime_level or 0,
                    recommended_officers=recommendations[parish_id],
                    timestamp=datetime.now()
                )
                db.add(prediction)
        
        # Commit all changes
        db.commit()
        
        return allocations
    
    def _calculate_recommended_allocation(self, parish_ids: List[int], crime_levels: List[int]) -> Dict[int, int]:
        """
        Calculate recommended allocation based purely on crime level proportion.
        This is an ideal mathematical distribution.
        """
        recommendations = {}
        
        # Give minimum officers to each parish first
        remaining_officers = self.total_officers - (self.min_officers_per_parish * len(parish_ids))
        for parish_id in parish_ids:
            recommendations[parish_id] = self.min_officers_per_parish
        
        # Distribute remaining officers by crime level proportion
        total_crime = sum(crime_levels)
        if total_crime > 0:
            for i, parish_id in enumerate(parish_ids):
                if crime_levels[i] > 0:
                    proportion = crime_levels[i] / total_crime
                    additional_officers = int(remaining_officers * proportion)
                    recommendations[parish_id] += additional_officers
        else:
            # If no crime data, distribute evenly
            per_parish = remaining_officers // len(parish_ids)
            for parish_id in parish_ids:
                recommendations[parish_id] += per_parish
        
        # Ensure total matches exactly (handle rounding discrepancies)
        total_allocated = sum(recommendations.values())
        diff = self.total_officers - total_allocated
        
        # Distribute remaining officers to parishes with highest crime levels
        sorted_parishes = sorted(zip(parish_ids, crime_levels), key=lambda x: x[1], reverse=(diff > 0))
        for parish_id, _ in sorted_parishes:
            if diff == 0:
                break
            elif diff > 0:
                recommendations[parish_id] += 1
                diff -= 1
            else:  # diff < 0
                if recommendations[parish_id] > self.min_officers_per_parish:
                    recommendations[parish_id] -= 1
                    diff += 1
        
        return recommendations
    
    def _calculate_actual_allocation(self, parish_ids: List[int], crime_levels: List[int]) -> Dict[int, int]:
        """
        Calculate actual allocation using a different approach - taking into account
        population density and tourism factors.
        This creates a difference from the recommended allocation.
        """
        # Population density approximation (higher values for urban parishes)
        population_density = {
            1: 0.9,  # Kingston (urban)
            2: 0.85, # St. Andrew (urban) 
            3: 0.7,  # St. Catherine (mixed)
            4: 0.5,  # Clarendon (mixed)
            5: 0.4,  # Manchester (rural)
            6: 0.3,  # St. Elizabeth (rural)
            7: 0.4,  # Westmoreland (rural)
            8: 0.3,  # Hanover (rural)
            9: 0.6,  # St. James (urban/tourist)
            10: 0.4, # Trelawny (rural)
            11: 0.5, # St. Ann (tourist)
            12: 0.4, # St. Mary (rural)
            13: 0.3, # Portland (rural)
            14: 0.4  # St. Thomas (rural)
        }
        
        # Tourism level proxy (additional weight)
        tourism_factor = {
            1: 0.5,  # Kingston (moderate)
            2: 0.4,  # St. Andrew (moderate)
            3: 0.2,  # St. Catherine (low)
            4: 0.1,  # Clarendon (low)
            5: 0.2,  # Manchester (low)
            6: 0.2,  # St. Elizabeth (low)
            7: 0.5,  # Westmoreland (high - Negril)
            8: 0.3,  # Hanover (moderate)
            9: 0.8,  # St. James (very high - Montego Bay)
            10: 0.3, # Trelawny (moderate)
            11: 0.7, # St. Ann (high - Ocho Rios)
            12: 0.3, # St. Mary (moderate)
            13: 0.4, # Portland (moderate)
            14: 0.2  # St. Thomas (low)
        }
        
        # Calculate weighted scores for each parish using crime level, population density, and tourism
        weighted_scores = {}
        for i, parish_id in enumerate(parish_ids):
            crime_score = crime_levels[i] if crime_levels[i] > 0 else 1  # Default to 1 if no crime data
            density_factor = population_density.get(parish_id, 0.5)  # Default to 0.5 if not found
            tourism_weight = tourism_factor.get(parish_id, 0.3)  # Default to 0.3 if not found
            
            # Calculate weighted score - high density and tourism areas get more officers
            weighted_scores[parish_id] = crime_score * (1 + density_factor + tourism_weight)
        
        # Now distribute officers based on weighted scores
        allocations = {}
        total_score = sum(weighted_scores.values())
        
        # First ensure minimum officers per parish
        remaining_officers = self.total_officers - (self.min_officers_per_parish * len(parish_ids))
        for parish_id in parish_ids:
            allocations[parish_id] = self.min_officers_per_parish
        
        # Distribute remaining based on weighted scores
        if total_score > 0:
            for parish_id in parish_ids:
                proportion = weighted_scores[parish_id] / total_score
                additional_officers = int(remaining_officers * proportion)
                allocations[parish_id] += additional_officers
        
        # Ensure total matches exactly
        total_allocated = sum(allocations.values())
        diff = self.total_officers - total_allocated
        
        # Distribute remaining officers
        sorted_parishes = sorted(parish_ids, key=lambda pid: weighted_scores[pid], reverse=(diff > 0))
        for parish_id in sorted_parishes:
            if diff == 0:
                break
            elif diff > 0:
                allocations[parish_id] += 1
                diff -= 1
            else:  # diff < 0
                if allocations[parish_id] > self.min_officers_per_parish:
                    allocations[parish_id] -= 1
                    diff += 1
        
        return allocations
        
    def generate_recommendations(self, db: Session) -> Dict[int, int]:
        """
        Public method for accessing recommendations directly
        Uses the same algorithm as _calculate_recommended_allocation but gets params from DB
        """
        # Get parishes and crime levels from DB
        parishes = db.query(Parish).all()
        parish_ids = [parish.id for parish in parishes]
        crime_levels = [parish.current_crime_level or 0 for parish in parishes]
        
        # Calculate recommendations
        return self._calculate_recommended_allocation(parish_ids, crime_levels)