# app/ml/training/synthetic_data.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict

from app.models.models import Parish, Intelligence
from app.schemas.intelligence import IntelligenceType

def generate_synthetic_intelligence(db: Session, num_records: int = 1000) -> List[Dict]:
    """
    Generate synthetic intelligence data with realistic distributions
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
    
    # Generate random data with more realistic distributions
    np.random.seed(42)  # For reproducibility
    
    # Generate timestamps spanning the last 12 months with more events in certain months
    # Create a weighted distribution favoring more recent months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    days_range = (end_date - start_date).days
    
    # Create time distribution weights - higher weight for summer months and recent weeks
    month_weights = np.ones(days_range)
    
    # Add seasonal patterns - more incidents during summer months
    for i in range(days_range):
        day = start_date + timedelta(days=i)
        # Summer months (June-August) have higher weights
        if 6 <= day.month <= 8:
            month_weights[i] *= 1.5
        # Winter months (December-February) have lower weights
        elif day.month in [12, 1, 2]:
            month_weights[i] *= 0.7
        # Weekend days have higher weights
        if day.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            month_weights[i] *= 1.3
        # More recent dates have slightly higher weights
        month_weights[i] *= 1 + (i / days_range) * 0.5
    
    # Normalize weights
    month_weights = month_weights / month_weights.sum()
    
    # Parish distribution - create realistic distribution based on population density
    # Kingston, St. Andrew, St. Catherine, and St. James (urban areas) should have more incidents
    # Rural parishes should have fewer
    urban_parish_ids = [1, 2, 3, 9]  # Kingston, St. Andrew, St. Catherine, St. James
    mixed_parish_ids = [4, 5, 7, 11]  # Clarendon, Manchester, Westmoreland, St. Ann
    rural_parish_ids = [6, 8, 10, 12, 13, 14]  # St. Elizabeth, Hanover, Trelawny, St. Mary, Portland, St. Thomas
    
    parish_weights = np.ones(len(parish_ids))
    for i, pid in enumerate(parish_ids):
        if pid in urban_parish_ids:
            parish_weights[i] = 4.0  # 4x more incidents in urban areas
        elif pid in mixed_parish_ids:
            parish_weights[i] = 2.0  # 2x more incidents in mixed areas
        else:
            parish_weights[i] = 1.0  # baseline for rural areas
    
    # Type distribution - create skewed distribution favoring certain types
    type_weights = {
        "Crime": 0.35,  # Most common
        "Suspicious Activity": 0.25,
        "Person": 0.15,
        "Gang Activity": 0.12,
        "Event": 0.08,
        "Police": 0.05   # Least common
    }
    
    # Generate synthetic intelligence records
    synthetic_data = []
    for i in range(num_records):
        # Select parish using weighted distribution
        parish_id = np.random.choice(parish_ids, p=parish_weights/parish_weights.sum())
        parish_name = parish_names[parish_id]
        
        # Select intelligence type using weighted distribution
        intel_type = np.random.choice(intelligence_types, p=[type_weights[t] for t in intelligence_types])
        
        # Generate timestamp with weighted distribution
        day_index = np.random.choice(range(days_range), p=month_weights)
        timestamp = start_date + timedelta(days=int(day_index))  # Convert numpy.int64 to regular Python int
        
        # Time of day patterns
        hour = None
        if intel_type == "Crime":
            # Crimes more likely at night
            hours_distribution = np.concatenate([
                np.ones(6) * 0.5,      # 00:00-06:00 (moderate)
                np.ones(12) * 0.3,     # 06:00-18:00 (low)
                np.ones(6) * 1.5       # 18:00-24:00 (high)
            ])
            hour = np.random.choice(24, p=hours_distribution/hours_distribution.sum())
        elif intel_type == "Suspicious Activity":
            # Suspicious activity more likely at night
            hours_distribution = np.concatenate([
                np.ones(6) * 1.5,      # 00:00-06:00 (high)
                np.ones(12) * 0.5,     # 06:00-18:00 (low)
                np.ones(6) * 1.2       # 18:00-24:00 (moderate)
            ])
            hour = np.random.choice(24, p=hours_distribution/hours_distribution.sum())
        else:
            # Other types more evenly distributed
            hour = np.random.randint(0, 24)
        
        # Add hour to timestamp
        timestamp = timestamp.replace(hour=int(hour), minute=int(np.random.randint(0, 60)))  # Convert numpy values to int
        
        # Severity distributions based on intelligence type and parish type
        # Urban areas tend to have more severe crimes
        # Gang Activity and Crime tend to be more severe
        base_severity = None
        if intel_type in ["Crime", "Gang Activity"]:
            # More severe
            if parish_id in urban_parish_ids:
                # Bimodal distribution - many lower severity and some high severity in urban areas
                if np.random.random() < 0.7:
                    base_severity = np.random.randint(2, 7)  # 70% lower severity
                else:
                    base_severity = np.random.randint(7, 11)  # 30% higher severity
            elif parish_id in mixed_parish_ids:
                # More even distribution in mixed areas
                base_severity = np.random.randint(3, 9)
            else:
                # Rural areas less severe
                base_severity = np.random.randint(1, 7)
        else:
            # Other types generally less severe
            if parish_id in urban_parish_ids:
                base_severity = np.random.randint(1, 8)
            elif parish_id in mixed_parish_ids:
                base_severity = np.random.randint(1, 6)
            else:
                base_severity = np.random.randint(1, 5)
        
        # Add randomness to severity scores
        severity_offset = np.random.choice([-1, 0, 1], p=[0.2, 0.6, 0.2])
        severity = max(1, min(10, int(base_severity) + int(severity_offset)))  # Convert to int
        
        # Confidence - generally higher for Police reports, lower for Suspicious Activity
        if intel_type == "Police":
            confidence = np.random.uniform(0.6, 0.95)
        elif intel_type == "Suspicious Activity":
            confidence = np.random.uniform(0.3, 0.7)
        else:
            confidence = np.random.uniform(0.4, 0.85)
        
        # Verification - Police reports more likely to be verified
        if intel_type == "Police":
            is_verified = np.random.random() < 0.8  # 80% verified
        elif intel_type in ["Crime", "Gang Activity"]:
            is_verified = np.random.random() < 0.65  # 65% verified
        else:
            is_verified = np.random.random() < 0.5  # 50% verified
        
        # Feedback - positive for verified reports, mixed for unverified
        if is_verified:
            feedback_weights = [0.05, 0.15, 0.8]  # [-1, 0, 1] - mostly positive
        else:
            feedback_weights = [0.3, 0.5, 0.2]  # [-1, 0, 1] - more mixed
        
        feedback_score = int(np.random.choice([-1, 0, 1], p=feedback_weights))  # Convert to int
        
        # Generate a realistic description
        description_template = np.random.choice(descriptions[intel_type])
        
        # Fill in the template with random values
        description = description_template.format(
            parish=parish_name,
            location=np.random.choice(locations),
            street=np.random.choice(streets),
            color=np.random.choice(colors),
            vehicle=np.random.choice(vehicles),
            number=int(np.random.randint(100, 999)),  # Convert to int
            date=f"{int(np.random.randint(1, 29))}/{int(np.random.randint(1, 13))}/2024",  # Convert to int
            gang=np.random.choice(gangs),
            crime=np.random.choice(crimes)
        )
        
        # Create record
        record = {
            "parish_id": int(parish_id),  # Convert to int
            "type": intel_type,
            "description": description,
            "severity": severity,
            "confidence": float(confidence),  # Convert to float
            "is_verified": bool(is_verified),  # Convert to bool
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