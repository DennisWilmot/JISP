# query_db.py
from app.db.session import SessionLocal
from app.models.models import Intelligence, Parish

# Create a database session
db = SessionLocal()

try:
    # Check for parishes
    parishes = db.query(Parish).all()
    print(f"Number of parishes: {len(parishes)}")
    if parishes:
        for parish in parishes:
            print(f"Parish ID: {parish.id}, Name: {parish.name}")
    
    # Check for intelligence data
    intel_count = db.query(Intelligence).count()
    print(f"Number of intelligence records: {intel_count}")
    
    if intel_count > 0:
        # Get a sample of records
        sample = db.query(Intelligence).limit(5).all()
        print("\nSample of intelligence records:")
        for i, record in enumerate(sample):
            print(f"Record {i+1}: Type: {record.type}, Parish: {record.parish_id}, Severity: {record.severity}")
    else:
        print("No intelligence records found!")
    
finally:
    db.close()