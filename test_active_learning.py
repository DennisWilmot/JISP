# test_active_learning.py
from app.db.session import SessionLocal
from app.models.models import Intelligence, ModelVersion
from datetime import datetime
import time
import random

def add_test_intelligence(count=15):
    """Add test intelligence records to trigger retraining"""
    db = SessionLocal()
    
    try:
        # Get the latest model version to check later
        initial_model = db.query(ModelVersion).order_by(ModelVersion.id.desc()).first()
        initial_model_id = initial_model.id if initial_model else None
        
        print(f"Current model version ID: {initial_model_id}")
        
        # Add new intelligence records
        print(f"Adding {count} new intelligence records...")
        for i in range(count):
            new_intel = Intelligence(
                type="Crime" if random.random() < 0.6 else "Suspicious Activity",
                parish_id=random.randint(1, 14),
                description=f"Test intelligence for active learning #{i+1}",
                severity=random.randint(1, 10),
                confidence=random.random(),
                is_verified=random.random() > 0.3,
                feedback_score=random.randint(-1, 2),
                timestamp=datetime.now()
            )
            db.add(new_intel)
            db.commit()
            print(f"Added intelligence record {i+1}/{count}")
            # Add a small delay between records to make timestamps different
            time.sleep(0.1)
        
        # Wait for active learning system to detect and process new data
        # The system checks every minute, so we'll wait a bit more to be safe
        print("Waiting for active learning system to process new data (2 minutes)...")
        time.sleep(120)
        
        # Check if a new model version was created
        latest_model = db.query(ModelVersion).order_by(ModelVersion.id.desc()).first()
        latest_model_id = latest_model.id if latest_model else None
        
        if latest_model_id and latest_model_id > initial_model_id:
            print(f"SUCCESS: New model version created (ID: {latest_model_id})")
            print(f"New model accuracy: {latest_model.accuracy}")
        else:
            print("WARNING: No new model version detected. Active learning might not have triggered.")
            print("Check server logs for any errors or adjust the min_new_records threshold.")
    
    finally:
        db.close()

if __name__ == "__main__":
    add_test_intelligence()