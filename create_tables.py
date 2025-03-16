# create_tables.py
from app.db.session import Base, engine
from app.models.models import Parish, Intelligence, Prediction, ModelVersion, SystemSettings, ResourceAllocation

# Print current tables before creation
from sqlalchemy import inspect
inspector = inspect(engine)
print("Tables BEFORE:", inspector.get_table_names())

# Force creation of all tables
Base.metadata.create_all(bind=engine)

# Print tables after creation to verify
inspector = inspect(engine)
print("Tables AFTER:", inspector.get_table_names())

# Verify ResourceAllocation table specifically
if "resource_allocations" in inspector.get_table_names():
    print("ResourceAllocation table created successfully!")
    print("Columns:", inspector.get_columns("resource_allocations"))
else:
    print("Failed to create ResourceAllocation table.")