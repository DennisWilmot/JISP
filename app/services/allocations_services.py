# app/services/allocation_service.py
from typing import Dict, List
from sqlalchemy.orm import Session
from app.models.models import Parish
from app.socket.manager import manager  # For broadcasting updates

async def execute_allocation_plan(db: Session, allocation_plan: Dict[int, int]) -> Dict[int, int]:
    """
    Execute an allocation plan by updating the parish allocations in the database
    
    Args:
        db: Database session
        allocation_plan: Dictionary mapping parish_id to officer count
        
    Returns:
        Dictionary of the actual allocations applied
    """
    # Validate the allocation plan
    parishes = db.query(Parish).all()
    parish_ids = [p.id for p in parishes]
    
    # Ensure all parish_ids in the plan exist
    invalid_ids = [pid for pid in allocation_plan.keys() if pid not in parish_ids]
    if invalid_ids:
        raise ValueError(f"Invalid parish IDs in allocation plan: {invalid_ids}")
    
    # Ensure the total allocation matches the total officers
    total_allocated = sum(allocation_plan.values())
    total_officers_setting = db.query(SystemSettings).filter(SystemSettings.key == "total_officers").first()
    total_officers = int(total_officers_setting.value) if total_officers_setting else 400
    
    if total_allocated != total_officers:
        raise ValueError(f"Total allocation ({total_allocated}) does not match total officers ({total_officers})")
    
    # Apply the allocation plan
    applied_changes = {}
    for parish in parishes:
        if parish.id in allocation_plan:
            new_allocation = allocation_plan[parish.id]
            old_allocation = parish.police_allocated
            
            # Record the change
            applied_changes[parish.id] = {
                "old": old_allocation,
                "new": new_allocation,
                "difference": new_allocation - old_allocation
            }
            
            # Update the database
            parish.police_allocated = new_allocation
    
    # Commit the changes
    db.commit()
    
    # Broadcast the updates via WebSockets
    await manager.send_resource_update(allocation_plan)
    
    # Create a log of this allocation
    # TODO: Add code to log the allocation change with timestamp and who made it
    
    return {p.id: p.police_allocated for p in db.query(Parish).all()}