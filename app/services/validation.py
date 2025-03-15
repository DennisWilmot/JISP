# app/services/validation.py
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import Intelligence, Parish
from app.schemas.intelligence import IntelligenceType

def validate_intelligence(data: Dict[str, Any], db: Session) -> Tuple[bool, str]:
    """
    Validate intelligence data before saving to database
    Returns (is_valid, error_message)
    """
    # Check if parish exists
    parish_id = data.get("parish_id")
    if parish_id:
        parish = db.query(Parish).filter(Parish.id == parish_id).first()
        if not parish:
            return False, f"Parish with ID {parish_id} does not exist"
    else:
        return False, "Parish ID is required"
    
    # Validate intelligence type
    intel_type = data.get("type")
    try:
        # Ensure type is a valid enum value
        IntelligenceType(intel_type)
    except ValueError:
        valid_types = [t.value for t in IntelligenceType]
        return False, f"Invalid intelligence type. Must be one of: {', '.join(valid_types)}"
    
    # Validate severity
    severity = data.get("severity")
    if severity is not None:
        if not isinstance(severity, int) or severity < 1 or severity > 10:
            return False, "Severity must be an integer between 1 and 10"
    else:
        return False, "Severity is required"
    
    # Validate description
    description = data.get("description")
    if not description or len(description.strip()) < 10:
        return False, "Description must be at least 10 characters long"
    
    # Check for potential duplicates (similar intelligence within the last hour)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_similar = db.query(Intelligence).filter(
        Intelligence.parish_id == parish_id,
        Intelligence.type == intel_type,
        Intelligence.timestamp > one_hour_ago
    ).count()
    
    if recent_similar > 0:
        # Not an error, but a warning that can be returned with the validation
        return True, "Warning: Similar intelligence was reported in the last hour"
    
    return True, ""

def check_intelligence_trends(parish_id: int, db: Session) -> Dict[str, Any]:
    """
    Analyze intelligence trends for a specific parish
    Returns metrics about intelligence reporting patterns
    """
    # Get total intelligence count
    total_count = db.query(func.count(Intelligence.id)).filter(
        Intelligence.parish_id == parish_id
    ).scalar()
    
    # Get average severity
    avg_severity = db.query(func.avg(Intelligence.severity)).filter(
        Intelligence.parish_id == parish_id
    ).scalar() or 0.0
    
    # Get intelligence count by type
    intel_by_type = {}
    for intel_type in IntelligenceType:
        count = db.query(func.count(Intelligence.id)).filter(
            Intelligence.parish_id == parish_id,
            Intelligence.type == intel_type.value
        ).scalar()
        intel_by_type[intel_type.value] = count
    
    # Get verified vs unverified ratio
    verified_count = db.query(func.count(Intelligence.id)).filter(
        Intelligence.parish_id == parish_id,
        Intelligence.is_verified == True
    ).scalar()
    
    # Calculate recent activity (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_count = db.query(func.count(Intelligence.id)).filter(
        Intelligence.parish_id == parish_id,
        Intelligence.timestamp > week_ago
    ).scalar()
    
    return {
        "total_intelligence": total_count,
        "average_severity": float(avg_severity),
        "intelligence_by_type": intel_by_type,
        "verified_count": verified_count,
        "unverified_count": total_count - verified_count,
        "recent_activity": recent_count
    }