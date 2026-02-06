import sys
import os
# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import models, database
from src.database import SessionLocal, engine

# Init DB
models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

def create_data():
    if db.query(models.Student).first():
        print("Data already exists.")
        return

    # Create Students
    students = [
        {"full_name": "Juan Perez", "code": "1001", "course": "401", "section": models.SectionEnum.PREESCOLAR_PRIMARIA},
        {"full_name": "Maria Garcia", "code": "1002", "course": "401", "section": models.SectionEnum.PREESCOLAR_PRIMARIA},
        {"full_name": "Carlos Lopez", "code": "2001", "course": "1101", "section": models.SectionEnum.BACHILLERATO},
    ]
    
    for s in students:
        db_s = models.Student(**s)
        db.add(db_s)
    
    # Create Admin User (Mock)
    admin = models.User(
        email="admin@calasanz.edu.co",
        full_name="Admin Global",
        role=models.RoleEnum.ADMIN_GLOBAL
    )
    db.add(admin)
    
    db.commit()
    print("Dummy data created!")

if __name__ == "__main__":
    create_data()
