# app/ml/models/resource_allocator.py
import numpy as np
from typing import Dict, List
from sqlalchemy.orm import Session

from app.models.models import Parish
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