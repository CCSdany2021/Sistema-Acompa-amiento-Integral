from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent dir to path to find src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import SQLALCHEMY_DATABASE_URL

def fix_enums():
    print(f"Connecting to {SQLALCHEMY_DATABASE_URL}...")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as connection:
        # Check current values
        print("Checking current status values...")
        try:
            result = connection.execute(text("SELECT id, status FROM reports"))
            for row in result:
                print(f"Report {row.id}: {row.status}")
        except Exception as e:
            print(f"Error reading reports: {e}")

        # Normalize ALL statuses to Uppercase
        print("Normalizing statuses to UPPERCASE...")
        connection.execute(text("UPDATE reports SET status = 'PROGRAMADO' WHERE status IN ('OPEN', 'Abierto', 'Programado')"))
        connection.execute(text("UPDATE reports SET status = 'SEGUIMIENTO' WHERE status IN ('Seguimiento')"))
        connection.execute(text("UPDATE reports SET status = 'ATENDIDO' WHERE status IN ('CLOSED', 'Cerrado', 'Atendido')"))
        
        connection.commit()
        print("Update complete.")

if __name__ == "__main__":
    fix_enums()
