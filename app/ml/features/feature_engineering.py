# app/ml/features/feature_engineering.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class FeatureEngineer:
    def __init__(self):
        # Feature importance tracking for active learning
        self.feature_importance = {}
    
    def extract_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """
        Enhanced feature extraction with more sophisticated transformations
        Returns the feature matrix and feature names
        """
        # Make a copy to avoid modifying the original
        df_processed = df.copy()
        
        # Add temporal features
        if 'timestamp' in df_processed.columns:
            df_processed = self._add_temporal_features(df_processed)
        
        # Add spatial features if coordinates are available
        if 'parish_id' in df_processed.columns:
            df_processed = self._add_spatial_features(df_processed)
        
        # Add intelligence type features
        if 'type' in df_processed.columns:
            df_processed = self._add_type_features(df_processed)
        
        # Add interaction features
        df_processed = self._add_interaction_features(df_processed)
        
        # Add recency features
        if 'timestamp' in df_processed.columns:
            df_processed = self._add_recency_features(df_processed)
        
        # Feature normalization
        df_processed = self._normalize_features(df_processed)
        
        # Drop non-numeric columns
        drop_columns = []
        for col in df_processed.columns:
            if df_processed[col].dtype == 'object' or col == 'timestamp':
                drop_columns.append(col)
        
        # Also drop the description column if it exists
        if 'description' in df_processed.columns:
            drop_columns.append('description')
            
        df_final = df_processed.drop(columns=drop_columns, errors='ignore')
        
        # Convert boolean columns to int
        for col in df_final.columns:
            if df_final[col].dtype == bool:
                df_final[col] = df_final[col].astype(int)
        
        # Get feature names for later interpretation
        feature_names = list(df_final.columns)
        
        return df_final.values, feature_names
    
    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add sophisticated temporal features"""
        # Basic time components
        df['hour'] = df['timestamp'].dt.hour
        df['day'] = df['timestamp'].dt.day
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        
        # Time of day features (using cyclic encoding to preserve continuity)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour']/24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour']/24)
        
        # Day of week features (using cyclic encoding)
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week']/7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week']/7)
        
        # Is weekend
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Time period categories
        df['time_period'] = pd.cut(
            df['hour'], 
            bins=[0, 6, 12, 18, 24], 
            labels=['night', 'morning', 'afternoon', 'evening'],
            include_lowest=True
        )
        
        # One-hot encode time periods
        time_period_dummies = pd.get_dummies(df['time_period'], prefix='time')
        df = pd.concat([df, time_period_dummies], axis=1)
        
        return df
    
    def _add_spatial_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add spatial features based on parish information"""
        # One-hot encode parishes
        parish_dummies = pd.get_dummies(df['parish_id'], prefix='parish')
        df = pd.concat([df, parish_dummies], axis=1)
        
        # Add parish-based features
        # In a real system, you would incorporate known characteristics about parishes
        # such as population density, urbanization level, etc.
        # For this example, we'll create simple mappings
        
        # Population density proxy (higher values for urban parishes)
        parish_density = {
            1: 0.9,  # Kingston (urban)
            2: 0.85, # St. Andrew (urban)
            3: 0.7,  # St. Catherine (mixed)
            4: 0.5,  # Clarendon (mixed)
            5: 0.4,  # Manchester (rural)
            6: 0.3,  # St. Elizabeth (rural)
            7: 0.4,  # Westmoreland (rural)
            8: 0.3,  # Hanover (rural)
            9: 0.6,  # St. James (urban/tourist)
            10: 0.4, # Trelawny (rural)
            11: 0.5, # St. Ann (tourist)
            12: 0.4, # St. Mary (rural)
            13: 0.3, # Portland (rural)
            14: 0.4  # St. Thomas (rural)
        }
        
        # Tourism level proxy
        parish_tourism = {
            1: 0.5,  # Kingston (moderate)
            2: 0.4,  # St. Andrew (moderate)
            3: 0.2,  # St. Catherine (low)
            4: 0.1,  # Clarendon (low)
            5: 0.2,  # Manchester (low)
            6: 0.2,  # St. Elizabeth (low)
            7: 0.5,  # Westmoreland (high - Negril)
            8: 0.3,  # Hanover (moderate)
            9: 0.8,  # St. James (very high - Montego Bay)
            10: 0.3, # Trelawny (moderate)
            11: 0.7, # St. Ann (high - Ocho Rios)
            12: 0.3, # St. Mary (moderate)
            13: 0.4, # Portland (moderate)
            14: 0.2  # St. Thomas (low)
        }
        
        # Apply these features
        df['population_density'] = df['parish_id'].map(parish_density)
        df['tourism_level'] = df['parish_id'].map(parish_tourism)
        
        return df
    
    def _add_type_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add features based on intelligence type"""
        # One-hot encode intelligence types
        type_dummies = pd.get_dummies(df['type'], prefix='type')
        df = pd.concat([df, type_dummies], axis=1)
        
        # Add severity weighting by type
        # Some intelligence types might be inherently more concerning
        type_severity_weight = {
            'Crime': 1.2,
            'Gang Activity': 1.5,
            'Person': 0.9,
            'Event': 0.8,
            'Police': 0.7,
            'Suspicious Activity': 1.0
        }
        
        df['type_severity_weight'] = df['type'].map(type_severity_weight)
        df['weighted_severity'] = df['severity'] * df['type_severity_weight']
        
        return df
    
    def _add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add interaction features between different variables"""
        # Only create these if the required columns exist
        if all(col in df.columns for col in ['severity', 'confidence']):
            # Confidence-weighted severity
            df['severity_confidence'] = df['severity'] * df['confidence']
        
        if all(col in df.columns for col in ['is_verified', 'severity']):
            # Verification impact
            df['verified_severity'] = df['severity'] * df['is_verified'].astype(int)
        
        if all(col in df.columns for col in ['is_weekend', 'severity']):
            # Weekend severity interaction
            df['weekend_severity'] = df['is_weekend'] * df['severity']
        
        if all(col in df.columns for col in ['population_density', 'severity']):
            # Population density and severity interaction
            df['density_severity'] = df['population_density'] * df['severity']
        
        return df
    
    def _add_recency_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add recency-based features"""
        # Calculate days since the most recent intelligence
        most_recent = df['timestamp'].max()
        df['days_since'] = (most_recent - df['timestamp']).dt.total_seconds() / (24 * 3600)
        
        # Apply recency decay factor
        df['recency_weight'] = np.exp(-0.1 * df['days_since'])
        
        # Apply recency weighting to severity
        df['recency_severity'] = df['severity'] * df['recency_weight']
        
        return df
    
    def _normalize_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize numerical features for better model performance"""
        # Select numeric columns only (excluding the target if present)
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        if 'severity' in numeric_cols:
            numeric_cols.remove('severity')  # Don't normalize the target variable
        
        # Standard scaling (z-score normalization)
        for col in numeric_cols:
            if df[col].std() > 0:  # Avoid division by zero
                df[f"{col}_norm"] = (df[col] - df[col].mean()) / df[col].std()
        
        return df
    
    def update_feature_importance(self, feature_names: List[str], importance_values: List[float]) -> None:
        """Update feature importance tracking for active learning"""
        self.feature_importance = dict(zip(feature_names, importance_values))