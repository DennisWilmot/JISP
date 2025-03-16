# Modify test_active_learning.py to check for feature engineering
from app.db.session import SessionLocal
from app.models.models import Intelligence, ModelVersion
from datetime import datetime
import time
import random
import json

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
        print("Waiting for active learning system to process new data (2 minutes)...")
        time.sleep(120)
        
        # Check if a new model version was created
        latest_model = db.query(ModelVersion).order_by(ModelVersion.id.desc()).first()
        latest_model_id = latest_model.id if latest_model else None
        
        if latest_model_id and latest_model_id > initial_model_id:
            print(f"SUCCESS: New model version created (ID: {latest_model_id})")
            print(f"New model accuracy: {latest_model.accuracy}")
            
            # Check for feature information
            if latest_model.features:
                try:
                    # Convert JSON string to Python object if needed
                    features = latest_model.features
                    if isinstance(features, str):
                        features = json.loads(features)
                    
                    print(f"Number of features used in model: {len(features)}")
                    
                    # Check for advanced features
                    advanced_features = [f for f in features if any(prefix in f for prefix in 
                                                                  ['time_', 'hour_', 'day_of_week_', 
                                                                   'parish_', 'type_', 'recency_', 
                                                                   'severity_confidence', 'weighted_severity'])]
                    
                    if advanced_features:
                        print("ADVANCED FEATURES DETECTED:")
                        for feature in advanced_features[:10]:  # Show first 10 to avoid long output
                            print(f"  - {feature}")
                        if len(advanced_features) > 10:
                            print(f"  ... and {len(advanced_features) - 10} more")
                        
                        print(f"Advanced features make up {len(advanced_features)/len(features)*100:.1f}% of all features")
                    else:
                        print("WARNING: No advanced features detected in the model")
                except Exception as e:
                    print(f"Error analyzing features: {e}")
        else:
            print("WARNING: No new model version detected. Active learning might not have triggered.")
            print("Check server logs for any errors or adjust the min_new_records threshold.")
    
    finally:
        db.close()

if __name__ == "__main__":
    add_test_intelligence()