import sys
import os
from sqlalchemy.orm import Session

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import models, database
from src.database import SessionLocal

def remove_dummy_data():
    db = SessionLocal()
    try:
        # Dummy codes from dummy_data.py: "1001", "1002", "2001"
        dummy_codes = ["1001", "1002", "2001"]
        
        # Check before
        existing = db.query(models.Student).filter(models.Student.code.in_(dummy_codes)).all()
        print(f"Found {len(existing)} dummy students to delete.")
        
        if not existing:
            print("No dummy students found.")
            return

        # Delete
        db.query(models.Student).filter(models.Student.code.in_(dummy_codes)).delete(synchronize_session=False)
        db.commit()
        print("Dummy students deleted successfully.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    remove_dummy_data()
