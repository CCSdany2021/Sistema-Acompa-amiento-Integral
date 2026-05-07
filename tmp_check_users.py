from src import database, models

db = database.SessionLocal()
try:
    users = db.query(models.User).all()
    print(f"Users count: {len(users)}")
    for u in users:
        print(
            f"  - {u.email}, name: {u.full_name}, role: {u.role}, assigned_section: {u.assigned_section}"
        )
finally:
    db.close()
