# app/ml/models/resource_allocator.py
import numpy as np
from typing import Dict, List
from sqlalchemy.orm import Session

from app.models.models import Parish, SystemSettings  # Added SystemSettings import
from app.core.config import settings

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
        
        # Extract crime levels
        parish_ids = [parish.id for parish in parishes]
        crime_levels = [parish.current_crime_level for parish in parishes]
        
        # Ensure we have crime level data
        if not crime_levels or all(level == 0 for level in crime_levels):
            # If no crime data, allocate officers evenly
            officers_per_parish = self.total_officers // len(parishes)
            return {parish_id: officers_per_parish for parish_id in parish_ids}
        
        # Allocate minimum officers to each parish
        allocation = {parish_id: self.min_officers_per_parish for parish_id in parish_ids}
        remaining_officers = self.total_officers - (self.min_officers_per_parish * len(parishes))
        
        # Weighted allocation for remaining officers
        total_crime = sum(crime_levels)
        if total_crime > 0:
            for i, parish_id in enumerate(parish_ids):
                # Calculate proportion of remaining officers based on crime level
                proportion = crime_levels[i] / total_crime
                additional_officers = int(remaining_officers * proportion)
                allocation[parish_id] += additional_officers
        
        # Make sure we've allocated exactly the right number of officers
        # Adjust if there's any discrepancy due to rounding
        total_allocated = sum(allocation.values())
        if total_allocated < self.total_officers:
            # Allocate remaining officers to highest crime parishes
            sorted_parishes = sorted(zip(parish_ids, crime_levels), key=lambda x: x[1], reverse=True)
            for parish_id, _ in sorted_parishes:
                if total_allocated >= self.total_officers:
                    break
                allocation[parish_id] += 1
                total_allocated += 1
        
        return allocation
        
    def generate_recommendations(self, db: Session) -> Dict[int, int]:
        """
        Generate recommended officer allocations that strictly sum to total_officers
        """
        # Get total officers from database
        total_officers_setting = db.query(SystemSettings).filter(SystemSettings.key == "total_officers").first()
        if total_officers_setting:
            self.total_officers = int(total_officers_setting.value)
        
        # Get all parishes with their crime levels
        parishes = db.query(Parish).all()
        parish_ids = [parish.id for parish in parishes]
        crime_levels = [parish.current_crime_level for parish in parishes]
        
        # Calculate raw recommendations (unconstrained)
        raw_recommendations = {}
        min_per_parish = self.min_officers_per_parish
        
        # Ensure we have valid crime data
        if not crime_levels or all(level == 0 for level in crime_levels):
            officers_per_parish = self.total_officers // len(parishes)
            return {parish_id: officers_per_parish for parish_id in parish_ids}
        
        # Calculate ideal allocation based on crime levels
        total_crime = sum(crime_levels)
        for i, parish_id in enumerate(parish_ids):
            if total_crime > 0:
                proportion = crime_levels[i] / total_crime
                # Still ensure minimum officers per parish
                raw_recommendations[parish_id] = max(
                    min_per_parish, 
                    int(self.total_officers * proportion)
                )
            else:
                raw_recommendations[parish_id] = min_per_parish
        
        # Now enforce the constraint that total must equal self.total_officers
        # First, make sure each parish gets at least the minimum
        constrained_recommendations = {pid: min_per_parish for pid in parish_ids}
        remaining = self.total_officers - (min_per_parish * len(parishes))
        
        # Calculate proportional distribution of remaining officers
        if remaining > 0 and total_crime > 0:
            for i, parish_id in enumerate(parish_ids):
                proportion = crime_levels[i] / total_crime
                constrained_recommendations[parish_id] += int(remaining * proportion)
        
        # Handle any rounding discrepancies
        total_allocated = sum(constrained_recommendations.values())
        diff = self.total_officers - total_allocated
        
        # Sort parishes by crime level for allocation adjustments
        sorted_parishes = sorted(zip(parish_ids, crime_levels), key=lambda x: x[1], reverse=(diff > 0))
        
        # Distribute any remaining officers or remove excess ones
        for parish_id, _ in sorted_parishes:
            if diff == 0:
                break
            elif diff > 0:
                constrained_recommendations[parish_id] += 1
                diff -= 1
            else:
                # Only reduce if it doesn't go below minimum
                if constrained_recommendations[parish_id] > min_per_parish:
                    constrained_recommendations[parish_id] -= 1
                    diff += 1
        
        return constrained_recommendations