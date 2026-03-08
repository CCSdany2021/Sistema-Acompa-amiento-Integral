from src.database import SessionLocal
try:
    db = SessionLocal()
    db.execute("SELECT 1")
    print("Success.")
    db.close()
except Exception as e:
    print(f"Locked? Error: {e}")
