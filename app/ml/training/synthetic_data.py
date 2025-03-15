# app/ml/training/synthetic_data.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict

from app.models.models import Parish, Intelligence
from app.schemas.intelligence import IntelligenceType

# app/ml/training/synthetic_data.py

def generate_synthetic_intelligence(db: Session, num_records: int = 1000) -> List[Dict]:
    """
    Generate synthetic intelligence data with realistic descriptions
    Returns a list of dictionaries with intelligence data
    """
    # Get all parishes
    parishes = db.query(Parish).all()
    parish_ids = [parish.id for parish in parishes]
    parish_names = {parish.id: parish.name for parish in parishes}
    
    # Define intelligence types
    intelligence_types = [intel_type.value for intel_type in IntelligenceType]
    
    # Define realistic description templates for each intelligence type
    descriptions = {
        "Crime": [
            "Armed robbery at {location} in {parish}. Suspects fled in a {color} vehicle.",
            "Burglary reported at a residence on {street} Street in {parish}. Items stolen include electronics and jewelry.",
            "Physical assault reported outside {location} in {parish}. Victim sustained minor injuries.",
            "Vandalism of public property at {location} in {parish}. Graffiti and property damage reported.",
            "Vehicle theft from {location} parking lot in {parish}. {color} {vehicle} with license plate ending in {number}."
        ],
        "Event": [
            "Large gathering planned at {location} in {parish} on {date}. Expecting {number} attendees.",
            "Political rally scheduled at {location} in {parish}. Potential for traffic disruption.",
            "Street festival in {parish} near {location} this weekend. Increased pedestrian activity expected.",
            "Protest demonstration planned outside {location} in {parish} regarding recent policy changes.",
            "Concert event at {location} in {parish} with history of security incidents in previous years."
        ],
        "Person": [
            "Suspect in recent {crime} cases spotted near {location} in {parish}. Individual matching description of wanted person.",
            "Known gang affiliate seen at {location} in {parish}. Individual has history of {crime} charges.",
            "Missing person last seen at {location} in {parish} wearing {color} clothing.",
            "Suspicious individual monitoring {location} in {parish} during late hours for past {number} days.",
            "Person with outstanding warrant observed frequenting {location} in {parish}."
        ],
        "Gang Activity": [
            "Increased activity of {gang} members in {parish} near {location}. Potential territory expansion.",
            "Suspected drug distribution operation by {gang} at {location} in {parish}.",
            "New gang tags/graffiti appeared at {location} in {parish} indicating {gang} presence.",
            "Confrontation between rival gangs reported at {location} in {parish}. No injuries reported.",
            "Recruitment efforts by {gang} targeting youth near schools in {parish}."
        ],
        "Police": [
            "Officer reports increased suspicious activity at {location} in {parish} during night shifts.",
            "Patrol unit identified potential drug house at {street} Street in {parish}.",
            "Community tip led to discovery of illegal goods at {location} in {parish}.",
            "Undercover operation in {parish} revealed connections between {location} business and criminal network.",
            "Traffic stop in {parish} resulted in seizure of illegal firearms near {location}."
        ],
        "Suspicious Activity": [
            "Unusual pattern of individuals entering/exiting {location} in {parish} at late hours.",
            "Multiple reports of drones flying over restricted areas in {parish} near {location}.",
            "Suspicious packages left unattended at {location} in {parish} on multiple occasions.",
            "Unusual financial transactions reported at {location} business in {parish}.",
            "Suspicious vehicle ({color} {vehicle}) frequently parked outside {location} in {parish} with occupants observing the area."
        ]
    }
    
    # Location templates
    locations = [
        "Main Street", "Commercial District", "Central Market", "Waterfront", "Town Square",
        "Shopping Mall", "Bus Terminal", "Railway Station", "Community Center", "Government Building",
        "Harbor Area", "Industrial Zone", "Beach Front", "Downtown", "University Campus",
        "Hospital Area", "Financial District", "Resort Area", "Tourist Zone", "Residential Complex"
    ]
    
    # Street names
    streets = [
        "Main", "First", "Second", "Third", "Park", "Oak", "Pine", "Maple", "Cedar", "Hill",
        "Ridge", "River", "Lake", "Ocean", "Mountain", "Valley", "Sunset", "Highland", "Meadow", "Spring"
    ]
    
    # Colors
    colors = ["red", "blue", "black", "white", "silver", "green", "yellow", "brown", "gray", "orange"]
    
    # Vehicle types
    vehicles = ["sedan", "SUV", "pickup truck", "van", "motorcycle", "coupe", "hatchback", "minivan", "truck", "bus"]
    
    # Gang names
    gangs = ["Southside Crew", "Eastside Posse", "Northtown Gangsters", "West Block Syndicate", "Downtown Mafia",
             "Harbor Boys", "Highland Thugs", "Riverside Killers", "Mountain Demons", "Valley Lords"]
    
    # Crime types for person descriptions
    crimes = ["theft", "assault", "drug", "robbery", "fraud", "violence", "weapon", "trafficking"]
    
    # Generate random data
    np.random.seed(42)  # For reproducibility
    
    # Generate timestamps spanning the last 12 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Generate synthetic intelligence records
    synthetic_data = []
    for i in range(num_records):
        # Parish distribution - weight urban areas more heavily
        parish_weights = [10, 10, 8, 6, 5, 5, 5, 4, 7, 4, 5, 4, 3, 3]  # Example weights
        parish_id = np.random.choice(parish_ids, p=np.array(parish_weights)/sum(parish_weights))
        parish_name = parish_names[parish_id]
        
        # Type distribution
        type_weights = [0.4, 0.2, 0.15, 0.15, 0.05, 0.05]  # More crimes than other types
        intel_type = np.random.choice(intelligence_types, p=type_weights)
        
        # Severity - bimodal distribution for more realism
        if np.random.random() < 0.7:  # 70% lower severity
            severity = np.random.randint(1, 6)
        else:  # 30% higher severity
            severity = np.random.randint(6, 11)
        
        # Confidence and verification
        confidence = np.random.uniform(0.3, 0.9)
        is_verified = np.random.random() < 0.6  # 60% verified
        
        # Feedback - tends to be positive (simplified)
        feedback_score = np.random.randint(-1, 3)
        
        # Generate a realistic description
        description_template = np.random.choice(descriptions[intel_type])
        
        # Fill in the template with random values
        description = description_template.format(
            parish=parish_name,
            location=np.random.choice(locations),
            street=np.random.choice(streets),
            color=np.random.choice(colors),
            vehicle=np.random.choice(vehicles),
            number=np.random.randint(100, 999),
            date=f"{np.random.randint(1, 29)}/{np.random.randint(1, 13)}/2024",
            gang=np.random.choice(gangs),
            crime=np.random.choice(crimes)
        )
        
        # Generate timestamp
        timestamp = start_date + timedelta(days=np.random.randint(0, 365))
        
        # Create record
        record = {
            "parish_id": parish_id,
            "type": intel_type,
            "description": description,
            "severity": severity,
            "confidence": confidence,
            "is_verified": is_verified,
            "feedback_score": feedback_score,
            "timestamp": timestamp
        }
        
        synthetic_data.append(record)
    
    return synthetic_data

def save_synthetic_data_to_db(db: Session, data: List[Dict]) -> None:
    """Save synthetic intelligence data to the database"""
    for record in data:
        # Convert NumPy data types to Python native types
        processed_record = {}
        for key, value in record.items():
            if hasattr(value, "item"):  # Check if it's a NumPy type with item() method
                processed_record[key] = value.item()  # Convert to Python native type
            else:
                processed_record[key] = value
        
        intelligence = Intelligence(**processed_record)
        db.add(intelligence)
    
    db.commit()