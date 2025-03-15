from app.ml.models.crime_prediction import CrimePredictionModel
from app.ml.models.resource_allocator import ResourceAllocator
from app.ml.training.synthetic_data import generate_synthetic_intelligence, save_synthetic_data_to_db
from app.db.session import SessionLocal

def train_initial_model():
    """Generate synthetic data and train the initial model"""
    # Create a new DB session
    db = SessionLocal()
    
    try:
        # Generate synthetic intelligence data
        print("Generating synthetic intelligence data...")
        synthetic_data = generate_synthetic_intelligence(db, num_records=1000)
        
        # Save data to database
        print("Saving synthetic data to database...")
        save_synthetic_data_to_db(db, synthetic_data)
        
        # Add debugging code here
        print("Data sample:")
        if synthetic_data:
            sample = synthetic_data[0]
            print(f"Sample record keys: {sample.keys()}")
            print(f"Sample record values: {sample}")
        
        # Train the crime prediction model
        print("Training crime prediction model...")
        prediction_model = CrimePredictionModel()
        accuracy = prediction_model.train(db, synthetic_data)
        print(f"Model trained with accuracy: {accuracy:.2f}")
        
        # Allocate initial resources
        print("Performing initial resource allocation...")
        allocator = ResourceAllocator()
        allocation = allocator.allocate_resources(db)
        print(f"Resource allocation complete: {allocation}")
        
        print("Initial training and setup complete!")
        
    finally:
        db.close()

if __name__ == "__main__":
    train_initial_model()