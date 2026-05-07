from src import database, models

db = database.SessionLocal()
try:
    user = (
        db.query(models.User)
        .filter(models.User.email == "admin@calasanz.edu.co")
        .first()
    )
    if user:
        print(f"role type: {type(user.role)}, value: {user.role}")
        print(
            f"assigned_section type: {type(user.assigned_section)}, value: {user.assigned_section}"
        )
finally:
    db.close()
