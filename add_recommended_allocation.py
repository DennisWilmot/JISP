# add_recommended_allocation.py
from app.db.session import engine, SessionLocal
from app.ml.models.resource_allocator import ResourceAllocator
from sqlalchemy import text

def add_column_and_update():
    # Create a connection to run the SQL
    connection = engine.connect()
    
    try:
        print("Adding 'recommended_allocation' column to parishes table...")
        # SQL query to add the column if it doesn't exist
        sql = text("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'parishes' AND column_name = 'recommended_allocation'
            ) THEN 
                ALTER TABLE parishes ADD COLUMN recommended_allocation INTEGER;
            END IF;
        END $$;
        """)
        
        # Execute the query
        connection.execute(sql)
        connection.commit()
        print("Column added successfully or already exists.")
        
        # Now run the resource allocator to populate the column
        print("Running resource allocator to populate values...")
        db = SessionLocal()
        try:
            allocator = ResourceAllocator()
            allocation = allocator.allocate_resources(db)
            print("Resource allocation completed successfully!")
            
            # Verify the data was populated
            from app.models.models import Parish
            parishes = db.query(Parish).all()
            print("\nVerification of updated data:")
            print("ID  | Name                    | Allocated | Recommended")
            print("-" * 60)
            for parish in parishes:
                print(f"{parish.id:<3} | {parish.name:<24} | {parish.police_allocated:<9} | {parish.recommended_allocation:<11}")
            
            print("\nSummary:")
            print(f"Total parishes updated: {len(parishes)}")
            print(f"Total officers allocated: {sum(p.police_allocated for p in parishes if p.police_allocated is not None)}")
            print(f"Total officers recommended: {sum(p.recommended_allocation for p in parishes if p.recommended_allocation is not None)}")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        connection.close()

if __name__ == "__main__":
    add_column_and_update()