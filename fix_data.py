# fix_app_data.py
from app.db.session import SessionLocal
from app.models.models import Parish, Prediction
import random
from datetime import datetime

print("Fixing parish data using application's existing connection...")

# Create a database session using the app's existing connection
db = SessionLocal()

try:
    # Get all parishes
    parishes = db.query(Parish).all()
    
    if not parishes:
        print("ERROR: No parishes found in database!")
        exit(1)
    
    print(f"Found {len(parishes)} parishes")
    
    # Define urban vs rural parishes for realistic allocations
    urban_parish_ids = [1, 2, 3, 9]  # Kingston, St. Andrew, St. Catherine, St. James
    
    # Total officers to allocate
    total_officers = 1000
    parish_count = len(parishes)
    base_officers = total_officers // parish_count
    
    # Track totals
    total_allocated = 0
    
    print("\nUpdating parishes with crime levels and allocations:")
    
    for parish in parishes:
        # Set a crime level based on whether it's urban or rural
        if parish.id in urban_parish_ids:
            # Urban areas have higher crime levels
            crime_level = random.randint(65, 90)
            # Allocate more officers to urban areas
            officers = int(base_officers * 1.5)
        else:
            # Rural areas have lower crime levels
            crime_level = random.randint(30, 60)
            officers = base_officers
        
        # Add a little randomness
        officers = max(30, min(150, officers + random.randint(-5, 5)))
        
        # Update the parish record
        parish.current_crime_level = crime_level
        parish.police_allocated = officers
        
        # Create a prediction record
        prediction = Prediction(
            parish_id=parish.id,
            predicted_crime_level=crime_level,
            recommended_officers=officers,
            timestamp=datetime.now()
        )
        db.add(prediction)
        
        total_allocated += officers
        
        print(f"Parish {parish.id} ({parish.name}): Crime Level = {crime_level}, Officers = {officers}")
    
    # Adjust to make sure we allocate exactly 1000 officers
    diff = total_officers - total_allocated
    if diff != 0:
        print(f"\nAdjusting allocation by {diff} officers to reach target of 1000")
        parishes[0].police_allocated += diff
        print(f"Updated {parishes[0].name} allocation to {parishes[0].police_allocated}")
    
    # Commit all changes
    print("\nCommitting changes to database...")
    db.commit()
    
    # Verify the changes
    print("\nVerifying changes:")
    parishes_after = db.query(Parish).all()
    
    for parish in parishes_after:
        print(f"Parish {parish.id} ({parish.name}): Crime Level = {parish.current_crime_level}, Officers = {parish.police_allocated}")
    
    total_after = sum(p.police_allocated or 0 for p in parishes_after)
    prediction_count = db.query(Prediction).count()
    
    print(f"\nTotal officers allocated: {total_after} (target: {total_officers})")
    print(f"Prediction records created: {prediction_count}")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    db.rollback()
    raise

finally:
    db.close()

print("\nProcess complete!")