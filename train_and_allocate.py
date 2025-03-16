# train_and_allocate.py
from app.db.session import SessionLocal
from app.models.models import Intelligence, Parish
from app.ml.models.crime_prediction import CrimePredictionModel
from app.ml.models.resource_allocator import ResourceAllocator

print("Starting model training and resource allocation...")

# Create a database session
db = SessionLocal()

try:
    # Get all intelligence data
    print("Loading intelligence data...")
    intelligence_records = db.query(Intelligence).all()
    
    print(f"Found {len(intelligence_records)} intelligence records")
    
    # Convert to list of dictionaries for the model
    data = [{
        "type": record.type,
        "parish_id": record.parish_id,
        "severity": record.severity,
        "confidence": record.confidence,
        "is_verified": record.is_verified,
        "feedback_score": record.feedback_score,
        "timestamp": record.timestamp
    } for record in intelligence_records]
    
    # Train the crime prediction model
    print("Training crime prediction model...")
    prediction_model = CrimePredictionModel()
    accuracy = prediction_model.train(db, data)
    print(f"Model trained with accuracy: {accuracy:.2f}")
    
    # Update crime levels for all parishes
    print("Updating parish crime levels...")
    parishes = db.query(Parish).all()
    for parish in parishes:
        crime_level = prediction_model.predict_crime_level(db, parish.id)
        parish.current_crime_level = crime_level
    
    db.commit()
    print("Parish crime levels updated")
    
    # Allocate resources
    print("Running resource allocation...")
    allocator = ResourceAllocator()
    allocation = allocator.allocate_resources(db)
    
    # Update parishes with allocations
    for parish_id, officers in allocation.items():
        parish = db.query(Parish).filter(Parish.id == parish_id).first()
        if parish:
            parish.police_allocated = officers
    
    db.commit()
    print("Resource allocation complete")
    
    # Print summary
    print("\nFinal allocations:")
    parishes = db.query(Parish).all()
    for parish in parishes:
        print(f"Parish {parish.id} ({parish.name}): Crime Level = {parish.current_crime_level}, Officers = {parish.police_allocated}")

finally:
    db.close()

print("Process complete!")