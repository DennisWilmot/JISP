# app/db/init_db.py
from sqlalchemy.orm import Session

from app.db.session import Base, engine
from app.models.models import Parish, SystemSettings  # Added SystemSettings import

def init_db(db: Session) -> None:
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Check if parishes already exist
    if db.query(Parish).count() == 0:
        # Add the 14 parishes of Jamaica with approximate coordinates
        parishes = [
            {"name": "Kingston", "coordinates": {"lat": 18.0179, "lng": -76.8099}, "current_crime_level": 0, "police_allocated": 0},
            {"name": "St. Andrew", "coordinates": {"lat": 18.0429, "lng": -76.8015}, "current_crime_level": 0, "police_allocated": 0},
            {"name": "St. Catherine", "coordinates": {"lat": 18.0420, "lng": -77.0260}, "current_crime_level": 0, "police_allocated": 0},
            {"name": "Clarendon", "coordinates": {"lat": 17.9592, "lng": -77.2350}, "current_crime_level": 0, "police_allocated": 0},
            {"name": "Manchester", "coordinates": {"lat": 18.0442, "lng": -77.5047}, "current_crime_level": 0, "police_allocated": 0},
            {"name": "St. Elizabeth", "coordinates": {"lat": 18.0724, "lng": -77.6757}, "current_crime_level": 0, "police_allocated": 0},
            {"name": "Westmoreland", "coordinates": {"lat": 18.2194, "lng": -78.1290}, "current_crime_level": 0, "police_allocated": 0},
            {"name": "Hanover", "coordinates": {"lat": 18.4005, "lng": -78.1317}, "current_crime_level": 0, "police_allocated": 0},
            {"name": "St. James", "coordinates": {"lat": 18.4762, "lng": -77.9145}, "current_crime_level": 0, "police_allocated": 0},
            {"name": "Trelawny", "coordinates": {"lat": 18.3521, "lng": -77.6570}, "current_crime_level": 0, "police_allocated": 0},
            {"name": "St. Ann", "coordinates": {"lat": 18.4286, "lng": -77.1988}, "current_crime_level": 0, "police_allocated": 0},
            {"name": "St. Mary", "coordinates": {"lat": 18.3638, "lng": -76.9113}, "current_crime_level": 0, "police_allocated": 0},
            {"name": "Portland", "coordinates": {"lat": 18.1818, "lng": -76.4543}, "current_crime_level": 0, "police_allocated": 0},
            {"name": "St. Thomas", "coordinates": {"lat": 17.9877, "lng": -76.4772}, "current_crime_level": 0, "police_allocated": 0},
        ]
        
        for parish_data in parishes:
            parish = Parish(**parish_data)
            db.add(parish)
        
        db.commit()
    
    # Initialize system settings if they don't exist
    if db.query(SystemSettings).filter(SystemSettings.key == "total_officers").count() == 0:
        total_officers = SystemSettings(
            key="total_officers",
            value="1000",
            description="Total number of police officers available for allocation across parishes"
        )
        db.add(total_officers)
        db.commit()