# add_recommended_column.py
from sqlalchemy import text
from app.db.session import engine

# Add the column - using text() to make it executable
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE parishes ADD COLUMN IF NOT EXISTS recommended_allocation INTEGER'))
    conn.commit()
    print("Column added successfully!")