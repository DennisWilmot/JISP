# test_allocation_fix.py
from app.db.session import SessionLocal
from app.models.models import Parish, Prediction
from app.ml.models.resource_allocator import ResourceAllocator

print("Testing updated resource allocation with recommendation saving...")

# Create a database session
db = SessionLocal()

try:
    # Get all parishes to confirm they exist
    parishes = db.query(Parish).all()
    if not parishes:
        print("ERROR: No parishes found in database!")
        exit(1)
    
    print(f"Found {len(parishes)} parishes")
    
    # Display current state before allocation
    print("\nCurrent parish allocations before update:")
    for parish in parishes:
        print(f"Parish {parish.id} ({parish.name}): Crime Level = {parish.current_crime_level}, Allocated = {parish.police_allocated}")
    
    # Check existing predictions
    old_predictions = db.query(Prediction).all()
    print(f"\nFound {len(old_predictions)} existing prediction records")
    
    # Run the updated resource allocator
    print("\nRunning resource allocation with updated code...")
    allocator = ResourceAllocator()
    allocations = allocator.allocate_resources(db)
    
    print("\nAllocations returned from method:")
    for parish_id, officers in allocations.items():
        print(f"Parish {parish_id}: Allocated = {officers}")
    
    # Verify parishes were updated
    updated_parishes = db.query(Parish).all()
    print("\nUpdated parish allocations:")
    for parish in updated_parishes:
        print(f"Parish {parish.id} ({parish.name}): Crime Level = {parish.current_crime_level}, Allocated = {parish.police_allocated}")
    
    # Verify new predictions were created
    new_predictions = db.query(Prediction).all()
    print(f"\nFound {len(new_predictions)} prediction records after update")
    
    if new_predictions:
        print("\nSample of prediction records:")
        for pred in new_predictions[:5]:  # Show first 5 as sample
            print(f"Prediction {pred.id}: Parish = {pred.parish_id}, Crime Level = {pred.predicted_crime_level}, Recommended = {pred.recommended_officers}")
    
    # Verify totals
    total_allocated = sum(parish.police_allocated or 0 for parish in updated_parishes)
    total_recommended = sum(pred.recommended_officers or 0 for pred in new_predictions if pred.recommended_officers is not None)
    
    print(f"\nTotal allocated officers: {total_allocated}")
    print(f"Total recommended officers: {total_recommended}")

except Exception as e:
    print(f"ERROR: {str(e)}")
    db.rollback()
    raise

finally:
    db.close()

print("\nTest complete!")