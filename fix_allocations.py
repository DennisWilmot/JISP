# fix_allocations.py
from app.db.session import SessionLocal
from app.models.models import Parish, Prediction
from app.ml.models.resource_allocator import ResourceAllocator
from datetime import datetime

print("Starting manual resource allocation...")

# Create a database session
db = SessionLocal()

try:
    # Get all parishes
    parishes = db.query(Parish).all()
    parish_count = len(parishes)
    print(f"Found {parish_count} parishes")
    
    # Check if crime levels are set
    missing_crime_levels = [p for p in parishes if p.current_crime_level is None]
    if missing_crime_levels:
        print(f"Warning: {len(missing_crime_levels)} parishes have no crime level set")
        for p in missing_crime_levels:
            p.current_crime_level = 50  # Set default level
        db.commit()
        print("Set default crime levels")
    
    # Run resource allocation
    print("Generating resource allocations...")
    allocator = ResourceAllocator()
    
    # Get both the recommendations and allocations
    recommendations = allocator.generate_recommendations(db)
    allocations = allocator.allocate_resources(db)
    
    print("\nRecommendations vs. Allocations:")
    total_rec = 0
    total_alloc = 0
    
    # Update parish allocations and create prediction records
    for pid in sorted(allocations.keys()):
        parish = next((p for p in parishes if p.id == pid), None)
        if parish:
            rec = recommendations.get(pid, 0)
            alloc = allocations.get(pid, 0)
            
            # Update the parish
            parish.police_allocated = alloc
            
            # Create a prediction record
            prediction = Prediction(
                parish_id=pid,
                predicted_crime_level=parish.current_crime_level,
                recommended_officers=rec,
                timestamp=datetime.now()
            )
            db.add(prediction)
            
            print(f"Parish {pid} ({parish.name}): Crime = {parish.current_crime_level}, Recommended = {rec}, Allocated = {alloc}")
            
            total_rec += rec
            total_alloc += alloc
    
    # Commit all changes
    db.commit()
    
    print(f"\nTotals: Recommended = {total_rec}, Allocated = {total_alloc}")
    
    # Verify the changes
    allocations_in_db = sum(p.police_allocated or 0 for p in db.query(Parish).all())
    predictions_count = db.query(Prediction).count()
    
    print(f"Verification: Total officers in database = {allocations_in_db}")
    print(f"Predictions in database = {predictions_count}")

except Exception as e:
    print(f"Error: {str(e)}")
    db.rollback()
    raise

finally:
    db.close()

print("Process complete!")