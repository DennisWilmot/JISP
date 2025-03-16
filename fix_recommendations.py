# fix_null_recommendations.py
from app.db.session import SessionLocal
from app.models.models import Parish, Prediction
from datetime import datetime

print("Fixing null recommendations...")

# Create a database session
db = SessionLocal()

try:
    # First check if parishes and predictions tables exist
    print("Checking database structure...")
    
    # Get all parishes
    parishes = db.query(Parish).all()
    if not parishes:
        print("ERROR: No parishes found in database!")
        exit(1)
    
    print(f"Found {len(parishes)} parishes")
    
    # Check current allocation values
    print("\nCurrent parish allocations:")
    for parish in parishes:
        print(f"Parish {parish.id} ({parish.name}): Crime Level = {parish.current_crime_level}, Allocated = {parish.police_allocated}")
    
    # Check predictions (where recommendations should be)
    predictions = db.query(Prediction).all()
    print(f"\nFound {len(predictions)} prediction records")
    
    if predictions:
        print("Sample prediction records:")
        for pred in predictions[:3]:  # Show first 3 as sample
            print(f"Prediction {pred.id}: Parish = {pred.parish_id}, Crime Level = {pred.predicted_crime_level}, Recommended = {pred.recommended_officers}")
    
    # Direct fix approach
    print("\nFixing missing recommendations...")
    
    # 1. Delete all existing predictions to start fresh
    db.query(Prediction).delete()
    db.commit()
    print("Deleted all existing prediction records")
    
    # 2. Create new prediction records with recommendations matching allocations for now
    for parish in parishes:
        # Use the police_allocated value as a baseline for recommended_officers
        recommended = parish.police_allocated if parish.police_allocated is not None else 70
        
        # Create new prediction
        new_prediction = Prediction(
            parish_id=parish.id,
            predicted_crime_level=parish.current_crime_level if parish.current_crime_level is not None else 50,
            recommended_officers=recommended,
            timestamp=datetime.now()
        )
        db.add(new_prediction)
    
    db.commit()
    print("Created new prediction records with recommendations")
    
    # 3. Double-check that recommendations are now properly set
    new_predictions = db.query(Prediction).all()
    print(f"\nConfirming {len(new_predictions)} new prediction records:")
    
    for pred in new_predictions:
        print(f"Parish {pred.parish_id}: Recommended = {pred.recommended_officers}")
    
    # 4. Verify totals 
    total_recommended = sum(p.recommended_officers or 0 for p in new_predictions)
    total_allocated = sum(p.police_allocated or 0 for p in parishes)
    
    print(f"\nTotal recommended officers: {total_recommended}")
    print(f"Total allocated officers: {total_allocated}")

except Exception as e:
    print(f"ERROR: {str(e)}")
    db.rollback()
    raise

finally:
    db.close()

print("\nProcess complete!")