# app/ml/active_learning.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import threading
import time

from app.models.models import Intelligence, ModelVersion
from app.ml.models.crime_prediction import CrimePredictionModel
from app.ml.models.resource_allocator import ResourceAllocator

class ActiveLearningSystem:
    def __init__(self):
        self.last_training_time = datetime.now()
        self.min_new_records = 5  # Minimum new records before retraining
        self.training_interval = timedelta(seconds=60)  # Don't train more often than this
    
    def should_retrain(self, db: Session) -> bool:
        """Determine if model should be retrained based on new data"""
        # Check if enough time has passed since last training
        if datetime.now() - self.last_training_time < self.training_interval:
            return False
        
        # Count new intelligence records since last training
        new_records_count = db.query(Intelligence).filter(
            Intelligence.timestamp > self.last_training_time
        ).count()
        
        return new_records_count >= self.min_new_records
    
    def train_model(self, db: Session) -> float:
        """Train model with latest data"""
        # Get all intelligence data
        intelligence_records = db.query(Intelligence).all()
        
        # Convert to list of dictionaries
        data = [{
            "type": record.type,
            "parish_id": record.parish_id,
            "severity": record.severity,
            "confidence": record.confidence,
            "is_verified": record.is_verified,
            "feedback_score": record.feedback_score,
            "timestamp": record.timestamp
        } for record in intelligence_records]
        
        # Train the model
        prediction_model = CrimePredictionModel()
        accuracy = prediction_model.train(db, data)
        
        # Update last training time
        self.last_training_time = datetime.now()
        
        # Update resource allocation
        allocator = ResourceAllocator()
        allocator.allocate_resources(db)
        
        return accuracy
    
    def start_monitoring(self, db_func):
        """Start a background thread to monitor for retraining opportunities"""
        def monitor_loop():
            while True:
                try:
                    db = next(db_func())
                    if self.should_retrain(db):
                        print(f"Active learning system: Retraining model with new data...")
                        accuracy = self.train_model(db)
                        print(f"Model retrained with accuracy: {accuracy:.2f}")
                    db.close()
                except Exception as e:
                    print(f"Error in active learning monitoring: {str(e)}")
                
                # Sleep for a while before checking again
                time.sleep(60)  # Check every minute
        
        # Start monitoring in a background thread
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        
        return thread