# direct_sql_update.py
import psycopg2
import random
from datetime import datetime
import os
from dotenv import load_dotenv

print("Performing direct SQL updates to fix parish data...")

# Load environment variables if available
load_dotenv()

# Extract database connection details from the DATABASE_URL in environment if available
# Otherwise use default values
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/police_intelligence_db")

# Parse the DATABASE_URL to get connection parameters
# Format is typically: postgresql://username:password@host:port/dbname
try:
    # Simple parsing - might need to be more robust for complex URLs
    if "://" in database_url:
        # Extract credentials and host info
        credentials_host = database_url.split("://")[1].split("/")[0]
        db_name = database_url.split("/")[-1]
        
        if "@" in credentials_host:
            # We have username and possibly password
            auth, host_port = credentials_host.split("@")
            
            if ":" in auth:
                db_user, db_password = auth.split(":")
            else:
                db_user = auth
                db_password = ""
        else:
            # No authentication in URL
            host_port = credentials_host
            db_user = "postgres"
            db_password = ""
        
        if ":" in host_port:
            db_host, db_port = host_port.split(":")
        else:
            db_host = host_port
            db_port = "5432"
    else:
        # Default values if can't parse
        db_user = "postgres"
        db_password = ""  # Empty password
        db_host = "localhost"
        db_port = "5432"
        db_name = "police_intelligence_db"
except Exception as e:
    print(f"Error parsing DATABASE_URL: {e}")
    # Default values
    db_user = "postgres"
    db_password = ""  # Empty password
    db_host = "localhost"
    db_port = "5432"
    db_name = "police_intelligence_db"

print(f"Using database connection: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")

try:
    # Connect directly to PostgreSQL
    print(f"Connecting to database {db_name} on {db_host}...")
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    
    # Set autocommit to True to ensure changes are saved
    conn.autocommit = True
    
    # Create a cursor to execute commands
    cursor = conn.cursor()
    
    # Check if the parishes table exists
    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'parishes')")
    table_exists = cursor.fetchone()[0]
    
    if not table_exists:
        print("ERROR: 'parishes' table does not exist!")
        exit(1)
    
    # Get all parishes
    cursor.execute("SELECT id, name FROM parishes")
    parishes = cursor.fetchall()
    
    if not parishes:
        print("ERROR: No parishes found in database!")
        exit(1)
    
    print(f"Found {len(parishes)} parishes")
    
    # Total officers to allocate
    total_officers = 1000
    parish_count = len(parishes)
    base_officers = total_officers // parish_count
    
    # Define urban vs rural parishes for realistic allocations
    urban_parish_ids = [1, 2, 3, 9]  # Kingston, St. Andrew, St. Catherine, St. James
    
    # Track totals
    total_allocated = 0
    
    # Update parishes one by one
    print("\nUpdating parishes with crime levels and allocations:")
    
    for parish_id, parish_name in parishes:
        # Set a crime level based on whether it's urban or rural
        if parish_id in urban_parish_ids:
            # Urban areas have higher crime levels
            crime_level = random.randint(65, 90)
            # Allocate more officers to urban areas
            officers = int(base_officers * 1.5)
        else:
            # Rural areas have lower crime levels
            crime_level = random.randint(30, 60)
            officers = base_officers
        
        # Add a little randomness
        officers = max(30, min(150, officers + random.randint(-5, 5)))
        
        # Update the parish record using SQL
        cursor.execute(
            """
            UPDATE parishes 
            SET current_crime_level = %s, police_allocated = %s
            WHERE id = %s
            """,
            (crime_level, officers, parish_id)
        )
        
        total_allocated += officers
        
        print(f"Parish {parish_id} ({parish_name}): Crime Level = {crime_level}, Officers = {officers}")
    
    # Adjust to make sure we allocate exactly 1000 officers
    diff = total_officers - total_allocated
    if diff != 0:
        first_parish_id = parishes[0][0]
        cursor.execute("SELECT police_allocated FROM parishes WHERE id = %s", (first_parish_id,))
        current_allocation = cursor.fetchone()[0] or 0  # Handle NULL value
        new_allocation = current_allocation + diff
        
        print(f"\nAdjusting allocation by {diff} officers to reach total of {total_officers}")
        cursor.execute(
            "UPDATE parishes SET police_allocated = %s WHERE id = %s",
            (new_allocation, first_parish_id)
        )
        print(f"Updated Parish {first_parish_id} allocation to {new_allocation}")
    
    # Check if predictions table exists and create it if needed
    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'predictions')")
    predictions_exist = cursor.fetchone()[0]
    
    if not predictions_exist:
        print("\nCreating predictions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                parish_id INTEGER REFERENCES parishes(id),
                predicted_crime_level INTEGER,
                recommended_officers INTEGER,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
    
    # Now add some prediction records
    print("\nCreating prediction records...")
    
    cursor.execute("DELETE FROM predictions")  # Clear existing predictions
    
    for parish_id, parish_name in parishes:
        # Get the current crime level and allocation
        cursor.execute(
            "SELECT current_crime_level, police_allocated FROM parishes WHERE id = %s",
            (parish_id,)
        )
        crime_level, officers = cursor.fetchone()
        
        # Insert a prediction record
        cursor.execute(
            """
            INSERT INTO predictions 
            (parish_id, predicted_crime_level, recommended_officers, timestamp) 
            VALUES (%s, %s, %s, %s)
            """,
            (parish_id, crime_level, officers, datetime.now())
        )
        
    # Verify the changes
    print("\nVerifying changes:")
    
    cursor.execute("SELECT id, name, current_crime_level, police_allocated FROM parishes ORDER BY id")
    updated_parishes = cursor.fetchall()
    
    for parish_id, name, crime_level, officers in updated_parishes:
        print(f"Parish {parish_id} ({name}): Crime Level = {crime_level}, Officers = {officers}")
    
    cursor.execute("SELECT SUM(police_allocated) FROM parishes")
    total_officers_db = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM predictions")
    prediction_count = cursor.fetchone()[0]
    
    print(f"\nTotal officers allocated: {total_officers_db} (target: {total_officers})")
    print(f"Prediction records created: {prediction_count}")

except Exception as e:
    print(f"ERROR: {str(e)}")
    if 'conn' in locals():
        conn.rollback()
    raise

finally:
    # Close the connection
    if 'conn' in locals():
        conn.close()

print("\nProcess complete!")