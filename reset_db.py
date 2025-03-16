# reset_db.py
from app.db.session import Base, engine
from app.models.models import *  # Import all models
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.ml.training.synthetic_data import generate_synthetic_intelligence, save_synthetic_data_to_db

# Drop all tables
print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)

# Recreate tables
print("Creating database tables...")
Base.metadata.create_all(bind=engine)

# Initialize the database with parish data
print("Initializing parishes...")
db = SessionLocal()
init_db(db)

# Generate new synthetic data with the updated function
print("Generating new synthetic intelligence data...")
data = generate_synthetic_intelligence(db, num_records=200)

# Save to database
print("Saving new data to database...")
save_synthetic_data_to_db(db, data)

db.close()
print("Database reset complete with new realistic data!")