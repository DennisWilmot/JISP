# app/services/allocation_service.py
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.models import Parish
from app.ml.models.resource_allocator import ResourceAllocator

def execute_allocation_plan(db: Session, allocation: Dict[int, int]) -> Dict[str, Any]:
    """
    Execute a resource allocation plan by updating the parishes table
    Returns details of the allocation execution
    """
    changes = []
    total_officers = 0
    
    # Update parish allocations in the database
    for parish_id, officers in allocation.items():
        parish = db.query(Parish).filter(Parish.id == parish_id).first()
        if parish:
            previous = parish.police_allocated
            parish.police_allocated = officers
            
            # Track changes
            if previous != officers:
                changes.append({
                    "parish_id": parish_id,
                    "parish_name": parish.name, 
                    "previous": previous,
                    "new": officers,
                    "difference": officers - previous
                })
            
            total_officers += officers
    
    db.commit()
    
    # Return execution summary
    return {
        "total_officers_allocated": total_officers,
        "parishes_updated": len(changes),
        "allocation_changes": changes
    }

def get_allocation_plan(db: Session) -> Dict[int, int]:
    """
    Get a resource allocation plan using the ResourceAllocator
    Returns a mapping of parish_id to officer count
    """
    allocator = ResourceAllocator()
    return allocator.allocate_resources(db)