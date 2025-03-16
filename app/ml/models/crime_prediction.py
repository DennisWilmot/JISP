# app/ml/models/crime_prediction.py
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import pickle
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.models.models import Intelligence, ModelVersion, Parish
from app.ml.features.feature_engineering import FeatureEngineer


class CrimePredictionModel:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model_version = None
        self.feature_engineer = FeatureEngineer()
        self.features = []
        
        # Try to load the latest model from the database
        try:
            self._load_latest_model()
        except Exception as e:
            print(f"Warning: Could not load trained model: {str(e)}")
    
    def _load_latest_model(self):
        """Load the latest model from the database"""
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            # Get the latest model version
            latest_model = db.query(ModelVersion).filter(
                ModelVersion.model_type == "crime_prediction"
            ).order_by(ModelVersion.id.desc()).first()
            
            if latest_model and latest_model.binary_data:
                # Deserialize the model
                self.model = pickle.loads(latest_model.binary_data)
                self.model_version = latest_model.id
                self.features = latest_model.features
                print(f"Loaded model version {self.model_version}")
                return True
            return False
        finally:
            db.close()
    
    # Update the train method
    def train(self, db: Session, intelligence_data: List[Dict[str, Any]]) -> float:
        """
        Train the model using the provided intelligence data
        Returns the model accuracy
        """
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(intelligence_data)
        
        # Extract features using the enhanced feature engineering
        X, feature_names = self.feature_engineer.extract_features(df)
        self.features = feature_names
        
        y = df['severity'].values  # Use severity as the target for now
        
        # Train the model
        self.model.fit(X, y)
        
        # Calculate accuracy (simplified - in reality would use cross-validation)
        y_pred = self.model.predict(X)
        accuracy = np.mean(y_pred == y)
        
        # Update feature importance tracking
        if hasattr(self.model, 'feature_importances_'):
            self.feature_engineer.update_feature_importance(
                feature_names, 
                self.model.feature_importances_
            )
        
        # Save model to database
        self._save_model_to_db(db, accuracy)
        
        return accuracy
    
    # Update the predict_crime_level method with robust error handling
    def predict_crime_level(self, db: Session, parish_id: int) -> int:
        """
        Predict crime level for a specific parish
        Returns a crime level score from 0-100
        """
        try:
            # Get recent intelligence for the parish
            recent_intelligence = (
                db.query(Intelligence)
                .filter(Intelligence.parish_id == parish_id)
                .order_by(Intelligence.timestamp.desc())
                .limit(50)
                .all()
            )
            
            # If no intelligence, return default value
            if not recent_intelligence:
                return 20  # Default baseline
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'type': item.type,
                'parish_id': item.parish_id,
                'severity': item.severity,
                'confidence': item.confidence,
                'is_verified': item.is_verified,
                'feedback_score': item.feedback_score,
                'timestamp': item.timestamp,
            } for item in recent_intelligence])
            
            # Extract features using the enhanced feature engineering
            X, _ = self.feature_engineer.extract_features(df)
            
            # Make prediction with error handling
            try:
                severity_predictions = self.model.predict(X)
                
                # Convert to crime level (0-100 scale)
                avg_severity = np.mean(severity_predictions)
                crime_level = int(min(100, max(0, avg_severity * 10)))
            except Exception as e:
                # If model fails for any reason, use a simple heuristic
                print(f"Warning: Prediction model error: {str(e)}")
                avg_severity = df['severity'].mean() if 'severity' in df.columns else 5
                crime_level = int(min(100, max(0, avg_severity * 10)))
            
            # Apply additional adjustments based on parish characteristics
            parish = db.query(Parish).filter(Parish.id == parish_id).first()
            
            return crime_level
            
        except Exception as e:
            print(f"Error in predict_crime_level: {str(e)}")
            return 50  # Default fallback value
    
    def _save_model_to_db(self, db: Session, accuracy: float) -> None:
        """Save the trained model to the database"""
        # Serialize the model
        model_binary = pickle.dumps(self.model)
        
        # Create model version entry
        model_version = ModelVersion(
            model_type="crime_prediction",
            accuracy=accuracy,
            features=self.features,
            binary_data=model_binary
        )
        
        db.add(model_version)
        db.commit()
        db.refresh(model_version)
        
        self.model_version = model_version.id