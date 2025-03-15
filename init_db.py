# init_db.py
from app.db.session import engine, SessionLocal
from app.models.models import Base
from app.db.init_db import init_db

print("Creating database tables...")
# Create all tables
Base.metadata.create_all(bind=engine)

print("Initializing data...")
# Initialize with parish data
db = SessionLocal()
init_db(db)
db.close()

print("Database initialized successfully!")