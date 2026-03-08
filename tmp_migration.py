from src.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("Migrating: Adding is_accomplished to reports table...")
    try:
        conn.execute(text("ALTER TABLE reports ADD COLUMN is_accomplished BOOLEAN;"))
        conn.commit()
        print("Success.")
    except Exception as e:
        print(f"Error (maybe already exists?): {e}")
