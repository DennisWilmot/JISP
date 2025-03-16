# test_field_names.py
from app.db.session import SessionLocal
from sqlalchemy import inspect

print("Checking database schema for field names...")

# Create a database session
db = SessionLocal()

try:
    # Get database inspector
    inspector = inspect(db.bind)
    
    # Check parishes table columns
    parish_columns = inspector.get_columns('parishes')
    print("\nParishes table columns:")
    for col in parish_columns:
        print(f"- {col['name']} ({col['type']})")
    
    # Check predictions table columns
    prediction_columns = inspector.get_columns('predictions')
    print("\nPredictions table columns:")
    for col in prediction_columns:
        print(f"- {col['name']} ({col['type']})")
    
    # Check if the specific field exists
    has_recommended_allocation = any(col['name'] == 'recommended_allocation' for col in parish_columns)
    has_recommended_officers = any(col['name'] == 'recommended_officers' for col in prediction_columns)
    
    print(f"\nParishes table has 'recommended_allocation' field: {has_recommended_allocation}")
    print(f"Predictions table has 'recommended_officers' field: {has_recommended_officers}")

except Exception as e:
    print(f"ERROR: {str(e)}")
    raise

finally:
    db.close()

print("\nSchema check complete!")